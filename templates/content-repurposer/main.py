"""
Content Repurposing Pipeline — Apify Actor
============================================
Takes a video URL (YouTube) and/or blog post text, then automatically generates:
  - Short-form social media posts (Twitter/X, LinkedIn)
  - Quote cards (Pillow-based visual quotes for Instagram/Twitter)
  - Audiogram snippets (gTTS audio of key quotes)
  - Key moments / timestamps from the video
  - Platform-specific content recommendations

Features:
  - YouTube URL → transcript + metadata (via yt-dlp)
  - Blog post text → analysis + repurposing
  - Quote card generation with background colors, text overlay
  - Audiogram generation via gTTS
  - Multiple social media formats

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms.

Usage:
    Input:  {"videoUrl": "https://youtube.com/watch?v=...", "maxClips": 5}
    Output: {"title": "...", "key_moments": [...], "social_posts": {...},
             "quote_cards": [...], "audiograms": [...], "metadata": {...}}
"""

import base64
import io
import json
import math
import os
import re
import textwrap
from io import BytesIO
from typing import Any, Optional
from xml.etree import ElementTree

from apify import Actor

# Optional: Pillow for quote card images
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# Optional: gTTS for audiogram audio
try:
    from gtts import gTTS, gTTSError
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# ─── Pure logic class (testable without apify SDK) ──────────────────────

class ContentRepurposer:
    """Content repurposing engine.

    Takes video metadata / transcript and generates social media posts,
    quote cards, key moments, and audiogram snippets.
    Designed to be testable WITHOUT the apify SDK.
    """

    # Default quote card dimensions (Instagram square)
    QUOTE_CARD_WIDTH = 1080
    QUOTE_CARD_HEIGHT = 1080

    # Color palettes for quote cards
    QUOTE_CARD_THEMES = {
        "dark": {"bg": (30, 30, 30), "text": (255, 255, 255), "accent": (255, 200, 50)},
        "light": {"bg": (255, 255, 255), "text": (40, 40, 40), "accent": (50, 120, 200)},
        "warm": {"bg": (50, 30, 20), "text": (255, 240, 220), "accent": (230, 150, 70)},
        "cool": {"bg": (20, 40, 60), "text": (230, 240, 255), "accent": (100, 180, 230)},
        "vibrant": {"bg": (100, 30, 60), "text": (255, 235, 240), "accent": (255, 200, 100)},
    }

    # Maximum characters per tweet
    TWITTER_MAX_CHARS = 280
    TWEET_THREAD_MAX_LENGTH = 25

    # Maximum LinkedIn post length
    LINKEDIN_MAX_CHARS = 3000

    @classmethod
    def extract_key_moments(cls, transcript: str, max_moments: int = 5) -> list[dict]:
        """Extract key moments from a transcript.

        Uses heuristic-based approach: finds numbered sections, timestamps,
        and topically distinct segments.

        Args:
            transcript: Full video transcript text
            max_moments: Maximum number of moments to extract

        Returns:
            List of dicts with 'title', 'text', 'timestamp' keys
        """
        if not transcript or not transcript.strip():
            return []

        lines = transcript.strip().split("\n")
        moments = []
        current_moment = {"title": "", "text": "", "timestamp": ""}

        # Try to find timestamp patterns like [00:00] or (00:00)
        timestamp_pattern = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for timestamp
            ts_match = timestamp_pattern.search(line)
            if ts_match:
                ts = ts_match.group(1)
                # New section — save previous
                if current_moment["text"]:
                    moments.append(current_moment)
                    current_moment = {"title": "", "text": "", "timestamp": ""}
                current_moment["timestamp"] = ts
                # Text after timestamp or on next line
                text_after = line[ts_match.end():].strip().lstrip(":] ")
                if text_after:
                    current_moment["text"] += text_after + " "
            else:
                # Accumulate text for current moment
                current_moment["text"] += line + " "

        # Don't forget the last moment
        if current_moment["text"]:
            moments.append(current_moment)

        # Generate titles for each moment
        for moment in moments:
            text = moment["text"].strip()
            # Use first sentence or first N chars as title
            first_sentence = re.split(r"[.!?]", text)[0] if text else ""
            moment["title"] = first_sentence[:80].strip() if first_sentence else "Key moment"

            # Clean up text
            moment["text"] = text[:500].strip()

        # Limit to max_moments
        if len(moments) > max_moments:
            # Keep evenly spaced moments
            step = len(moments) / max_moments
            moments = [moments[int(i * step)] for i in range(max_moments)]

        return moments

    @classmethod
    def extract_quotes(cls, text: str, max_quotes: int = 3) -> list[str]:
        """Extract quotable snippets from text.

        Looks for notable sentences — short, impactful statements.

        Args:
            text: Source text
            max_quotes: Max quotes to return

        Returns:
            List of quote strings
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 280]

        # Prefer shorter, punchy sentences (the "quotable" ones)
        scored = []
        for s in sentences:
            word_count = len(s.split())
            # Ideal quote: 5-20 words
            if 5 <= word_count <= 25:
                score = 100 - abs(word_count - 12) * 3  # Peak at 12 words
                scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        quotes = [s[1] + "." for s in scored[:max_quotes] if s[0] > 50]

        return quotes if quotes else sentences[:max_quotes]

    @classmethod
    def generate_tweet_thread(cls, title: str, key_moments: list[dict],
                              max_tweets: int = 5) -> list[str]:
        """Generate a Twitter/X thread from key moments.

        Args:
            title: Video title
            key_moments: List of moment dicts with 'title', 'text', 'timestamp'
            max_tweets: Max tweets in thread

        Returns:
            List of tweet strings ready to post
        """
        if not key_moments:
            return []

        thread = []

        # First tweet: Hook with title
        thread.append(f"🧵 {title[:200]}")

        # Body tweets: One per key moment
        for i, moment in enumerate(key_moments[:max_tweets - 1]):
            ts = moment.get("timestamp", "")
            title_text = moment.get("title", "")
            body_text = moment.get("text", "")[:150]

            tweet = f"{i+1}. {title_text}"
            if ts:
                tweet += f" [{ts}]"
            if body_text:
                tweet += f"\n\n{body_text}"

            # Truncate to Twitter limit
            if len(tweet) > cls.TWITTER_MAX_CHARS:
                tweet = tweet[:cls.TWITTER_MAX_CHARS - 3] + "..."

            thread.append(tweet)

        return thread

    @classmethod
    def generate_linkedin_post(cls, title: str, key_moments: list[dict],
                                quotes: list[str]) -> str:
        """Generate a LinkedIn post from video content.

        Args:
            title: Video title
            key_moments: List of moment dicts
            quotes: Extracted quotable snippets

        Returns:
            Full LinkedIn post text
        """
        lines = []

        # Hook
        lines.append(f"I just watched/discussed \"{title}\" and here are the key takeaways:\n")

        # Key moments as bullet points
        for i, moment in enumerate(key_moments[:4], 1):
            title_text = moment.get("title", "")
            ts = moment.get("timestamp", "")
            ts_str = f" [{ts}]" if ts else ""
            lines.append(f"🎯 {i}. {title_text}{ts_str}")

        lines.append("")

        # Add a quote if available
        if quotes:
            lines.append(f"💡 \"{quotes[0]}\"\n")

        # Call to action
        lines.append("What's your #1 takeaway? ♻️ Repost if this was valuable.")

        post = "\n".join(lines)

        # Truncate to LinkedIn limit
        if len(post) > cls.LINKEDIN_MAX_CHARS:
            post = post[:cls.LINKEDIN_MAX_CHARS - 3] + "..."

        return post

    @classmethod
    def generate_tweet_post(cls, title: str, quotes: list[str]) -> str:
        """Generate a single Twitter/X post from the content.

        Args:
            title: Video title
            quotes: Extracted quotes

        Returns:
            Single tweet text
        """
        if quotes:
            tweet = f"\"{quotes[0]}\"\n\n🎬 {title[:180]}"
        else:
            tweet = f"🎬 {title[:250]}"

        if len(tweet) > cls.TWITTER_MAX_CHARS:
            tweet = tweet[:cls.TWITTER_MAX_CHARS - 3] + "..."

        return tweet

    @classmethod
    def generate_quote_card(cls, quote: str, theme: str = "dark") -> dict:
        """Generate a quote card image.

        Creates a Pillow-based social media card with the quote text.

        Args:
            quote: The quote text to display
            theme: Color theme key (dark, light, warm, cool, vibrant)

        Returns:
            Dict with 'image_base64', 'width', 'height', 'theme' or 'error'
        """
        if not HAS_PILLOW:
            return {"error": "Pillow not available — install Pillow>=10.0.0"}

        if not quote or not quote.strip():
            return {"error": "Quote text is required"}

        theme_colors = cls.QUOTE_CARD_THEMES.get(theme, cls.QUOTE_CARD_THEMES["dark"])

        try:
            # Create image
            img = Image.new("RGB", (cls.QUOTE_CARD_WIDTH, cls.QUOTE_CARD_HEIGHT),
                           color=theme_colors["bg"])
            draw = ImageDraw.Draw(img)

            # Draw border accent
            accent_height = 12
            draw.rectangle([(0, 0), (cls.QUOTE_CARD_WIDTH, accent_height)],
                          fill=theme_colors["accent"])

            # Draw quote text
            text = f'"{quote}"'
            max_text_width = cls.QUOTE_CARD_WIDTH - 120  # 60px padding each side

            # Use default font (Pillow's built-in)
            font_size = 48
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()

            # Word wrap
            wrapped_lines = cls._word_wrap(text, draw, font, max_text_width)

            # Calculate total text height
            line_height = font_size + 10
            total_height = len(wrapped_lines) * line_height

            # Start Y position (centered vertically)
            y_start = (cls.QUOTE_CARD_HEIGHT - total_height) // 2

            # Draw each line
            for i, line in enumerate(wrapped_lines):
                # Center the text horizontally
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x = (cls.QUOTE_CARD_WIDTH - line_width) // 2
                draw.text((x, y_start + i * line_height), line,
                         fill=theme_colors["text"], font=font)

            # Convert to base64
            buffer = BytesIO()
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
        """Wrap text to fit within a given pixel width.

        Args:
            text: Text to wrap
            draw: ImageDraw instance
            font: PIL font object
            max_width: Maximum pixel width per line

        Returns:
            List of wrapped lines
        """
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
        """Generate an audiogram audio snippet from text.

        Uses gTTS to create an audio file of the spoken text.

        Args:
            text: Text to convert to speech
            voice: Voice preset (narrator, friendly, professional, etc.)

        Returns:
            Dict with 'audio_base64', 'duration_sec', or 'error'
        """
        if not HAS_GTTS:
            return {"error": "gTTS not available — install gtts>=2.5.0"}

        if not text or not text.strip():
            return {"error": "Text is required for audiogram generation"}

        try:
            # Use standard gTTS (US English)
            tts = gTTS(text=text[:500], lang="en", slow=False, tld="com")
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Estimate duration (~200 words per minute = ~3.3 words/sec)
            word_count = len(text.split())
            duration_sec = round(word_count / 3.3, 1)

            return {
                "audio_base64": audio_base64,
                "audio_bytes": len(audio_bytes),
                "duration_sec": duration_sec,
                "format": "mp3",
                "text": text[:100],
            }

        except gTTSError as e:
            return {"error": f"gTTS generation failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Audiogram generation failed: {str(e)}"}

    @classmethod
    def process(cls, title: str = "", transcript: str = "",
                max_clips: int = 5, quote_card_theme: str = "dark",
                generate_quote_cards: bool = True,
                generate_audiograms: bool = True,
                blog_text: str = "") -> dict:
        """Full pipeline: extract moments, generate posts, generate cards.

        Args:
            title: Video/blog title
            transcript: Video transcript text
            max_clips: Max moments to extract
            quote_card_theme: Color theme for quote cards
            generate_quote_cards: Whether to generate quote card images
            generate_audiograms: Whether to generate audiogram audio
            blog_text: Additional blog post text (optional)

        Returns:
            Dict with all repurposed content
        """
        result: dict[str, Any] = {}

        # Combine transcript and blog text for analysis
        full_text = transcript
        if blog_text:
            full_text = f"{transcript}\n\n{blog_text}" if transcript else blog_text

        # Extract key moments
        moments = cls.extract_key_moments(full_text, max_moments=max_clips)
        result["key_moments"] = moments

        # Extract quotes
        quotes = cls.extract_quotes(full_text, max_quotes=3)
        result["quotes"] = quotes

        # Generate social posts
        result["social_posts"] = {
            "twitter_thread": cls.generate_tweet_thread(title, moments),
            "twitter_post": cls.generate_tweet_post(title, quotes),
            "linkedin_post": cls.generate_linkedin_post(title, moments, quotes),
        }

        # Generate quote card images
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

        # Generate audiograms
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

        # Metadata
        result["metadata"] = {
            "title": title,
            "moment_count": len(moments),
            "quote_count": len(quotes),
            "has_transcript": bool(transcript.strip()),
            "has_blog_text": bool(blog_text.strip()),
            "pillow_available": HAS_PILLOW,
            "gtts_available": HAS_GTTS,
        }

        return result


# ─── Apify SDK wrapper (runs in Docker) ────────────────────────────────

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        title = actor_input.get("title", "")
        transcript = actor_input.get("transcript", "")
        blog_text = actor_input.get("blogText", "")
        video_url = actor_input.get("videoUrl", "")
        blog_url = actor_input.get("blogUrl", "")
        max_clips = actor_input.get("maxClips", 5)
        quote_card_theme = actor_input.get("quoteCardTheme", "dark")
        generate_quote_cards = actor_input.get("generateQuoteCards", True)
        generate_audiograms = actor_input.get("generateAudiograms", True)
        action = actor_input.get("action", "process")

        # Handle listing actions
        if action == "list_themes":
            themes = list(ContentRepurposer.QUOTE_CARD_THEMES.keys())
            await Actor.push_data({
                "available_themes": themes,
                "themes": {
                    k: {
                        "bg": f"rgb{v['bg']}",
                        "text": f"rgb{v['text']}",
                        "accent": f"rgb{v['accent']}",
                    }
                    for k, v in ContentRepurposer.QUOTE_CARD_THEMES.items()
                },
            })
            Actor.log.info(f"Returned {len(themes)} quote card themes")
            return

        # Validate: need at least transcript, blogText, or videoUrl
        if not transcript and not blog_text and not video_url:
            raise RuntimeError(
                "One of 'transcript', 'blogText', or 'videoUrl' is required"
            )

        # Validate max_clips
        try:
            max_clips = int(max_clips)
            max_clips = max(1, min(10, max_clips))
        except (ValueError, TypeError):
            max_clips = 5

        # Validate theme
        valid_themes = list(ContentRepurposer.QUOTE_CARD_THEMES.keys())
        if quote_card_theme not in valid_themes:
            Actor.log.warning(f"Invalid theme '{quote_card_theme}', using 'dark'")
            quote_card_theme = "dark"

        # If videoUrl is provided but no transcript, we fetch metadata
        if video_url and not transcript:
            Actor.log.info(f"Video URL provided: {video_url}")
            try:
                metadata = await _fetch_video_metadata(video_url)
                if not title:
                    title = metadata.get("title", "")
                if not transcript:
                    transcript = metadata.get("transcript", "")
                Actor.log.info(f"Fetched metadata: title='{title[:50]}...', "
                              f"transcript_length={len(transcript)}")
            except Exception as e:
                Actor.log.warning(f"Failed to fetch video metadata: {e}")
                # Continue with whatever we have

        # Run the pipeline
        result = ContentRepurposer.process(
            title=title,
            transcript=transcript,
            max_clips=max_clips,
            quote_card_theme=quote_card_theme,
            generate_quote_cards=generate_quote_cards,
            generate_audiograms=generate_audiograms,
            blog_text=blog_text,
        )

        await Actor.push_data(result)
        Actor.log.info(
            f"Content repurposed: "
            f"{result['metadata']['moment_count']} moments, "
            f"{result['metadata']['quote_count']} quotes, "
            f"{result.get('quote_card_count', 0)} cards, "
            f"{result.get('audiogram_count', 0)} audiograms"
        )
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


async def _fetch_video_metadata(video_url: str) -> dict:
    """Fetch video metadata and transcript via yt-dlp.

    Note: This runs in the Docker container where yt-dlp is installed.
    For local testing, returns empty dict if yt-dlp is unavailable.
    """
    try:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Fetch metadata with yt-dlp
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", video_url],
                capture_output=True, text=True, timeout=30,
                cwd=tmpdir,
            )
            if result.returncode != 0:
                return {}

            metadata = json.loads(result.stdout)
            title = metadata.get("title", "")
            description = metadata.get("description", "")
            upload_date = metadata.get("upload_date", "")
            duration = metadata.get("duration", 0)

            # Try to get auto-generated captions
            transcript = ""
            try:
                subprocess.run(
                    ["yt-dlp", "--write-auto-sub", "--sub-lang", "en",
                     "--skip-download", "--sub-format", "vtt",
                     "--output", "captions", video_url],
                    capture_output=True, text=True, timeout=60,
                    cwd=tmpdir,
                )
                # Find caption file
                for f in os.listdir(tmpdir):
                    if f.endswith(".vtt"):
                        with open(os.path.join(tmpdir, f), "r") as cf:
                            vtt_content = cf.read()
                        # Strip VTT header and remove timing info
                        lines = vtt_content.split("\n")
                        text_lines = [
                            l for l in lines
                            if l.strip() and not l.startswith("WEBVTT")
                            and not l.startswith("Kind:")
                            and not l.startswith("Language:")
                            and not "-->" in l
                            and not l.strip().isdigit()
                        ]
                        transcript = " ".join(text_lines)
                        break
            except Exception:
                pass

            return {
                "title": title,
                "description": description,
                "upload_date": upload_date,
                "duration_sec": duration,
                "transcript": transcript or description or "",
            }
    except Exception:
        return {}
