"""
Aesthetic Music Tagger — Apify Actor
=======================================
Analyzes music files (MP3, FLAC, WAV, OGG) and returns aesthetic/mood/energy tags.

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's 
factory pipelines, brand strategy, or proprietary algorithms. It uses only 
librosa for audio analysis and returns generic descriptive tags.

Usage:
    Input:  {"fileUrl": "https://example.com/track.mp3"}
    Output: {"filename": "track.mp3", "tags": [...], "analysis": {...}}
"""

import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from apify import Actor
import librosa
import numpy as np


class AudioAnalyzer:
    """Lightweight audio analysis for aesthetic/mood tagging."""

    MOOD_ENERGY_THRESHOLDS = {
        'low_energy': (0.0, 0.35),
        'moderate_energy': (0.35, 0.65),
        'high_energy': (0.65, 1.0),
    }

    ACOUSTIC_THRESHOLD = 0.3  # spectral_centroid < threshold = acoustic/warm
    BRIGHT_THRESHOLD = 0.65   # spectral_centroid > threshold = bright

    @staticmethod
    def tag_energy(rms_energy: float) -> str:
        """Classify track energy level."""
        for tag, (low, high) in AudioAnalyzer.MOOD_ENERGY_THRESHOLDS.items():
            if low <= rms_energy < high:
                return tag
        return 'moderate_energy'

    @staticmethod
    def tag_mood(spectral_centroid: float, spectral_rolloff: float) -> list:
        """Derive mood tags from spectral features."""
        moods = []
        if spectral_centroid < AudioAnalyzer.ACOUSTIC_THRESHOLD:
            moods.extend(['warm', 'soft', 'mellow'])
        else:
            moods.append('bright')

        if spectral_rolloff > 0.85:
            moods.append('airy')
        elif spectral_rolloff < 0.4:
            moods.append('dark')

        return moods

    @staticmethod
    def tag_danceability(tempogram: np.ndarray) -> str:
        """Estimate danceability based on tempogram stability."""
        if tempogram is None or len(tempogram) == 0:
            return 'unknown'

        std_val = float(np.std(tempogram[0]))
        if std_val < 15:
            return 'steady_rhythm'
        elif std_val < 30:
            return 'moderate_variation'
        else:
            return 'complex_rhythm'

    @staticmethod
    def analyze(file_path: str) -> dict:
        """Full analysis pipeline for a single audio file."""
        try:
            y, sr = librosa.load(file_path, sr=22050, mono=True, duration=120)
        except Exception as e:
            return {'error': f'Could not load audio: {str(e)}'}

        if len(y) == 0:
            return {'error': 'Empty audio file'}

        # Duration
        duration_sec = float(len(y) / sr)

        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        rms_normalized = float(np.clip(np.mean(rms) * 10, 0, 1))

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_normalized = float(np.minimum(np.mean(spectral_centroids) / sr, 1.0))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        rolloff_normalized = float(np.mean(spectral_rolloff) / sr)

        # Spectral contrast (brightness vs darkness)
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = float(np.mean(contrast[1])) if contrast.shape[0] > 1 else 0.0

        # Tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo) if tempo else 0.0

        # Tempogram
        try:
            tempogram = librosa.feature.tempogram(y=y, sr=sr)
        except Exception:
            tempogram = None

        # Zero crossing rate (texture proxy)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        # Spectral flatness (noise level)
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        flatness_mean = float(np.mean(flatness))

        # Build tags
        energy_tag = AudioAnalyzer.tag_energy(rms_normalized)
        mood_tags = AudioAnalyzer.tag_mood(centroid_normalized, rolloff_normalized)
        rhythm_tag = AudioAnalyzer.tag_danceability(tempogram)

        # Build BPM range tag
        if bpm < 60:
            bpm_tag = 'very_slow'
        elif bpm < 90:
            bpm_tag = 'slow'
        elif bpm < 120:
            bpm_tag = 'moderate'
        elif bpm < 150:
            bpm_tag = 'upbeat'
        else:
            bpm_tag = 'fast'

        # Texture tag
        if flatness_mean > 0.7:
            texture_tag = 'noisy_texture'
        elif flatness_mean < 0.3:
            texture_tag = 'pure_tone_texture'
        else:
            texture_tag = 'mixed_texture'

        tags = [energy_tag] + mood_tags + [rhythm_tag, bpm_tag, texture_tag]
        tags = list(set(tags))  # deduplicate

        # Build summary
        analysis = {
            'duration_sec': round(duration_sec, 1),
            'bpm': round(bpm, 1),
            'rms_energy': round(rms_normalized, 3),
            'spectral_centroid': round(centroid_normalized, 3),
            'spectral_rolloff': round(rolloff_normalized, 3),
            'spectral_contrast': round(contrast_mean, 3),
            'zero_crossing_rate': round(zcr_mean, 3),
            'spectral_flatness': round(flatness_mean, 3),
        }

        return {
            'tags': tags,
            'analysis': analysis,
        }


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        
        file_url = actor_input.get('fileUrl', '')
        file_path = actor_input.get('filePath', '')

        if not file_url and not file_path:
            raise ValueError('Either fileUrl or filePath must be provided')

        temp_file = None
        try:
            if file_url:
                # Download remote file to temp
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.audio')
                file_path = temp_file.name
                urllib.request.urlretrieve(file_url, file_path)

            if not os.path.exists(file_path):
                raise FileNotFoundError(f'File not found: {file_path}')

            # Analyze
            result = AudioAnalyzer.analyze(file_path)
            
            if 'error' in result:
                raise RuntimeError(result['error'])

            result['filename'] = os.path.basename(file_url) if file_url else os.path.basename(file_path)
            result['input_md5'] = actor_input.get('fileUrl', actor_input.get('filePath', '')).split('/')[-1]

            # Push result
            await Actor.push_data(result)
            Actor.log.info(f"Analysis complete: {result['filename']} — {len(result['tags'])} tags")

        finally:
            if temp_file:
                os.unlink(temp_file.name)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
