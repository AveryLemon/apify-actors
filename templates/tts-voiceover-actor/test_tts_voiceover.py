"""
Tests for TTS Voiceover Actor — pure logic class tests.

These tests exercise TTSVoiceoverEngine (no apify SDK, no gTTS network calls).
They verify:
  1. Input validation and normalization
  2. Word count estimation
  3. Duration estimation
  4. Text truncation at boundaries
  5. Voice preset listing
  6. Language listing
  7. Error handling for edge cases
  8. Output structure verification (with mocked gTTS)

NOTE: actual gTTS network synthesis is NOT tested here.
"""

import json
import math
import os
import sys
import unittest
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Minimal testable copy of TTSVoiceoverEngine (no apify/gTTS imports) ──

class TTSVoiceoverEngine:
    """Testable copy of the TTSVoiceoverEngine class from main.py.

    Exact same logic, no apify or gTTS imports — gTTS is injected
    via a class-level attribute for easy mocking.
    """

    gTTS = None  # Will be set by tests that need synthesis
    gTTSError = Exception

    VOICE_PRESETS = {
        "narrator": {"tld": "com", "lang": "en", "slow": False,
                      "description": "Clear standard US English narration"},
        "friendly": {"tld": "com", "lang": "en", "slow": False,
                      "description": "Warm, slightly slower US English"},
        "professional": {"tld": "co.uk", "lang": "en", "slow": False,
                          "description": "British English, authoritative tone"},
        "energetic": {"tld": "com", "lang": "en", "slow": False,
                       "description": "US English, standard pace with punch"},
        "soft": {"tld": "com", "lang": "en", "slow": True,
                  "description": "Softer, slower delivery"},
        "australian": {"tld": "com.au", "lang": "en", "slow": False,
                        "description": "Australian English"},
        "indian": {"tld": "co.in", "lang": "en", "slow": False,
                    "description": "Indian English"},
    }

    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "nl", "ru",
        "ja", "ko", "zh-CN", "zh-TW", "ar", "hi", "pl",
        "tr", "sv", "da", "fi", "no", "cs", "ro", "hu",
    ]

    WORDS_PER_SECOND_NORMAL = 200.0 / 60.0
    WORDS_PER_SECOND_SLOW = 150.0 / 60.0

    @staticmethod
    def estimate_word_count(text):
        if not text or not text.strip():
            return 0
        return len([w for w in text.split() if w.strip()])

    @staticmethod
    def estimate_duration_sec(text, slow=False, speed_multiplier=1.0):
        word_count = TTSVoiceoverEngine.estimate_word_count(text)
        wps = TTSVoiceoverEngine.WORDS_PER_SECOND_SLOW if slow else TTSVoiceoverEngine.WORDS_PER_SECOND_NORMAL
        if speed_multiplier > 0:
            base_duration = word_count / wps
            return round(base_duration / speed_multiplier, 2)
        return 0.0

    @staticmethod
    def truncate_text(text, max_chars=5000):
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            last_boundary = truncated.rfind(sep)
            if last_boundary > max_chars * 0.8:
                return truncated[:last_boundary + 1]
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.5:
            return truncated[:last_space]
        return truncated

    @staticmethod
    def validate_input(text, voice, speed, lang):
        errors = []
        if not text or not text.strip():
            errors.append("'text' is required and must be non-empty")
        valid_voices = list(TTSVoiceoverEngine.VOICE_PRESETS.keys())
        if voice is not None and voice not in valid_voices:
            errors.append(f"'voice' must be one of: {', '.join(valid_voices)}")
        if speed is not None:
            try:
                speed_f = float(speed)
                if speed_f < 0.5 or speed_f > 2.0:
                    errors.append("'speed' must be between 0.5 and 2.0")
            except (ValueError, TypeError):
                errors.append("'speed' must be a number")
        if lang is not None:
            if lang not in TTSVoiceoverEngine.SUPPORTED_LANGUAGES:
                errors.append(
                    f"'lang' must be one of: {', '.join(TTSVoiceoverEngine.SUPPORTED_LANGUAGES[:10])}..."
                )
        if errors:
            return {"valid": False, "error": "; ".join(errors)}
        voice = voice or "narrator"
        speed = float(speed) if speed is not None else 1.0
        lang = lang or "en"
        return {
            "valid": True,
            "normalized": {"text": text.strip(), "voice": voice, "speed": speed, "lang": lang},
        }

    @staticmethod
    def list_voices():
        return [
            {"id": key, "name": key.capitalize(), "description": preset["description"],
             "tld": preset["tld"], "lang": preset["lang"]}
            for key, preset in TTSVoiceoverEngine.VOICE_PRESETS.items()
        ]

    @staticmethod
    def list_languages():
        return sorted(TTSVoiceoverEngine.SUPPORTED_LANGUAGES)

    @classmethod
    def synthesize(cls, text, voice="narrator", speed=1.0, lang="en"):
        validation = cls.validate_input(text, voice, speed, lang)
        if not validation["valid"]:
            return {"error": validation["error"]}

        normalized = validation["normalized"]
        text = normalized["text"]
        voice = normalized["voice"]
        speed = normalized["speed"]
        lang = normalized["lang"]

        preset = cls.VOICE_PRESETS.get(voice, cls.VOICE_PRESETS["narrator"])
        tld = preset["tld"]
        slow = preset.get("slow", False) if speed <= 1.0 else False
        if speed > 1.1:
            slow = False

        text = cls.truncate_text(text)

        try:
            gtts = cls.gTTS(text=text, lang=lang, slow=slow, tld=tld)
            audio_buffer = BytesIO()
            gtts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            duration_sec = cls.estimate_duration_sec(text, slow, speed)
            word_count = cls.estimate_word_count(text)
            preview = text[:40].replace(" ", "_").lower()
            filename = f"voiceover_{preview}.mp3"
            parameters = {
                "voice": voice, "voice_description": preset["description"],
                "lang": lang, "tld": tld, "slow": slow,
                "speed_multiplier": speed, "estimated_duration_sec": duration_sec,
                "word_count": word_count, "character_count": len(text),
                "audio_bytes": len(audio_bytes),
            }
            return {
                "audio_base64": audio_base64, "audio_bytes": len(audio_bytes),
                "duration_sec": duration_sec, "filename": filename, "parameters": parameters,
            }
        except Exception as e:
            return {"error": f"Unexpected synthesis error: {str(e)}"}


import base64


# ── Tests ──

class TestWordCount(unittest.TestCase):
    """Test word count estimation."""

    def test_empty_text(self):
        self.assertEqual(TTSVoiceoverEngine.estimate_word_count(""), 0)
        self.assertEqual(TTSVoiceoverEngine.estimate_word_count("   "), 0)
        self.assertEqual(TTSVoiceoverEngine.estimate_word_count(None), 0)

    def test_single_word(self):
        self.assertEqual(TTSVoiceoverEngine.estimate_word_count("Hello"), 1)

    def test_multiple_words(self):
        self.assertEqual(TTSVoiceoverEngine.estimate_word_count("Hello world test"), 3)

    def test_with_punctuation(self):
        self.assertEqual(
            TTSVoiceoverEngine.estimate_word_count("Hello, world! How are you?"), 5
        )

    def test_with_newlines(self):
        self.assertEqual(
            TTSVoiceoverEngine.estimate_word_count("Line one.\nLine two.\nLine three."), 6
        )


class TestDurationEstimation(unittest.TestCase):
    """Test duration estimation."""

    def test_normal_speed(self):
        dur = TTSVoiceoverEngine.estimate_duration_sec(
            "one two three four five six seven eight nine ten"
        )
        self.assertGreater(dur, 1.0)
        self.assertLess(dur, 6.0)

    def test_slow_mode_longer(self):
        dur_normal = TTSVoiceoverEngine.estimate_duration_sec("hello world test", slow=False)
        dur_slow = TTSVoiceoverEngine.estimate_duration_sec("hello world test", slow=True)
        self.assertGreater(dur_slow, dur_normal)

    def test_higher_speed_shorter(self):
        dur_1x = TTSVoiceoverEngine.estimate_duration_sec("hello world " * 10, speed_multiplier=1.0)
        dur_2x = TTSVoiceoverEngine.estimate_duration_sec("hello world " * 10, speed_multiplier=2.0)
        self.assertGreater(dur_1x, dur_2x)

    def test_empty_text_duration(self):
        self.assertEqual(TTSVoiceoverEngine.estimate_duration_sec(""), 0.0)


class TestTextTruncation(unittest.TestCase):
    """Test text truncation at boundaries."""

    def test_short_text_no_truncation(self):
        text = "Hello world, this is a test."
        result = TTSVoiceoverEngine.truncate_text(text, max_chars=100)
        self.assertEqual(result, text)

    def test_truncation_at_sentence_boundary(self):
        text = "This is a long sentence that should be truncated. " * 50
        result = TTSVoiceoverEngine.truncate_text(text, max_chars=200)
        self.assertLessEqual(len(result), 200)

    def test_truncation_empty(self):
        self.assertEqual(TTSVoiceoverEngine.truncate_text(""), "")
        self.assertEqual(TTSVoiceoverEngine.truncate_text(None), "")


class TestInputValidation(unittest.TestCase):
    """Test input validation and normalization."""

    def test_valid_input(self):
        result = TTSVoiceoverEngine.validate_input("Hello world", "narrator", 1.0, "en")
        self.assertTrue(result["valid"])
        self.assertEqual(result["normalized"]["text"], "Hello world")

    def test_missing_text(self):
        result = TTSVoiceoverEngine.validate_input(None, "narrator", 1.0, "en")
        self.assertFalse(result["valid"])
        self.assertIn("required", result["error"])

    def test_empty_text(self):
        result = TTSVoiceoverEngine.validate_input("", "narrator", 1.0, "en")
        self.assertFalse(result["valid"])

    def test_whitespace_only_text(self):
        result = TTSVoiceoverEngine.validate_input("   ", "narrator", 1.0, "en")
        self.assertFalse(result["valid"])

    def test_invalid_voice(self):
        result = TTSVoiceoverEngine.validate_input("Hello", "robot", 1.0, "en")
        self.assertFalse(result["valid"])
        self.assertIn("voice", result["error"])

    def test_invalid_speed_too_low(self):
        result = TTSVoiceoverEngine.validate_input("Hello", "narrator", 0.1, "en")
        self.assertFalse(result["valid"])

    def test_invalid_speed_too_high(self):
        result = TTSVoiceoverEngine.validate_input("Hello", "narrator", 5.0, "en")
        self.assertFalse(result["valid"])

    def test_invalid_language(self):
        result = TTSVoiceoverEngine.validate_input("Hello", "narrator", 1.0, "klingon")
        self.assertFalse(result["valid"])

    def test_default_voice_when_none(self):
        result = TTSVoiceoverEngine.validate_input("Hello", None, None, None)
        self.assertTrue(result["valid"])
        self.assertEqual(result["normalized"]["voice"], "narrator")
        self.assertEqual(result["normalized"]["speed"], 1.0)
        self.assertEqual(result["normalized"]["lang"], "en")

    def test_text_trimming(self):
        result = TTSVoiceoverEngine.validate_input("  Hello world  ", "narrator", 1.0, "en")
        self.assertEqual(result["normalized"]["text"], "Hello world")

    def test_all_voice_presets_valid(self):
        for voice in TTSVoiceoverEngine.VOICE_PRESETS:
            result = TTSVoiceoverEngine.validate_input("Test", voice, 1.0, "en")
            self.assertTrue(result["valid"], f"Voice '{voice}' should be valid")

    def test_speed_boundaries(self):
        for speed_val in [0.5, 2.0]:
            result = TTSVoiceoverEngine.validate_input("Test", "narrator", speed_val, "en")
            self.assertTrue(result["valid"], f"Speed {speed_val} should be valid")
        for speed_val in [0.49, 2.01]:
            result = TTSVoiceoverEngine.validate_input("Test", "narrator", speed_val, "en")
            self.assertFalse(result["valid"], f"Speed {speed_val} should be invalid")


class TestVoiceListing(unittest.TestCase):
    """Test voice preset listing."""

    def test_list_voices_returns_list(self):
        voices = TTSVoiceoverEngine.list_voices()
        self.assertIsInstance(voices, list)

    def test_list_voices_has_all_presets(self):
        voices = TTSVoiceoverEngine.list_voices()
        voice_ids = [v["id"] for v in voices]
        for preset_id in TTSVoiceoverEngine.VOICE_PRESETS:
            self.assertIn(preset_id, voice_ids)

    def test_voice_has_required_fields(self):
        for voice in TTSVoiceoverEngine.list_voices():
            self.assertIn("id", voice)
            self.assertIn("name", voice)
            self.assertIn("description", voice)
            self.assertIn("tld", voice)
            self.assertIn("lang", voice)

    def test_narrator_is_first(self):
        self.assertEqual(TTSVoiceoverEngine.list_voices()[0]["id"], "narrator")


class TestLanguageListing(unittest.TestCase):
    """Test supported language listing."""

    def test_list_languages_returns_list(self):
        langs = TTSVoiceoverEngine.list_languages()
        self.assertIsInstance(langs, list)

    def test_english_is_included(self):
        self.assertIn("en", TTSVoiceoverEngine.list_languages())

    def test_returns_sorted(self):
        self.assertEqual(TTSVoiceoverEngine.list_languages(),
                         sorted(TTSVoiceoverEngine.list_languages()))


class TestSynthesizeEdgeCases(unittest.TestCase):
    """Test synthesize() for pure error handling (no gTTS needed)."""

    def test_synthesize_empty_text(self):
        result = TTSVoiceoverEngine.synthesize("")
        self.assertIn("error", result)

    def test_synthesize_invalid_voice(self):
        result = TTSVoiceoverEngine.synthesize("Hello world", voice="invalid")
        self.assertIn("error", result)

    def test_synthesize_none_text(self):
        result = TTSVoiceoverEngine.synthesize(None)
        self.assertIn("error", result)


class TestSynthesizeWithMockGtts(unittest.TestCase):
    """Test synthesize() with a mock gTTS to verify output structure."""

    def setUp(self):
        # Create mock gTTS class
        self.mock_gtts = MagicMock()
        self.mock_instance = MagicMock()

        def write_bytes(fp):
            fp.write(b"fake_mp3_audio_data_here_for_testing")
        self.mock_instance.write_to_fp.side_effect = write_bytes
        self.mock_gtts.return_value = self.mock_instance

        # Inject into the engine
        TTSVoiceoverEngine.gTTS = self.mock_gtts

    def test_synthesize_output_structure(self):
        """Verify output structure when gTTS succeeds."""
        result = TTSVoiceoverEngine.synthesize(
            "Hello world, this is a test.",
            voice="narrator",
            speed=1.0,
            lang="en",
        )

        self.assertNotIn("error", result, f"Got error: {result.get('error', '')}")
        self.assertIn("audio_base64", result)
        self.assertIn("audio_bytes", result)
        self.assertIn("duration_sec", result)
        self.assertIn("filename", result)
        self.assertIn("parameters", result)

        params = result["parameters"]
        self.assertEqual(params["voice"], "narrator")
        self.assertEqual(params["lang"], "en")
        self.assertEqual(params["speed_multiplier"], 1.0)
        self.assertGreater(result["audio_bytes"], 0)

        # Verify gTTS was called correctly
        self.mock_gtts.assert_called_once()
        call_kwargs = self.mock_gtts.call_args[1]
        self.assertEqual(call_kwargs["text"], "Hello world, this is a test.")
        self.assertEqual(call_kwargs["lang"], "en")
        self.assertEqual(call_kwargs["slow"], False)

    def test_all_voice_presets_call_correct_tld(self):
        """Verify each voice preset uses the correct TLD."""
        for voice_name, preset in TTSVoiceoverEngine.VOICE_PRESETS.items():
            self.mock_gtts.reset_mock()
            self.mock_gtts.return_value = self.mock_instance

            result = TTSVoiceoverEngine.synthesize("Test", voice=voice_name)
            self.assertNotIn("error", result, f"Voice '{voice_name}' failed")

            call_kwargs = self.mock_gtts.call_args[1]
            self.assertEqual(
                call_kwargs["tld"], preset["tld"],
                f"Voice '{voice_name}': expected TLD '{preset['tld']}', got '{call_kwargs.get('tld')}'",
            )

    def test_soft_voice_uses_slow(self):
        """Soft voice preset should use slow=True."""
        TTSVoiceoverEngine.synthesize("Test", voice="soft")
        call_kwargs = self.mock_gtts.call_args[1]
        self.assertTrue(call_kwargs["slow"])

    def test_high_speed_disables_slow(self):
        """Speed > 1.1 should force slow=False."""
        TTSVoiceoverEngine.synthesize("Test", voice="soft", speed=1.5)
        call_kwargs = self.mock_gtts.call_args[1]
        self.assertFalse(call_kwargs["slow"])


class TestPresetCompleteness(unittest.TestCase):
    """Verify all voice presets have required fields."""

    def test_all_presets_have_required_fields(self):
        for name, preset in TTSVoiceoverEngine.VOICE_PRESETS.items():
            for field in ["tld", "lang", "slow", "description"]:
                self.assertIn(field, preset, f"Preset '{name}' missing {field}")
            self.assertIsInstance(preset["slow"], bool, f"Preset '{name}' slow not bool")

    def test_all_tlds_are_valid(self):
        valid_tlds = {"com", "co.uk", "com.au", "co.in"}
        for name, preset in TTSVoiceoverEngine.VOICE_PRESETS.items():
            self.assertIn(preset["tld"], valid_tlds,
                          f"Preset '{name}' has unknown tld '{preset['tld']}'")


if __name__ == "__main__":
    unittest.main()
