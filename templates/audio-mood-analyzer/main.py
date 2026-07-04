"""
Audio Mood/Emotion Analyzer — Apify Actor
===========================================
Analyzes audio files and returns a comprehensive mood/emotion profile:
- Overall mood classification (happy, sad, tense, calm, etc.)
- Energy curve over the track
- Arousal-valence emotional mapping
- Segment-level mood tags (e.g., 0-30s: calm, 30-60s: building)
- Timbre/texture description

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms. It uses only
librosa for audio analysis and returns generic descriptive tags.

Usage:
    Input:  {"fileUrl": "https://example.com/track.mp3"}
    Output: {"filename": "track.mp3", "moods": [...], "segments": [...], "analysis": {...}}
"""

import json
import math
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from apify import Actor
import librosa
import numpy as np


class MoodAnalyzer:
    """Audio mood and emotion analysis engine.

    Analyzes spectral, rhythmic, and temporal features to derive
    mood tags, energy curves, and emotion vectors (arousal-valence).
    Designed to be testable WITHOUT the apify SDK.
    """

    # Arousal feature thresholds (0-1 scale)
    AROUSAL_ENERGY_LOW = 0.3
    AROUSAL_ENERGY_HIGH = 0.6
    AROUSAL_BPM_LOW = 80
    AROUSAL_BPM_HIGH = 130
    AROUSAL_ZCR_LOW = 0.05
    AROUSAL_ZCR_HIGH = 0.12

    # Valence feature thresholds (0-1 scale)
    VALENCE_CENTROID_LOW = 0.35  # below = warm/dark (lower valence)
    VALENCE_CENTROID_HIGH = 0.55  # above = bright (higher valence)
    VALENCE_FLATNESS_LOW = 0.3
    VALENCE_FLATNESS_HIGH = 0.6
    VALENCE_CONTRAST_LOW = 20

    # Mood quadrant thresholds (arousal × valence)
    QUADRANT_HAPPY = {"arousal_min": 0.5, "valence_min": 0.6}
    QUADRANT_CALM = {"arousal_max": 0.45, "valence_min": 0.55}
    QUADRANT_TENSE = {"arousal_min": 0.55, "valence_max": 0.46}
    QUADRANT_SAD = {"arousal_max": 0.4, "valence_max": 0.4}

    # Segment duration in seconds
    SEGMENT_DURATION = 15.0

    @staticmethod
    def compute_arousal(rms_energy: float, bpm: float, zcr_mean: float) -> float:
        """Compute arousal (energy/intensity) score from audio features.

        Arousal: 0.0 (very calm/sleepy) to 1.0 (very intense/excited).
        """
        energy_score = min(rms_energy / MoodAnalyzer.AROUSAL_ENERGY_HIGH, 1.0)
        bpm_score = min(max((bpm - MoodAnalyzer.AROUSAL_BPM_LOW) /
                           (MoodAnalyzer.AROUSAL_BPM_HIGH - MoodAnalyzer.AROUSAL_BPM_LOW), 0.0), 1.0)
        zcr_score = min(max((zcr_mean - MoodAnalyzer.AROUSAL_ZCR_LOW) /
                          (MoodAnalyzer.AROUSAL_ZCR_HIGH - MoodAnalyzer.AROUSAL_ZCR_LOW), 0.0), 1.0)

        arousal = (energy_score * 0.5 + bpm_score * 0.3 + zcr_score * 0.2)
        return float(np.clip(arousal, 0.0, 1.0))

    @staticmethod
    def compute_valence(spectral_centroid: float, spectral_flatness: float,
                        spectral_contrast: float) -> float:
        """Compute valence (positivity/happiness) score from spectral features.

        Valence: 0.0 (very negative/sad) to 1.0 (very positive/happy).
        """
        # Bright/clear sounds → higher valence
        centroid_score = min(max((spectral_centroid - MoodAnalyzer.VALENCE_CENTROID_LOW) /
                               (MoodAnalyzer.VALENCE_CENTROID_HIGH - MoodAnalyzer.VALENCE_CENTROID_LOW), 0.0), 1.0)

        # Low flatness (pure tones) → structured → higher valence
        flatness_score = 1.0 - min(spectral_flatness / MoodAnalyzer.VALENCE_FLATNESS_HIGH, 1.0)

        # High contrast (clear harmonic vs noise bands) → higher valence
        contrast_score = min(spectral_contrast / MoodAnalyzer.VALENCE_CONTRAST_LOW, 1.0)

        valence = (centroid_score * 0.4 + flatness_score * 0.3 + contrast_score * 0.3)
        return float(np.clip(valence, 0.0, 1.0))

    @staticmethod
    def classify_mood(arousal: float, valence: float) -> list:
        """Classify mood based on arousal-valence coordinates.

        Returns a list of mood tags sorted by strength.
        """
        moods = []
        strengths = []

        # Quadrant-based classification
        if arousal >= MoodAnalyzer.QUADRANT_HAPPY["arousal_min"] and valence >= MoodAnalyzer.QUADRANT_HAPPY["valence_min"]:
            moods.append("happy")
            strengths.append(arousal * valence)
        if arousal >= MoodAnalyzer.QUADRANT_TENSE["arousal_min"] and valence <= MoodAnalyzer.QUADRANT_TENSE["valence_max"]:
            moods.append("tense")
            strengths.append(arousal * (1.0 - valence))
        if arousal <= MoodAnalyzer.QUADRANT_CALM["arousal_max"] and valence >= MoodAnalyzer.QUADRANT_CALM["valence_min"]:
            moods.append("calm")
            strengths.append((1.0 - arousal) * valence)
        if arousal <= MoodAnalyzer.QUADRANT_SAD["arousal_max"] and valence <= MoodAnalyzer.QUADRANT_SAD["valence_max"]:
            moods.append("sad")
            strengths.append((1.0 - arousal) * (1.0 - valence))

        # Fine-grained refinements
        if valence > 0.8 and arousal > 0.3:
            moods.append("joyful")
            strengths.append(valence * 0.8)
        if valence > 0.7 and arousal < 0.3:
            moods.append("peaceful")
            strengths.append(valence * 0.7)
        if valence < 0.3 and arousal > 0.6:
            moods.append("angry")
            strengths.append((1.0 - valence) * arousal)
        if valence < 0.4 and arousal > 0.7:
            moods.append("agitated")
            strengths.append((1.0 - valence) * arousal * 0.9)
        if 0.35 < valence < 0.65 and arousal < 0.4:
            moods.append("melancholic")
            strengths.append(0.5)
        if valence < 0.35 and arousal < 0.3:
            moods.append("gloomy")
            strengths.append(0.6)
        if 0.5 < arousal < 0.7 and 0.45 < valence < 0.65:
            moods.append("anticipation")
            strengths.append(arousal * valence)

        # Deduplicate by highest strength
        seen = set()
        unique_moods = []
        unique_strengths = []
        for m, s in zip(moods, strengths):
            if m not in seen:
                seen.add(m)
                unique_moods.append(m)
                unique_strengths.append(s)

        # Sort by strength descending
        paired = list(zip(unique_moods, unique_strengths))
        paired.sort(key=lambda x: x[1], reverse=True)

        return [m for m, _ in paired]

    @staticmethod
    def compute_energy_curve(y: np.ndarray, sr: int, num_segments: int = 20) -> list:
        """Compute energy over time as a list of (position_sec, energy) pairs."""
        if len(y) == 0:
            return []

        hop_length = max(len(y) // num_segments, sr // 10)  # at least 100ms per segment
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        duration_sec = len(y) / sr

        # Normalize energy to 0-1
        energy_max = np.max(rms) if np.max(rms) > 0 else 1.0
        energy_normalized = (rms / energy_max).tolist()

        # Generate time positions
        positions_sec = [
            round(i * hop_length / sr, 1)
            for i in range(len(energy_normalized))
            if i * hop_length / sr <= duration_sec
        ]

        return [
            {"time_sec": t, "energy": round(e, 3)}
            for t, e in zip(positions_sec, energy_normalized[:len(positions_sec)])
        ]

    @staticmethod
    def compute_segments(y: np.ndarray, sr: int) -> list:
        """Segment audio into blocks and analyze each block's mood.

        Returns a list of segment dicts with time range, arousal, valence, and mood.
        """
        total_duration = len(y) / sr
        segment_samples = int(MoodAnalyzer.SEGMENT_DURATION * sr)
        overlap = segment_samples // 4  # 25% overlap for smooth transitions

        segments = []
        start_sample = 0
        segment_idx = 0

        while start_sample < len(y):
            end_sample = min(start_sample + segment_samples, len(y))
            segment_audio = y[start_sample:end_sample]
            segment_dur = len(segment_audio) / sr

            if segment_dur < 2.0:  # Skip segments shorter than 2 seconds
                break

            # Analyze this segment
            rms = librosa.feature.rms(y=segment_audio)[0]
            rms_energy = float(np.clip(np.mean(rms) * 10, 0, 1)) if len(rms) > 0 else 0.0

            centroids = librosa.feature.spectral_centroid(y=segment_audio, sr=sr)[0]
            centroid = float(np.minimum(np.mean(centroids) / sr, 1.0)) if len(centroids) > 0 else 0.0

            flatness = librosa.feature.spectral_flatness(y=segment_audio)[0]
            flatness_mean = float(np.mean(flatness)) if len(flatness) > 0 else 0.5

            contrast = librosa.feature.spectral_contrast(y=segment_audio, sr=sr)
            contrast_mean = float(np.mean(contrast[1])) if contrast.shape[0] > 1 else 0.0

            zcr = librosa.feature.zero_crossing_rate(segment_audio)[0]
            zcr_mean = float(np.mean(zcr)) if len(zcr) > 0 else 0.0

            tempo, _ = librosa.beat.beat_track(y=segment_audio, sr=sr)
            bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo) if tempo else 0.0

            # Compute emotion metrics
            arousal = MoodAnalyzer.compute_arousal(rms_energy, bpm, zcr_mean)
            valence = MoodAnalyzer.compute_valence(centroid, flatness_mean, contrast_mean)
            moods = MoodAnalyzer.classify_mood(arousal, valence)

            start_time = round(start_sample / sr, 1)
            end_time = round(end_sample / sr, 1)

            segments.append({
                "start_sec": start_time,
                "end_sec": end_time,
                "duration_sec": round(segment_dur, 1),
                "moods": moods[:3],  # Top 3 moods for this segment
                "arousal": round(arousal, 3),
                "valence": round(valence, 3),
                "energy": round(rms_energy, 3),
                "bpm": round(bpm, 1),
            })

            start_sample += segment_samples - overlap
            segment_idx += 1

            # Cap at 30 segments to avoid huge outputs
            if segment_idx >= 30:
                break

        return segments

    @staticmethod
    def describe_mood_texture(arousal: float, valence: float, energy_curve: list) -> str:
        """Generate a short text description of the overall mood texture."""
        if arousal < 0.25 and valence < 0.3:
            return "deeply melancholic and subdued"
        elif arousal < 0.3 and valence > 0.7:
            return "serene and peaceful"
        elif arousal < 0.35 and valence < 0.5:
            return "contemplative with a hint of sadness"
        elif arousal < 0.3:
            return "gentle and restrained"
        elif arousal > 0.8 and valence > 0.7:
            return "exuberant and high-energy"
        elif arousal > 0.8 and valence < 0.3:
            return "intense and aggressive"
        elif arousal > 0.7 and valence < 0.45:
            return "driving with an undercurrent of tension"
        elif arousal > 0.6 and valence > 0.65:
            return "upbeat and lively"
        elif arousal > 0.5 and valence < 0.4:
            return "restless and anxious"
        elif arousal > 0.4 and valence > 0.6:
            return "optimistic and warm"
        elif 0.3 < arousal < 0.6 and 0.35 < valence < 0.6:
            return "balanced and reflective"

        # Fallback
        return "moderate energy with mixed emotional character"

    @staticmethod
    def analyze(file_path: str) -> dict:
        """Full mood analysis pipeline for a single audio file.

        Args:
            file_path: Path to the audio file.

        Returns:
            Dict with moods, arousal-valence, energy_curve, segments, and analysis.
            Returns {'error': ...} on failure.
        """
        try:
            y, sr = librosa.load(file_path, sr=22050, mono=True, duration=180)
        except Exception as e:
            return {"error": f"Could not load audio: {str(e)}"}

        if len(y) == 0:
            return {"error": "Empty audio file"}

        duration_sec = float(len(y) / sr)

        # ---- Global features ----
        rms = librosa.feature.rms(y=y)[0]
        rms_energy = float(np.clip(np.mean(rms) * 10, 0, 1))

        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid = float(np.minimum(np.mean(spectral_centroids) / sr, 1.0))

        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        rolloff = float(np.mean(spectral_rolloff) / sr)

        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = float(np.mean(contrast[1])) if contrast.shape[0] > 1 else 0.0

        flatness = librosa.feature.spectral_flatness(y=y)[0]
        flatness_mean = float(np.mean(flatness))

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo) if tempo else 0.0

        # ---- Emotion computation ----
        arousal = MoodAnalyzer.compute_arousal(rms_energy, bpm, zcr_mean)
        valence = MoodAnalyzer.compute_valence(centroid, flatness_mean, contrast_mean)
        moods = MoodAnalyzer.classify_mood(arousal, valence)

        # ---- Energy curve ----
        energy_curve = MoodAnalyzer.compute_energy_curve(y, sr, num_segments=20)

        # ---- Segments ----
        segments = MoodAnalyzer.compute_segments(y, sr)

        # ---- Texture description ----
        texture_description = MoodAnalyzer.describe_mood_texture(arousal, valence, energy_curve)

        # ---- BPM classification ----
        if bpm < 60:
            tempo_tag = "very_slow"
        elif bpm < 90:
            tempo_tag = "slow"
        elif bpm < 120:
            tempo_tag = "moderate"
        elif bpm < 150:
            tempo_tag = "upbeat"
        else:
            tempo_tag = "fast"

        # ---- Build result ----
        analysis = {
            "duration_sec": round(duration_sec, 1),
            "bpm": round(bpm, 1),
            "tempo_tag": tempo_tag,
            "arousal": round(arousal, 4),
            "valence": round(valence, 4),
            "rms_energy": round(rms_energy, 4),
            "spectral_centroid": round(centroid, 4),
            "spectral_rolloff": round(rolloff, 4),
            "spectral_contrast": round(contrast_mean, 4),
            "spectral_flatness": round(flatness_mean, 4),
            "zero_crossing_rate": round(zcr_mean, 4),
        }

        return {
            "moods": moods[:5],  # Top 5 moods
            "arousal_valence": {
                "arousal": round(arousal, 4),
                "valence": round(valence, 4),
                "quadrant": "high_arousal_high_valence" if arousal >= 0.5 and valence >= 0.5 else
                            "high_arousal_low_valence" if arousal >= 0.5 else
                            "low_arousal_high_valence" if valence >= 0.5 else
                            "low_arousal_low_valence",
            },
            "analysis": analysis,
            "energy_curve": energy_curve,
            "segments": segments,
            "texture_description": texture_description,
        }


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        file_url = actor_input.get("fileUrl", "")
        file_path = actor_input.get("filePath", "")

        if not file_url and not file_path:
            raise ValueError("Either fileUrl or filePath must be provided")

        temp_file = None
        try:
            if file_url:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".audio")
                file_path = temp_file.name
                urllib.request.urlretrieve(file_url, file_path)

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            result = MoodAnalyzer.analyze(file_path)

            if "error" in result:
                raise RuntimeError(result["error"])

            result["filename"] = os.path.basename(file_url) if file_url else os.path.basename(file_path)

            await Actor.push_data(result)
            Actor.log.info(
                f"Mood analysis complete: {result['filename']} — "
                f"moods={result['moods']}, "
                f"arousal={result['arousal_valence']['arousal']:.3f}, "
                f"valence={result['arousal_valence']['valence']:.3f}"
            )

        finally:
            if temp_file:
                os.unlink(temp_file.name)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
