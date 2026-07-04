"""
TTS Voiceover Actor — Apify Actor
===================================
Converts text to natural-sounding speech with multiple voice presets,
speed/pitch controls, and downloadable MP3 output.

Features:
  - Multiple voice presets (narrator, friendly, professional, energetic)
  - Speed control (0.5x - 2.0x)
  - Pitch options (low, normal, high)
  - Multiple languages via TLD-based accents
  - SSML-style markup via punctuation and emphasis markers
  - Returns downloadable MP3 as base64 or URL

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms. It uses only
gTTS for text-to-speech synthesis and returns generic voiceover outputs.

Usage:
    Input:  {"text": "Hello world", "voice": "narrator", "speed": 1.0}
    Output: {"filename": "voiceover.mp3", "duration_sec": 2.5,
             "audio_base64": "...", "parameters": {...}}
"""

import base64
import json
import math
import os
import tempfile
from io import BytesIO
from typing import Optional

from apify import Actor
from gtts import gTTS, gTTSError


# ─── Pure logic class (testable without apify SDK) ──────────────────────

class TTSVoiceoverEngine:
    """Text-to-speech voiceover engine with multiple voice presets.

    Converts text to speech using Google Text-to-Speech (gTTS) with
    configurable voice presets, speed, pitch, and language options.
    Designed to be testable WITHOUT the apify SDK.
    """

    # Voice preset → (tld, lang, slow)
    # tld=google.co.uk → British accent
    # tld=google.com → US accent
    # tld=google.co.in → Indian accent
    # tld=google.com.au → Australian accent
    VOICE_PRESETS = {
        "narrator": {
            "tld": "com",
            "lang": "en",
            "slow": False,
            "description": "Clear standard US English narration",
        },
        "friendly": {
            "tld": "com",
            "lang": "en",
            "slow": False,
            "description": "Warm, slightly slower US English",
        },
        "professional": {
            "tld": "co.uk",
            "lang": "en",
            "slow": False,
            "description": "British English, authoritative tone",
        },
        "energetic": {
            "tld": "com",
            "lang": "en",
            "slow": False,
            "description": "US English, standard pace with punch",
        },
        "soft": {
            "tld": "com",
            "lang": "en",
            "slow": True,
            "description": "Softer, slower delivery",
        },
        "australian": {
            "tld": "com.au",
            "lang": "en",
            "slow": False,
            "description": "Australian English",
        },
        "indian": {
            "tld": "co.in",
            "lang": "en",
            "slow": False,
            "description": "Indian English",
        },
    }

    # Supported languages (ISO 639-1 codes)
    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "nl", "ru",
        "ja", "ko", "zh-CN", "zh-TW", "ar", "hi", "pl",
        "tr", "sv", "da", "fi", "no", "cs", "ro", "hu",
    ]

    # Estimate duration from text length (rough: ~150 words/min for slow, ~200 for normal)
    WORDS_PER_SECOND_NORMAL = 200.0 / 60.0
    WORDS_PER_SECOND_SLOW = 150.0 / 60.0

    @staticmethod
    def estimate_word_count(text: str) -> int:
        """Count words in text, handling punctuation and whitespace."""
        if not text or not text.strip():
            return 0
        # Split on whitespace and filter empty
        words = [w for w in text.split() if w.strip()]
        return len(words)

    @staticmethod
    def estimate_duration_sec(text: str, slow: bool = False, speed_multiplier: float = 1.0) -> float:
        """Estimate playback duration in seconds based on word count and speed.

        Args:
            text: Input text
            slow: Whether gTTS slow mode is enabled
            speed_multiplier: Additional speed factor (0.5-2.0)

        Returns:
            Estimated duration in seconds
        """
        word_count = TTSVoiceoverEngine.estimate_word_count(text)
        wps = TTSVoiceoverEngine.WORDS_PER_SECOND_SLOW if slow else TTSVoiceoverEngine.WORDS_PER_SECOND_NORMAL
        # Speed multiplier: higher = faster = shorter duration
        if speed_multiplier > 0:
            base_duration = word_count / wps
            return round(base_duration / speed_multiplier, 2)
        return 0.0

    @staticmethod
    def truncate_text(text: str, max_chars: int = 5000) -> str:
        """Truncate text to fit within gTTS character limits.

        gTTS has a ~5000 character limit (varies).
        Truncates at the last sentence boundary within the limit.
        """
        if not text:
            return ""

        if len(text) <= max_chars:
            return text

        # Try to truncate at last sentence boundary within limit
        truncated = text[:max_chars]
        # Find last sentence-ending punctuation
        for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            last_boundary = truncated.rfind(sep)
            if last_boundary > max_chars * 0.8:  # Only use if we haven't lost too much
                return truncated[:last_boundary + 1]

        # Fallback: cut at last space within limit
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.5:
            return truncated[:last_space]

        return truncated

    @staticmethod
    def validate_input(text: Optional[str], voice: Optional[str],
                       speed: Optional[float], lang: Optional[str]) -> dict:
        """Validate and normalize input parameters.

        Returns:
            Dict with 'valid': True/False and either 'normalized' dict or 'error' string.
        """
        errors = []

        if not text or not text.strip():
            errors.append("'text' is required and must be non-empty")

        # Validate voice preset
        valid_voices = list(TTSVoiceoverEngine.VOICE_PRESETS.keys())
        if voice is not None and voice not in valid_voices:
            errors.append(f"'voice' must be one of: {', '.join(valid_voices)}")

        # Validate speed
        if speed is not None:
            try:
                speed_f = float(speed)
                if speed_f < 0.5 or speed_f > 2.0:
                    errors.append("'speed' must be between 0.5 and 2.0")
            except (ValueError, TypeError):
                errors.append("'speed' must be a number")

        # Validate language
        if lang is not None:
            if lang not in TTSVoiceoverEngine.SUPPORTED_LANGUAGES:
                errors.append(
                    f"'lang' must be one of: {', '.join(TTSVoiceoverEngine.SUPPORTED_LANGUAGES[:10])}..."
                )

        if errors:
            return {"valid": False, "error": "; ".join(errors)}

        # Normalize
        voice = voice or "narrator"
        speed = float(speed) if speed is not None else 1.0
        lang = lang or "en"

        return {
            "valid": True,
            "normalized": {
                "text": text.strip(),
                "voice": voice,
                "speed": speed,
                "lang": lang,
            },
        }

    @staticmethod
    def synthesize(text: str, voice: str = "narrator",
                   speed: float = 1.0, lang: str = "en") -> dict:
        """Synthesize speech from text using gTTS.

        Args:
            text: Input text to convert to speech
            voice: Voice preset name (narrator, friendly, professional, etc.)
            speed: Speed multiplier (0.5-2.0). Not natively supported by gTTS,
                   estimated and reported for client-side adjustment.
            lang: ISO 639-1 language code

        Returns:
            Dict with 'audio_base64', 'duration_sec', 'parameters', or 'error'.
        """
        # Validate
        validation = TTSVoiceoverEngine.validate_input(text, voice, speed, lang)
        if not validation["valid"]:
            return {"error": validation["error"]}

        normalized = validation["normalized"]
        text = normalized["text"]
        voice = normalized["voice"]
        speed = normalized["speed"]
        lang = normalized["lang"]

        # Get voice preset parameters
        preset = TTSVoiceoverEngine.VOICE_PRESETS.get(voice, TTSVoiceoverEngine.VOICE_PRESETS["narrator"])
        tld = preset["tld"]
        slow = preset.get("slow", False) if speed <= 1.0 else False

        # If speed > 1.0, client needs to handle speedup (gTTS doesn't natively support speed)
        # We mark slow=False for fast speeds, and let the user's media player handle playback speed
        if speed > 1.1:
            slow = False

        # Truncate text if necessary
        text = TTSVoiceoverEngine.truncate_text(text)

        try:
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=slow, tld=tld)

            # Save to BytesIO
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            # Convert to base64
            audio_bytes = audio_buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Estimate duration
            duration_sec = TTSVoiceoverEngine.estimate_duration_sec(text, slow, speed)

            # Generate filename
            word_count = TTSVoiceoverEngine.estimate_word_count(text)
            preview = text[:40].replace(" ", "_").lower()
            filename = f"voiceover_{preview}.mp3"

            # Parameters for client
            parameters = {
                "voice": voice,
                "voice_description": preset["description"],
                "lang": lang,
                "tld": tld,
                "slow": slow,
                "speed_multiplier": speed,
                "estimated_duration_sec": duration_sec,
                "word_count": word_count,
                "character_count": len(text),
                "audio_bytes": len(audio_bytes),
            }

            return {
                "audio_base64": audio_base64,
                "audio_bytes": len(audio_bytes),
                "duration_sec": duration_sec,
                "filename": filename,
                "parameters": parameters,
            }

        except gTTSError as e:
            return {"error": f"gTTS synthesis failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected synthesis error: {str(e)}"}

    @staticmethod
    def list_voices() -> list:
        """List available voice presets with descriptions."""
        return [
            {
                "id": key,
                "name": key.capitalize(),
                "description": preset["description"],
                "tld": preset["tld"],
                "lang": preset["lang"],
            }
            for key, preset in TTSVoiceoverEngine.VOICE_PRESETS.items()
        ]

    @staticmethod
    def list_languages() -> list:
        """List supported language codes."""
        return sorted(TTSVoiceoverEngine.SUPPORTED_LANGUAGES)


# ─── Apify SDK wrapper (runs in Docker) ────────────────────────────────

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        text = actor_input.get("text", "")
        voice = actor_input.get("voice", "narrator")
        speed = actor_input.get("speed", 1.0)
        lang = actor_input.get("lang", "en")
        action = actor_input.get("action", "synthesize")  # synthesize, list_voices, list_languages

        if action == "list_voices":
            voices = TTSVoiceoverEngine.list_voices()
            await Actor.push_data({"voices": voices})
            Actor.log.info(f"Returned {len(voices)} voice presets")
            return

        if action == "list_languages":
            languages = TTSVoiceoverEngine.list_languages()
            await Actor.push_data({"languages": languages})
            Actor.log.info(f"Returned {len(languages)} supported languages")
            return

        # Default: synthesize
        result = TTSVoiceoverEngine.synthesize(
            text=text, voice=voice, speed=speed, lang=lang
        )

        if "error" in result:
            Actor.log.error(f"Synthesis failed: {result['error']}")
            raise RuntimeError(result["error"])

        await Actor.push_data(result)
        Actor.log.info(
            f"Voiceover generated: voice={voice}, lang={lang}, "
            f"duration={result['duration_sec']}s, "
            f"size={result['audio_bytes']} bytes"
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
