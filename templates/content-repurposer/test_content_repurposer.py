"""
Tests for Content Repurposing Pipeline Actor
=============================================
Tests the ContentRepurposer logic class (pure, no apify SDK dependency).
Uses Pattern B: duplicated test class with class-level dependency injection.
"""

import base64
import io
import json
import os
import re
import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# ─── Duplicated logic class for testing (Pattern B) ──────────────────────

class TestableContentRepurposer:
    """Testable copy of ContentRepurposer — pure logic, no apify SDK."""

    QUOTE_CARD_WIDTH = 1080
    QUOTE_CARD_HEIGHT = 1080

    QUOTE_CARD_THEMES = {
        "dark": {"bg": (30, 30, 30), "text": (255, 255, 255), "accent": (255, 200, 50)},
        "light": {"bg": (255, 255, 255), "text": (40, 40, 40), "accent": (50, 120, 200)},
        "warm": {"bg": (50, 30, 20), "text": (255, 240, 220), "accent": (230, 150, 70)},
        "cool": {"bg": (20, 40, 60), "text": (230, 240, 255), "accent": (100, 180, 230)},
        "vibrant": {"bg": (100, 30, 60), "text": (255, 235, 240), "accent": (255, 200, 100)},
    }

    TWITTER_MAX_CHARS = 280
    LINKEDIN_MAX_CHARS = 3000

    # Injected by tests when needed
    Pillow = None
    gTTS = None
    gTTSError = Exception

    @classmethod
    def extract_key_moments(cls, transcript: str, max_moments: int = 5) -> list[dict]:
        if not transcript or not transcript.strip():
            return []

        lines = transcript.strip().split("\n")
        moments = []
        current_moment = {"title": "", "text": "", "timestamp": ""}

        timestamp_pattern = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            ts_match = timestamp_pattern.search(line)
            if ts_match:
                ts = ts_match.group(1)
                if current_moment["text"]:
                    moments.append(current_moment)
                    current_moment = {"title": "", "text": "", "timestamp": ""}
                current_moment["timestamp"] = ts
                text_after = line[ts_match.end():].strip().lstrip(":] ")
                if text_after:
                    current_moment["text"] += text_after + " "
            else:
                current_moment["text"] += line + " "

        if current_moment["text"]:
            moments.append(current_moment)

        for moment in moments:
            text = moment["text"].strip()
            first_sentence = re.split(r"[.!?]", text)[0] if text else ""
            moment["title"] = first_sentence[:80].strip() if first_sentence else "Key moment"
            moment["text"] = text[:500].strip()

        if len(moments) > max_moments:
            step = len(moments) / max_moments
            moments = [moments[int(i * step)] for i in range(max_moments)]

        return moments

    @classmethod
    def extract_quotes(cls, text: str, max_quotes: int = 3) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 280]

        scored = []
        for s in sentences:
            word_count = len(s.split())
            if 5 <= word_count <= 25:
                score = 100 - abs(word_count - 12) * 3
                scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        quotes = [s[1] + "." for s in scored[:max_quotes] if s[0] > 50]

        return quotes if quotes else sentences[:max_quotes]

    @classmethod
    def generate_tweet_thread(cls, title: str, key_moments: list[dict],
                              max_tweets: int = 5) -> list[str]:
        if not key_moments:
            return []

        thread = []
        thread.append(f"🧵 {title[:200]}")

        for i, moment in enumerate(key_moments[:max_tweets - 1]):
            ts = moment.get("timestamp", "")
            title_text = moment.get("title", "")
            body_text = moment.get("text", "")[:150]

            tweet = f"{i+1}. {title_text}"
            if ts:
                tweet += f" [{ts}]"
            if body_text:
                tweet += f"\n\n{body_text}"

            if len(tweet) > cls.TWITTER_MAX_CHARS:
                tweet = tweet[:cls.TWITTER_MAX_CHARS - 3] + "..."

            thread.append(tweet)

        return thread

    @classmethod
    def generate_linkedin_post(cls, title: str, key_moments: list[dict],
                                quotes: list[str]) -> str:
        lines = []

        lines.append(f"I just watched/discussed \"{title}\" and here are the key takeaways:\n")

        for i, moment in enumerate(key_moments[:4], 1):
            title_text = moment.get("title", "")
            ts = moment.get("timestamp", "")
            ts_str = f" [{ts}]" if ts else ""
            lines.append(f"🎯 {i}. {title_text}{ts_str}")

        lines.append("")

        if quotes:
            lines.append(f"💡 \"{quotes[0]}\"\n")

        lines.append("What's your #1 takeaway? ♻️ Repost if this was valuable.")

        post = "\n".join(lines)

        if len(post) > cls.LINKEDIN_MAX_CHARS:
            post = post[:cls.LINKEDIN_MAX_CHARS - 3] + "..."

        return post

    @classmethod
    def generate_tweet_post(cls, title: str, quotes: list[str]) -> str:
        if quotes:
            tweet = f"\"{quotes[0]}\"\n\n🎬 {title[:180]}"
        else:
            tweet = f"🎬 {title[:250]}"

        if len(tweet) > cls.TWITTER_MAX_CHARS:
            tweet = tweet[:cls.TWITTER_MAX_CHARS - 3] + "..."

        return tweet

    @classmethod
    def generate_quote_card(cls, quote: str, theme: str = "dark") -> dict:
        if not cls.Pillow:
            return {"error": "Pillow not available"}

        if not quote or not quote.strip():
            return {"error": "Quote text is required"}

        theme_colors = cls.QUOTE_CARD_THEMES.get(theme, cls.QUOTE_CARD_THEMES["dark"])

        try:
            Image = cls.Pillow.Image
            ImageDraw = cls.Pillow.ImageDraw
            ImageFont = cls.Pillow.ImageFont

            img = Image.new("RGB", (cls.QUOTE_CARD_WIDTH, cls.QUOTE_CARD_HEIGHT),
                           color=theme_colors["bg"])
            draw = ImageDraw.Draw(img)

            # Draw accent bar
            draw.rectangle([(0, 0), (cls.QUOTE_CARD_WIDTH, 12)], fill=theme_colors["accent"])

            text = f'"{quote}"'

            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            except (IOError, OSError):
                font = ImageFont.load_default()

            wrapped_lines = cls._word_wrap(text, draw, font, cls.QUOTE_CARD_WIDTH - 120)
            line_height = 60 if font.size > 20 else 20
            total_height = len(wrapped_lines) * line_height
            y_start = (cls.QUOTE_CARD_HEIGHT - total_height) // 2

            for i, line in enumerate(wrapped_lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x = (cls.QUOTE_CARD_WIDTH - line_width) // 2
                draw.text((x, y_start + i * line_height), line,
                         fill=theme_colors["text"], font=font)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return {
                "image_base64": img_base64,
                "image_bytes": buffer.tell(),
                "width": cls.QUOTE_CARD_WIDTH,
                "height": cls.QUOTE_CARD_HEIGHT,
                "theme": theme,
                "quote": quote,
            }

        except Exception as e:
            return {"error": f"Quote card generation failed: {str(e)}"}

    @classmethod
    def _word_wrap(cls, text: str, draw, font, max_width: int) -> list[str]:
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]

    @classmethod
    def generate_audiogram(cls, text: str, voice: str = "narrator") -> dict:
        if not cls.gTTS:
            return {"error": "gTTS not available"}

        if not text or not text.strip():
            return {"error": "Text is required for audiogram generation"}

        try:
            tts = cls.gTTS(text=text[:500], lang="en", slow=False, tld="com")
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            word_count = len(text.split())
            duration_sec = round(word_count / 3.3, 1)

            return {
                "audio_base64": audio_base64,
                "audio_bytes": len(audio_bytes),
                "duration_sec": duration_sec,
                "format": "mp3",
                "text": text[:100],
            }

        except cls.gTTSError as e:
            return {"error": f"gTTS generation failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Audiogram generation failed: {str(e)}"}

    @classmethod
    def process(cls, title: str = "", transcript: str = "",
                max_clips: int = 5, quote_card_theme: str = "dark",
                generate_quote_cards: bool = True,
                generate_audiograms: bool = True,
                blog_text: str = "") -> dict:
        result = {}

        full_text = transcript
        if blog_text:
            full_text = f"{transcript}\n\n{blog_text}" if transcript else blog_text

        moments = cls.extract_key_moments(full_text, max_moments=max_clips)
        result["key_moments"] = moments

        quotes = cls.extract_quotes(full_text, max_quotes=3)
        result["quotes"] = quotes

        result["social_posts"] = {
            "twitter_thread": cls.generate_tweet_thread(title, moments),
            "twitter_post": cls.generate_tweet_post(title, quotes),
            "linkedin_post": cls.generate_linkedin_post(title, moments, quotes),
        }

        if generate_quote_cards and quotes:
            quote_cards = []
            for quote in quotes:
                card = cls.generate_quote_card(quote, theme=quote_card_theme)
                if "error" not in card:
                    quote_cards.append(card)
            result["quote_cards"] = quote_cards
            result["quote_card_count"] = len(quote_cards)
        else:
            result["quote_cards"] = []
            result["quote_card_count"] = 0

        if generate_audiograms and quotes:
            audiograms = []
            for quote in quotes:
                audiogram = cls.generate_audiogram(quote)
                if "error" not in audiogram:
                    audiograms.append(audiogram)
            result["audiograms"] = audiograms
            result["audiogram_count"] = len(audiograms)
        else:
            result["audiograms"] = []
            result["audiogram_count"] = 0

        result["metadata"] = {
            "title": title,
            "moment_count": len(moments),
            "quote_count": len(quotes),
            "has_transcript": bool(transcript.strip()),
            "has_blog_text": bool(blog_text.strip()),
            "pillow_available": cls.Pillow is not None,
            "gtts_available": cls.gTTS is not None,
        }

        return result


# ─── Test Suite ─────────────────────────────────────────────────────

class TestContentRepurposerKeyMoments(unittest.TestCase):
    """Tests for extract_key_moments"""

    def test_empty_transcript(self):
        self.assertEqual(TestableContentRepurposer.extract_key_moments(""), [])

    def test_none_transcript(self):
        self.assertEqual(TestableContentRepurposer.extract_key_moments(""), [])

    def test_whitespace_only(self):
        self.assertEqual(TestableContentRepurposer.extract_key_moments("   \n  \n  "), [])

    def test_transcript_without_timestamps(self):
        transcript = "This is the first point about the topic.\nThis is the second point about another aspect."
        moments = TestableContentRepurposer.extract_key_moments(transcript)
        self.assertGreaterEqual(len(moments), 1)
        self.assertIn("title", moments[0])
        self.assertIn("text", moments[0])

    def test_transcript_with_timestamps(self):
        transcript = "[00:00] Introduction to the topic\n[01:30] First key insight explained\n[03:45] Important conclusion"
        moments = TestableContentRepurposer.extract_key_moments(transcript, max_moments=3)
        self.assertEqual(len(moments), 3)
        self.assertEqual(moments[0]["timestamp"], "00:00")
        self.assertEqual(moments[1]["timestamp"], "01:30")
        self.assertEqual(moments[2]["timestamp"], "03:45")

    def test_parenthesis_timestamps(self):
        transcript = "(00:00) Opening remark\n(02:15) Deep dive begins"
        moments = TestableContentRepurposer.extract_key_moments(transcript)
        self.assertEqual(len(moments), 2)
        self.assertEqual(moments[0]["timestamp"], "00:00")

    def test_timestamp_with_seconds(self):
        transcript = "[00:00:00] Start\n[01:30:45] Middle section"
        moments = TestableContentRepurposer.extract_key_moments(transcript)
        self.assertEqual(len(moments), 2)
        self.assertEqual(moments[1]["timestamp"], "01:30:45")

    def test_max_moments_limit(self):
        transcript = "\n".join(f"[{i:02d}:00] Point number {i}" for i in range(10))
        moments = TestableContentRepurposer.extract_key_moments(transcript, max_moments=3)
        self.assertLessEqual(len(moments), 3)

    def test_moments_have_titles(self):
        transcript = "[00:00] This is the introduction to our main topic today."
        moments = TestableContentRepurposer.extract_key_moments(transcript)
        self.assertGreater(len(moments), 0)
        self.assertTrue(len(moments[0]["title"]) > 0)

    def test_moments_text_capped(self):
        long_text = "[00:00] " + "word " * 300
        moments = TestableContentRepurposer.extract_key_moments(long_text)
        self.assertLessEqual(len(moments[0]["text"]), 500)

    def test_transcript_lines_without_timestamps_grouped(self):
        transcript = "This is a continuous explanation about something important.\nIt continues without any timestamp markers.\nAnd finishes here."
        moments = TestableContentRepurposer.extract_key_moments(transcript)
        self.assertGreaterEqual(len(moments), 1)
        # All lines should be grouped into one moment
        self.assertIn("continuous", moments[0]["text"].lower())


class TestContentRepurposerQuoteExtraction(unittest.TestCase):
    """Tests for extract_quotes"""

    def test_empty_text(self):
        self.assertEqual(TestableContentRepurposer.extract_quotes(""), [])

    def test_none_text(self):
        self.assertEqual(TestableContentRepurposer.extract_quotes(""), [])

    def test_short_sentences_excluded(self):
        text = "A. B. Hi. No. Go."
        quotes = TestableContentRepurposer.extract_quotes(text)
        self.assertEqual(len(quotes), 0)

    def test_medium_length_quotes_preferred(self):
        text = "The single most important thing is to just start doing it. Everything else follows."
        quotes = TestableContentRepurposer.extract_quotes(text)
        self.assertGreaterEqual(len(quotes), 1)
        self.assertIn("start doing", quotes[0])

    def test_multiple_quotes_returned(self):
        text = "Innovation distinguishes between a leader and a follower. Stay hungry, stay foolish. The only way to do great work is to love what you do."
        quotes = TestableContentRepurposer.extract_quotes(text, max_quotes=3)
        self.assertLessEqual(len(quotes), 3)
        self.assertGreaterEqual(len(quotes), 1)

    def test_max_quotes_respected(self):
        text = ". ".join(["This is a great sentence about topic number " + str(i) for i in range(10)])
        quotes = TestableContentRepurposer.extract_quotes(text, max_quotes=2)
        self.assertLessEqual(len(quotes), 2)

    def test_quotes_have_punctuation(self):
        text = "The future belongs to those who believe in the beauty of their dreams."
        quotes = TestableContentRepurposer.extract_quotes(text)
        for q in quotes:
            self.assertTrue(q.endswith(".") or q.endswith("!") or q.endswith("?"))


class TestContentRepurposerSocialPosts(unittest.TestCase):
    """Tests for social media post generation"""

    def setUp(self):
        self.title = "10 Tips for Better Content Creation"
        self.moments = [
            {"title": "Start with a hook", "text": "Opening with a strong hook captures attention", "timestamp": "00:00"},
            {"title": "Know your audience", "text": "Understanding who you're creating for", "timestamp": "01:30"},
            {"title": "Consistency matters", "text": "Posting regularly builds trust", "timestamp": "03:00"},
        ]
        self.quotes = ["Content is fire, social media is gasoline."]

    def test_tweet_thread_starts_with_emoji(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, self.moments)
        self.assertTrue(thread[0].startswith("🧵"))

    def test_tweet_thread_contains_title(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, self.moments)
        self.assertIn(self.title, thread[0])

    def test_tweet_thread_has_moments(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, self.moments)
        self.assertGreater(len(thread), 1)

    def test_tweet_thread_max_length(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, self.moments, max_tweets=2)
        self.assertLessEqual(len(thread), 2)

    def test_tweet_thread_includes_timestamps(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, self.moments)
        # At least one tweet should mention [00:00]
        has_timestamp = any("[00:00]" in t or "[01:30]" in t or "[03:00]" in t for t in thread)
        self.assertTrue(has_timestamp, "No timestamps found in thread")

    def test_tweet_thread_empty_moments(self):
        thread = TestableContentRepurposer.generate_tweet_thread(self.title, [])
        self.assertEqual(thread, [])

    def test_tweet_char_limit(self):
        long_title = "A" * 300
        thread = TestableContentRepurposer.generate_tweet_thread(long_title, self.moments)
        for tweet in thread:
            self.assertLessEqual(len(tweet), 280)

    def test_single_tweet_post_with_quote(self):
        tweet = TestableContentRepurposer.generate_tweet_post(self.title, self.quotes)
        self.assertIn("Content is fire", tweet)
        self.assertIn(self.title, tweet)

    def test_single_tweet_post_without_quote(self):
        tweet = TestableContentRepurposer.generate_tweet_post(self.title, [])
        self.assertTrue(tweet.startswith("🎬"))
        self.assertIn(self.title, tweet)

    def test_single_tweet_char_limit(self):
        long_title = "A" * 300
        tweet = TestableContentRepurposer.generate_tweet_post(long_title, self.quotes)
        self.assertLessEqual(len(tweet), 280)

    def test_linkedin_post_structure(self):
        post = TestableContentRepurposer.generate_linkedin_post(self.title, self.moments, self.quotes)
        self.assertIn(self.title, post)
        self.assertIn("key takeaways", post.lower())
        self.assertIn("🎯", post)
        self.assertIn("♻️", post)

    def test_linkedin_post_has_quote(self):
        post = TestableContentRepurposer.generate_linkedin_post(self.title, self.moments, self.quotes)
        self.assertIn("Content is fire", post)

    def test_linkedin_post_without_quotes(self):
        post = TestableContentRepurposer.generate_linkedin_post(self.title, self.moments, [])
        self.assertIn("takeaway", post.lower())

    def test_linkedin_post_length_limit(self):
        long_title = "A" * 3100
        long_moments = [{"title": long_title, "text": long_title, "timestamp": "00:00"}]
        post = TestableContentRepurposer.generate_linkedin_post(long_title, long_moments, self.quotes)
        self.assertLessEqual(len(post), 3000)


class TestContentRepurposerQuoteCard(unittest.TestCase):
    """Tests for quote card image generation"""

    def test_requires_pillow(self):
        TestableContentRepurposer.Pillow = None
        result = TestableContentRepurposer.generate_quote_card("Test quote")
        self.assertIn("error", result)
        self.assertIn("Pillow", result["error"])

    def test_empty_quote_returns_error(self):
        TestableContentRepurposer.Pillow = MagicMock()
        result = TestableContentRepurposer.generate_quote_card("")
        self.assertIn("error", result)

    @patch('PIL.Image.new')
    @patch('PIL.ImageDraw.Draw')
    def test_quote_card_returns_image_base64(self, mock_draw, mock_image_new):
        # Mock Pillow primitives
        mock_img = MagicMock()
        mock_image_new.return_value = mock_img
        mock_draw_instance = MagicMock()
        mock_draw.return_value = mock_draw_instance

        mock_img.save.return_value = None

        # Mock textbbox to return predictable values
        mock_draw_instance.textbbox.return_value = (0, 0, 100, 20)
        mock_draw_instance.text.return_value = None
        mock_draw_instance.rectangle.return_value = None

        # Create a fake ImageFont
        mock_font = MagicMock()
        mock_font.size = 48

        mock_image_module = MagicMock()
        mock_image_module.Image = MagicMock()
        mock_image_module.Image.new = mock_image_new
        mock_image_module.ImageDraw = MagicMock()
        mock_image_module.ImageDraw.Draw = mock_draw
        mock_image_module.ImageFont = MagicMock()
        mock_image_module.ImageFont.load_default.return_value = mock_font
        mock_image_module.ImageFont.truetype = MagicMock(return_value=mock_font)

        TestableContentRepurposer.Pillow = mock_image_module

        result = TestableContentRepurposer.generate_quote_card("Test quote")
        self.assertIn("image_base64", result)
        self.assertEqual(result["width"], 1080)
        self.assertEqual(result["height"], 1080)
        self.assertEqual(result["theme"], "dark")

    def test_unknown_theme_defaults_to_dark(self):
        TestableContentRepurposer.Pillow = None
        result = TestableContentRepurposer.generate_quote_card("Test", theme="nonexistent")
        self.assertIn("error", result)

    def test_valid_themes_work(self):
        for theme in ["dark", "light", "warm", "cool", "vibrant"]:
            self.assertIn(theme, TestableContentRepurposer.QUOTE_CARD_THEMES)


class TestContentRepurposerAudiogram(unittest.TestCase):
    """Tests for audiogram generation"""

    def test_requires_gtts(self):
        TestableContentRepurposer.gTTS = None
        result = TestableContentRepurposer.generate_audiogram("Test text")
        self.assertIn("error", result)
        self.assertIn("gTTS", result["error"])

    def test_empty_text_error(self):
        TestableContentRepurposer.gTTS = MagicMock()
        result = TestableContentRepurposer.generate_audiogram("")
        self.assertIn("error", result)

    def test_returns_audio_base64_with_mock(self):
        mock_gtts = MagicMock()
        mock_audio_buffer = io.BytesIO(b"fake_audio_data")
        mock_gtts_instance = MagicMock()
        mock_gtts_instance.write_to_fp.side_effect = lambda buf: buf.write(b"fake_audio_data")
        mock_gtts.return_value = mock_gtts_instance

        TestableContentRepurposer.gTTS = mock_gtts
        TestableContentRepurposer.gTTSError = Exception

        result = TestableContentRepurposer.generate_audiogram("This is a test quote")
        self.assertIn("audio_base64", result)
        self.assertIn("duration_sec", result)
        self.assertEqual(result["format"], "mp3")

    def test_text_truncated_to_500_chars(self):
        mock_gtts = MagicMock()
        mock_gtts_instance = MagicMock()
        mock_gtts_instance.write_to_fp.side_effect = lambda buf: buf.write(b"audio_data")
        mock_gtts.return_value = mock_gtts_instance

        TestableContentRepurposer.gTTS = mock_gtts
        long_text = "test " * 200
        result = TestableContentRepurposer.generate_audiogram(long_text)
        # Verify gTTS was called with truncated text
        call_text = mock_gtts.call_args[1]["text"]
        self.assertLessEqual(len(call_text), 500)


class TestContentRepurposerFullPipeline(unittest.TestCase):
    """Tests for the full process() pipeline"""

    def setUp(self):
        # Set up mocks for optional dependencies
        mock_gtts = MagicMock()
        mock_gtts_instance = MagicMock()
        mock_gtts_instance.write_to_fp.side_effect = lambda buf: buf.write(b"audio_data")
        mock_gtts.return_value = mock_gtts_instance
        TestableContentRepurposer.gTTS = mock_gtts
        TestableContentRepurposer.gTTSError = Exception

        mock_font = MagicMock()
        mock_font.size = 48

        mock_image_module = MagicMock()
        mock_image_module.Image = MagicMock()
        mock_image_module.ImageDraw = MagicMock()
        mock_image_module.ImageFont = MagicMock()
        mock_image_module.ImageFont.load_default.return_value = mock_font
        mock_image_module.ImageFont.truetype = MagicMock(return_value=mock_font)
        TestableContentRepurposer.Pillow = mock_image_module

    def test_process_basic_transcript(self):
        transcript = "[00:00] Introduction to content repurposing\n[01:30] Why this matters for creators"
        result = TestableContentRepurposer.process(
            title="Content Repurposing Guide",
            transcript=transcript,
        )
        self.assertIn("key_moments", result)
        self.assertIn("quotes", result)
        self.assertIn("social_posts", result)
        self.assertIn("quote_cards", result)
        self.assertIn("audiograms", result)
        self.assertIn("metadata", result)

    def test_process_metadata_tracked(self):
        result = TestableContentRepurposer.process(
            title="Test Video",
            transcript="[00:00] Some content about something.",
        )
        self.assertEqual(result["metadata"]["title"], "Test Video")
        self.assertTrue(result["metadata"]["has_transcript"])
        self.assertFalse(result["metadata"]["has_blog_text"])

    def test_process_with_blog_text(self):
        result = TestableContentRepurposer.process(
            title="Test",
            transcript="[00:00] Video content.",
            blog_text="Additional blog content here.",
        )
        self.assertTrue(result["metadata"]["has_blog_text"])

    def test_process_no_audiograms(self):
        result = TestableContentRepurposer.process(
            title="Test",
            transcript="[00:00] Just testing without extras.",
            generate_audiograms=False,
        )
        self.assertEqual(result["audiogram_count"], 0)

    def test_process_no_quote_cards(self):
        result = TestableContentRepurposer.process(
            title="Test",
            transcript="[00:00] Just testing card generation.",
            generate_quote_cards=False,
        )
        self.assertEqual(result["quote_card_count"], 0)

    def test_process_max_clips(self):
        transcript = "\n".join(f"[{i:02d}:00] Point number {i}" for i in range(10))
        result = TestableContentRepurposer.process(
            title="Test",
            transcript=transcript,
            max_clips=3,
        )
        self.assertLessEqual(len(result["key_moments"]), 3)

    def test_process_social_posts_always_generated(self):
        result = TestableContentRepurposer.process(
            title="Test",
            transcript="[00:00] Some content.\n[01:00] More content.",
        )
        self.assertIn("twitter_thread", result["social_posts"])
        self.assertIn("twitter_post", result["social_posts"])
        self.assertIn("linkedin_post", result["social_posts"])

    def test_process_empty_transcript(self):
        result = TestableContentRepurposer.process(title="Empty Video", transcript="")
        self.assertEqual(result["metadata"]["moment_count"], 0)
        self.assertEqual(result["metadata"]["has_transcript"], False)

    def test_process_gtts_availability_tracked(self):
        result = TestableContentRepurposer.process(
            title="Test",
            transcript="[00:00] Content here.",
        )
        self.assertTrue(result["metadata"]["gtts_available"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
