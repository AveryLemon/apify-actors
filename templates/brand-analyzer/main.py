"""
Cross-Modal Brand Consistency Analyzer — Apify Actor
=====================================================
Analyzes a brand's visual AND audio content, producing a unified
brand consistency report with cross-modal alignment scoring.

Outputs:
- visual_identity:   Dominant colors, style classification, mood palette, aesthetic scores
- sonic_identity:    Mood profile, energy signature, genre affinity, tempo range
- cross_modal:       Alignment scores across visual+sonic dimensions
- brand_consistency: Overall consistency score (0-100), visual variance, sonic variance
- recommendations:   Actionable steps to improve cross-modal brand alignment

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms. It uses only
Pillow and numpy (image analysis) and librosa (audio analysis) — all public
libraries — and returns generic analytical judgments.

Usage:
    Input:  {"imageUrls": [...], "audioUrls": [...]}
    Output: {"visual_identity": {...}, "sonic_identity": {...}, 
             "cross_modal": {...}, "brand_consistency": {...}, "recommendations": [...]}
"""

import json
import math
import os
import tempfile
import urllib.request
from collections import Counter
from typing import Optional

from apify import Actor
import numpy as np


# ═══════════════════════════════════════════════════════════════
# IMAGE ANALYSIS — Pillow-based aesthetic/style analysis
# ═══════════════════════════════════════════════════════════════

class VisualAnalyzer:
    """Analyze visual brand assets for aesthetic/color/style consistency.

    Pure Pillow+numpy — no ML models. Designed to be testable WITHOUT the apify SDK.
    Combines patterns from the Aesthetic Style Analyzer and Album Art Analyzer actors.
    """

    # Style archetypes with visual signatures
    STYLE_PROFILES = {
        'minimalist': {
            'brightness_level': 'bright',
            'color_diversity': 'low_diversity',
            'contrast': ['low_contrast', 'moderate_contrast'],
            'color_temperatures': ['neutral'],
        },
        'grunge': {
            'brightness_level': 'dark',
            'color_diversity': 'moderate_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['warm', 'neutral'],
        },
        'vintage': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'moderate_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['warm'],
        },
        'clean_modern': {
            'brightness_level': 'bright',
            'color_diversity': 'low_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'dark_moody': {
            'brightness_level': 'dark',
            'color_diversity': 'low_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'nature_organic': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'high_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['warm'],
        },
        'vibrant_colorful': {
            'brightness_level': 'bright',
            'color_diversity': 'high_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['warm', 'cool'],
        },
        'monochrome': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'low_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['neutral'],
        },
        'noir': {
            'brightness_level': 'dark',
            'color_diversity': 'low_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'pastel': {
            'brightness_level': 'bright',
            'color_diversity': 'moderate_diversity',
            'contrast': ['low_contrast'],
            'color_temperatures': ['cool', 'warm'],
        },
    }

    # Color-to-mood mappings
    COLOR_MOODS = {
        'red': ['passionate', 'intense', 'energetic', 'aggressive'],
        'orange': ['warm', 'playful', 'inviting', 'creative'],
        'yellow': ['optimistic', 'cheerful', 'bright', 'attention-seeking'],
        'green': ['calm', 'natural', 'fresh', 'balanced'],
        'blue': ['serene', 'melancholic', 'trustworthy', 'cold'],
        'purple': ['mysterious', 'regal', 'creative', 'spiritual'],
        'pink': ['romantic', 'sweet', 'tender', 'nostalgic'],
        'brown': ['earthy', 'warm', 'vintage', 'simple'],
        'gray': ['neutral', 'subdued', 'sophisticated', 'moody'],
        'black': ['bold', 'dramatic', 'minimalist', 'powerful'],
        'white': ['clean', 'pure', 'minimalist', 'ethereal'],
    }

    @staticmethod
    def classify_color(rgb):
        """Map an RGB value to a named color."""
        r, g, b = rgb
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        chroma = max_val - min_val

        if chroma < 30:
            if max_val < 50:
                return 'black'
            elif max_val > 200:
                return 'white'
            else:
                return 'gray'

        if max_val == 0:
            return 'black'

        rn = r / max_val
        gn = g / max_val
        bn = b / max_val

        if rn > 0.8 and gn > 0.8 and bn < 0.3:
            return 'yellow'
        elif rn > 0.8 and gn < 0.4 and bn < 0.4:
            return 'red'
        elif rn > 0.8 and gn > 0.5 and bn > 0.6:
            return 'pink'
        elif rn > 0.8 and gn > 0.4 and bn < 0.3:
            return 'orange'
        elif gn > 0.8 and rn < 0.6 and bn < 0.6:
            return 'green'
        elif bn > 0.8 and rn < 0.6 and gn < 0.6:
            return 'blue'
        elif rn > 0.6 and gn > 0.2 and bn > 0.6:
            return 'purple'
        elif rn > 0.5 and gn > 0.2 and bn < 0.4 and rn > gn > bn:
            return 'brown'
        else:
            named = {
                'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
                'yellow': (255, 255, 0), 'purple': (128, 0, 128),
                'orange': (255, 165, 0), 'pink': (255, 192, 203),
            }
            distances = {name: sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, target))
                        for name, target in named.items()}
            return min(distances, key=lambda k: distances[k])

    @staticmethod
    def get_dominant_colors(img_array, n=5):
        """Extract dominant colors via simple quantization."""
        flat = img_array.reshape(-1, 3)
        if len(flat) > 20000:
            indices = np.random.choice(len(flat), 20000, replace=False)
            flat = flat[indices]

        quantized = (flat // 32) * 32 + 16
        quantized = np.clip(quantized, 0, 255)
        color_tuples = [tuple(c) for c in quantized]
        counter = Counter(color_tuples)
        dominant = counter.most_common(n)
        return [(list(rgb), count) for rgb, count in dominant]

    @staticmethod
    def assess_color_temperature(img_array):
        """Determine if the image is warm-toned, cool-toned, or neutral."""
        r_channel = img_array[:, :, 0].astype(float)
        b_channel = img_array[:, :, 2].astype(float)
        ratio = np.mean(r_channel) / max(np.mean(b_channel), 1.0)
        if ratio > 1.15:
            return 'warm'
        elif ratio < 0.85:
            return 'cool'
        else:
            return 'neutral'

    @staticmethod
    def analyze_harmony_from_colors(colors):
        """Analyze color harmony type from dominant colors."""
        if len(colors) < 2:
            return 'monochrome'
        color_names = [VisualAnalyzer.classify_color(c) for c in colors[:5]]
        for c1, c2 in [('red', 'green'), ('blue', 'orange'), ('purple', 'yellow'),
                        ('pink', 'teal'), ('teal', 'pink')]:
            if c1 in color_names and c2 in color_names:
                return 'complementary'
        warm = {'red', 'orange', 'yellow', 'pink', 'brown'}
        cool = {'blue', 'green', 'purple'}
        warm_count = sum(1 for c in color_names if c in warm)
        cool_count = sum(1 for c in color_names if c in cool)
        if warm_count >= 2:
            return 'analogous_warm'
        elif cool_count >= 2:
            return 'analogous_cool'
        if len(set(color_names)) >= 3:
            return 'triadic'
        return 'mixed'

    @staticmethod
    def analyze_brightness(img_array):
        """Analyze overall brightness and contrast."""
        gray = np.mean(img_array, axis=2)
        mean_brightness = float(np.mean(gray))
        std_brightness = float(np.std(gray))

        if mean_brightness < 60:
            brightness = 'dark'
        elif mean_brightness < 140:
            brightness = 'mid_tone'
        else:
            brightness = 'bright'

        if std_brightness < 40:
            contrast = 'low_contrast'
        elif std_brightness < 70:
            contrast = 'moderate_contrast'
        else:
            contrast = 'high_contrast'

        return {
            'brightness_level': brightness,
            'contrast_level': contrast,
            'mean_brightness': round(mean_brightness, 1),
            'brightness_std': round(std_brightness, 1),
        }

    @staticmethod
    def analyze_color_variance(img_array):
        """Analyze color diversity."""
        flat = img_array.reshape(-1, 3)
        if len(flat) > 10000:
            indices = np.random.choice(len(flat), 10000, replace=False)
            flat = flat[indices]
        std_per_channel = np.std(flat, axis=0)
        mean_std = float(np.mean(std_per_channel))
        if mean_std < 30:
            return 'low_diversity'
        elif mean_std < 55:
            return 'moderate_diversity'
        else:
            return 'high_diversity'

    @classmethod
    def analyze_image(cls, img_array):
        """Full visual analysis of a single image.

        Returns a dict with aesthetic score, dominant colors, style, etc.
        """
        dominant = cls.get_dominant_colors(img_array)
        color_names = [cls.classify_color(c) for c, _ in dominant]

        temp = cls.assess_color_temperature(img_array)
        brightness = cls.analyze_brightness(img_array)
        diversity = cls.analyze_color_variance(img_array)
        harmony = cls.analyze_harmony_from_colors([c for c, _ in dominant])

        # Style classification
        candidates = []
        for style, profile in cls.STYLE_PROFILES.items():
            score = 0
            total_checks = 0
            if profile['brightness_level'] == brightness['brightness_level']:
                score += 1
            total_checks += 1
            if profile['color_diversity'] == diversity:
                score += 1
            total_checks += 1
            if brightness['contrast_level'] in profile['contrast']:
                score += 1
            total_checks += 1
            temps = profile.get('color_temperatures', ['neutral'])
            if temp in temps:
                score += 1
            total_checks += 1
            confidence = score / max(total_checks, 1)
            if confidence >= 0.5:
                candidates.append((style, round(confidence, 2)))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_styles = candidates[:2]

        # Color mood palette
        color_moods = set()
        for name in color_names[:4]:
            moods = cls.COLOR_MOODS.get(name, [])
            color_moods.update(moods[:2])
        mood_list = list(color_moods)[:5]

        # Harmony score
        harmony_scores = {
            'complementary': 8.5, 'analogous_warm': 7.0, 'analogous_cool': 7.0,
            'triadic': 9.0, 'monochrome': 6.0, 'mixed': 5.0,
        }
        harmony_score = harmony_scores.get(harmony, 5.0)

        # Aesthetic base score from brightness + diversity + harmony
        brightness_map = {'dark': 5, 'mid_tone': 7, 'bright': 8}
        diversity_map = {'low_diversity': 5, 'moderate_diversity': 7, 'high_diversity': 8}
        astro = (brightness_map.get(brightness['brightness_level'], 5) * 0.25 +
                 diversity_map.get(diversity, 5) * 0.25 +
                 harmony_score * 0.5)

        return {
            'dominant_colors': color_names[:4],
            'color_palette': [list(c) for c, _ in dominant[:4]],
            'color_temperature': temp,
            'harmony_type': harmony,
            'harmony_score': round(harmony_score, 1),
            'brightness': brightness['brightness_level'],
            'contrast': brightness['contrast_level'],
            'color_diversity': diversity,
            'style_classification': top_styles,
            'aesthetic_score': round(astro, 1),
            'color_mood_palette': mood_list,
        }


# ═══════════════════════════════════════════════════════════════
# AUDIO ANALYSIS — librosa-based mood/energy analysis
# ═══════════════════════════════════════════════════════════════

class SonicAnalyzer:
    """Analyze audio brand assets for mood/energy/genre consistency.

    Pure librosa — no ML models. Designed to be testable WITHOUT the apify SDK.
    Combines patterns from the Audio Mood Analyzer actor.
    """

    # Mood quadrant thresholds
    QUADRANT_HAPPY = {"arousal_min": 0.5, "valence_min": 0.6}
    QUADRANT_CALM = {"arousal_max": 0.45, "valence_min": 0.55}
    QUADRANT_TENSE = {"arousal_min": 0.55, "valence_max": 0.46}
    QUADRANT_SAD = {"arousal_max": 0.4, "valence_max": 0.4}

    @staticmethod
    def compute_arousal(rms_energy: float, bpm: float, zcr_mean: float) -> float:
        """Compute arousal (energy/intensity) score from audio features.

        Arousal: 0.0 (very calm/sleepy) to 1.0 (very intense/excited).
        """
        energy_score = min(rms_energy / 0.6, 1.0)
        bpm_score = min(max((bpm - 80) / (130 - 80), 0.0), 1.0)
        zcr_score = min(max((zcr_mean - 0.05) / (0.12 - 0.05), 0.0), 1.0)
        arousal = (energy_score * 0.5 + bpm_score * 0.3 + zcr_score * 0.2)
        return float(np.clip(arousal, 0.0, 1.0))

    @staticmethod
    def compute_valence(spectral_centroid_mean: float, spectral_flatness_mean: float,
                        spectral_contrast_mean: float) -> float:
        """Compute valence (positivity/happiness) from spectral features.

        Valence: 0.0 (very negative/sad) to 1.0 (very positive/happy).
        """
        # Normalize spectral centroid (brightness correlates with positivity)
        centroid_score = min(spectral_centroid_mean / 4000.0, 1.0)
        # Higher flatness = more noise-like = less tonal = lower valence
        flatness_score = 1.0 - min(spectral_flatness_mean / 1.0, 0.8)
        # Higher contrast = more defined structure = higher valence
        contrast_score = min(spectral_contrast_mean / 60.0, 1.0)

        valence = (centroid_score * 0.4 + flatness_score * 0.3 + contrast_score * 0.3)
        return float(np.clip(valence, 0.0, 1.0))

    @staticmethod
    def classify_mood_quadrant(arousal: float, valence: float) -> str:
        """Classify the overall mood quadrant."""
        if arousal >= SonicAnalyzer.QUADRANT_HAPPY["arousal_min"] and valence >= SonicAnalyzer.QUADRANT_HAPPY["valence_min"]:
            return "happy/excited"
        elif arousal <= SonicAnalyzer.QUADRANT_CALM["arousal_max"] and valence >= SonicAnalyzer.QUADRANT_CALM["valence_min"]:
            return "calm/peaceful"
        elif arousal >= SonicAnalyzer.QUADRANT_TENSE["arousal_min"] and valence <= SonicAnalyzer.QUADRANT_TENSE["valence_max"]:
            return "tense/angry"
        elif arousal <= SonicAnalyzer.QUADRANT_SAD["arousal_max"] and valence <= SonicAnalyzer.QUADRANT_SAD["valence_max"]:
            return "sad/melancholic"
        else:
            return "neutral/ambiguous"

    @classmethod
    def analyze_audio(cls, audio_path: str) -> dict:
        """Full sonic analysis of a single audio file.

        Returns a dict with mood, energy, tempo, and spectral profile.
        Uses librosa for all feature extraction.
        """
        import librosa

        # Load audio — mix to mono, resample to 22050
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        if len(y) < sr:  # Less than 1 second
            return {
                'error': 'Audio too short (< 1 second)',
                'duration_sec': round(len(y) / sr, 1),
            }

        duration = len(y) / sr

        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))

        # Tempo / BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(np.atleast_1d(tempo)[0]) if np.atleast_1d(tempo)[0] > 0 else 120.0

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(spectral_centroids))

        spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
        flatness_mean = float(np.mean(spectral_flatness))

        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = float(np.mean(spectral_contrast))

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        # Compute arousal and valence
        arousal = cls.compute_arousal(rms_mean, bpm, zcr_mean)
        valence = cls.compute_valence(centroid_mean, flatness_mean, contrast_mean)

        # Energy curve (10 segments)
        n_segments = min(10, max(2, len(rms) // 2))
        seg_len = len(rms) // n_segments
        energy_segments = []
        for i in range(n_segments):
            start_idx = i * seg_len
            end_idx = min((i + 1) * seg_len, len(rms))
            if end_idx <= start_idx:
                seg_energy = 0.0
            else:
                seg_energy = float(np.mean(rms[start_idx:end_idx]))
            energy_segments.append({
                'segment': i,
                'start_sec': round((start_idx * 512) / sr, 1),
                'end_sec': round((end_idx * 512) / sr, 1),
                'energy': round(seg_energy, 4),
            })

        # Energy profile
        energy_values = [s['energy'] for s in energy_segments]
        energy_trend = 'increasing' if float(np.mean(energy_values[-3:])) > float(np.mean(energy_values[:3])) * 1.1 else \
                       'decreasing' if float(np.mean(energy_values[-3:])) < float(np.mean(energy_values[:3])) * 0.9 else \
                       'stable'

        # Mood quadrant
        mood_quadrant = cls.classify_mood_quadrant(arousal, valence)

        # Genre approximation from tempo + spectral profile
        if bpm < 70 and centroid_mean < 2000 and flatness_mean < 0.5:
            genre = 'ambient/drone'
        elif bpm < 70 and centroid_mean < 3000:
            genre = 'slow/ballad'
        elif 70 <= bpm <= 110 and flatness_mean > 0.6:
            genre = 'hiphop/rnb'
        elif 70 <= bpm <= 120 and centroid_mean > 3000:
            genre = 'pop/rock'
        elif 110 < bpm <= 140 and centroid_mean > 3000:
            genre = 'dance/electronic'
        elif bpm > 140 and centroid_mean > 3500:
            genre = 'uptempo/edm'
        else:
            genre = 'mixed/generic'

        return {
            'duration_sec': round(duration, 1),
            'bpm': round(bpm, 1),
            'rms_energy_mean': round(rms_mean, 4),
            'rms_energy_std': round(rms_std, 4),
            'spectral_centroid_mean': round(centroid_mean, 1),
            'spectral_flatness_mean': round(flatness_mean, 4),
            'spectral_contrast_mean': round(contrast_mean, 2),
            'zero_crossing_rate_mean': round(zcr_mean, 4),
            'arousal': round(arousal, 3),
            'valence': round(valence, 3),
            'mood_quadrant': mood_quadrant,
            'genre_affinity': genre,
            'energy_curve': energy_segments,
            'energy_trend': energy_trend,
        }


# ═══════════════════════════════════════════════════════════════
# CROSS-MODAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

class BrandConsistencyAnalyzer:
    """Cross-reference visual and sonic analyses for brand consistency.

    Combines VisualAnalyzer results and SonicAnalyzer results into a
    unified brand report with alignment scores.
    """

    # Visual mood → sonic mood mapping for alignment
    VISUAL_SONIC_MAP = {
        'passionate': ['happy/excited', 'tense/angry'],
        'energetic': ['happy/excited', 'tense/angry'],
        'calm': ['calm/peaceful'],
        'serene': ['calm/peaceful'],
        'cheerful': ['happy/excited'],
        'optimistic': ['happy/excited', 'calm/peaceful'],
        'melancholic': ['sad/melancholic'],
        'mysterious': ['sad/melancholic', 'neutral/ambiguous'],
        'romantic': ['calm/peaceful', 'sad/melancholic'],
        'creative': ['neutral/ambiguous', 'happy/excited'],
        'fresh': ['happy/excited', 'calm/peaceful'],
        'bold': ['tense/angry', 'happy/excited'],
        'dramatic': ['tense/angry', 'happy/excited'],
        'playful': ['happy/excited'],
        'intense': ['tense/angry', 'happy/excited'],
        'earthy': ['calm/peaceful'],
        'sophisticated': ['calm/peaceful', 'neutral/ambiguous'],
        'pure': ['calm/peaceful'],
        'trustworthy': ['calm/peaceful'],
        'warm': ['calm/peaceful', 'neutral/ambiguous'],
        'sweet': ['happy/excited', 'calm/peaceful'],
    }

    # Energy alignment: visual brightness → sonic energy
    ENERGY_ALIGNMENT = {
        'bright': 0.7,
        'mid_tone': 0.5,
        'dark': 0.3,
    }

    # Tempo alignment: visual contrast → sonic tempo
    TEMPO_ALIGNMENT = {
        'high_contrast': 130.0,
        'moderate_contrast': 100.0,
        'low_contrast': 75.0,
    }

    @classmethod
    def compute_visual_mood_vector(cls, visual_results: list) -> dict:
        """Aggregate mood vectors from multiple image analyses."""
        all_moods = []
        aesthetic_scores = []
        dominant_colors_all = []
        style_scores = {}

        for v in visual_results:
            if 'error' in v:
                continue
            aesthetic_scores.append(v.get('aesthetic_score', 5.0))
            all_moods.extend(v.get('color_mood_palette', []))
            dominant_colors_all.extend(v.get('dominant_colors', []))

            for style, conf in v.get('style_classification', []):
                if style not in style_scores:
                    style_scores[style] = []
                style_scores[style].append(conf)

        if not aesthetic_scores:
            return None

        # Aggregate style consistency
        avg_style_confidence = {}
        for style, scores in style_scores.items():
            avg_style_confidence[style] = round(float(np.mean(scores)), 2)
        sorted_styles = sorted(avg_style_confidence.items(), key=lambda x: x[1], reverse=True)

        # Mood consistency
        if all_moods:
            mood_counts = Counter(all_moods)
            top_moods = mood_counts.most_common(5)
        else:
            top_moods = []

        # Color consistency
        if dominant_colors_all:
            color_counts = Counter(dominant_colors_all)
            brand_colors = [c for c, _ in color_counts.most_common(6)]
        else:
            brand_colors = []

        return {
            'mean_aesthetic_score': round(float(np.mean(aesthetic_scores)), 1),
            'aesthetic_std': round(float(np.std(aesthetic_scores)), 2),
            'top_styles': sorted_styles[:3],
            'brand_colors': brand_colors,
            'top_moods': [{'mood': m, 'frequency': round(c / len(all_moods), 2)}
                          for m, c in top_moods],
            'total_images_analyzed': len(aesthetic_scores),
        }

    @classmethod
    def compute_sonic_mood_vector(cls, sonic_results: list) -> dict:
        """Aggregate mood vectors from multiple audio analyses."""
        all_moods = []
        bpm_values = []
        arousal_values = []
        valence_values = []
        genres = []

        for s in sonic_results:
            if 'error' in s:
                continue
            all_moods.append(s.get('mood_quadrant', 'neutral/ambiguous'))
            bpm_values.append(s.get('bpm', 120.0))
            arousal_values.append(s.get('arousal', 0.5))
            valence_values.append(s.get('valence', 0.5))
            genres.append(s.get('genre_affinity', 'mixed/generic'))

        if not all_moods:
            return None

        mood_counts = Counter(all_moods)
        genre_counts = Counter(genres)

        return {
            'mean_arousal': round(float(np.mean(arousal_values)), 3),
            'mean_valence': round(float(np.mean(valence_values)), 3),
            'mean_bpm': round(float(np.mean(bpm_values)), 1),
            'bpm_std': round(float(np.std(bpm_values)), 2),
            'dominant_mood': mood_counts.most_common(1)[0][0] if mood_counts else 'unknown',
            'mood_distribution': [{'mood': m, 'frequency': round(c / len(all_moods), 2)}
                                  for m, c in mood_counts.most_common()],
            'dominant_genre': genre_counts.most_common(1)[0][0] if genre_counts else 'unknown',
            'genre_diversity': len(genre_counts),
            'total_audio_analyzed': len(all_moods),
        }

    @classmethod
    def compute_cross_modal_alignment(cls, visual_vector: dict, sonic_vector: dict) -> dict:
        """Score how well visual and sonic identities align."""
        if not visual_vector or not sonic_vector:
            return {'alignment_score': 0, 'details': 'Insufficient data for cross-modal analysis'}

        # Mood alignment: do visual moods match sonic mood?
        vis_moods = set()
        for entry in visual_vector.get('top_moods', []):
            mood_name = entry.get('mood', '')
            if mood_name in cls.VISUAL_SONIC_MAP:
                expected_sonic_moods = cls.VISUAL_SONIC_MAP[mood_name]
                vis_moods.update(expected_sonic_moods)

        sonic_mood = sonic_vector.get('dominant_mood', 'neutral/ambiguous')
        mood_alignment = 1.0 if sonic_mood in vis_moods else \
                         0.6 if sonic_vector.get('mean_valence', 0.5) > 0.5 and \
                                 any('happy' in v or 'calm' in v for v in vis_moods) else 0.3

        # Energy alignment: visual brightness → sonic arousal
        # Compute average brightness from visual results
        brightness_scores = []
        if visual_vector.get('top_styles'):
            # Map styles to approximate brightness
            style_brightness_map = {
                'minimalist': 0.8, 'clean_modern': 0.8, 'pastel': 0.75,
                'vibrant_colorful': 0.7, 'vintage': 0.5, 'nature_organic': 0.5,
                'monochrome': 0.5, 'grunge': 0.3, 'dark_moody': 0.2, 'noir': 0.15,
            }
            for style, _ in visual_vector.get('top_styles', []):
                brightness_scores.append(style_brightness_map.get(style, 0.5))

        vis_energy = float(np.mean(brightness_scores)) if brightness_scores else 0.5
        sonic_energy = sonic_vector.get('mean_arousal', 0.5)
        energy_alignment = 1.0 - min(abs(vis_energy - sonic_energy), 1.0)

        # Tempo alignment: visual contrast → sonic tempo
        vis_tempo_expected = 100.0  # default moderate
        vis_style_contrast_map = {
            'high_contrast': 130.0, 'moderate_contrast': 100.0, 'low_contrast': 75.0,
        }
        sonic_bpm = sonic_vector.get('mean_bpm', 100.0)
        tempo_alignment = 1.0 - min(abs(vis_tempo_expected - sonic_bpm) / 80.0, 1.0)

        # Consistency breadth penalty: if many different styles/moods detected, brand is less consistent
        diversity_penalty = 1.0
        if visual_vector.get('top_styles') and len(visual_vector['top_styles']) >= 3:
            diversity_penalty *= 0.9
        if sonic_vector.get('genre_diversity', 1) >= 3:
            diversity_penalty *= 0.9

        # Composite score
        alignment_score = (
            mood_alignment * 0.35 +
            energy_alignment * 0.30 +
            tempo_alignment * 0.15 +
            diversity_penalty * 0.20
        ) * 100

        return {
            'alignment_score': round(alignment_score, 1),
            'mood_alignment': round(mood_alignment, 2),
            'energy_alignment': round(energy_alignment, 2),
            'tempo_alignment': round(tempo_alignment, 2),
            'visual_energy_level': round(vis_energy, 2),
            'sonic_energy_level': round(sonic_energy, 2),
            'visual_mood_suggestions': list(vis_moods)[:4],
            'sonic_mood_detected': sonic_mood,
            'analysis_quality': 'good' if alignment_score > 50 else 'partial',
        }

    @classmethod
    def compute_brand_consistency(cls, visual_vector: dict, sonic_vector: dict,
                                  cross_modal: dict) -> dict:
        """Compute overall brand consistency score."""
        if not visual_vector and not sonic_vector:
            return {'overall_consistency': 0, 'assessment': 'No content provided for analysis'}

        scores = []
        score_details = {}

        # Visual consistency (low std = consistent)
        if visual_vector:
            vis_std = visual_vector.get('aesthetic_std', 2.0)
            vis_consistency = max(0, 100 - vis_std * 20)
            scores.append(vis_consistency)
            score_details['visual_consistency'] = round(vis_consistency, 1)

        # Sonic consistency (low BPM std = consistent tempo)
        if sonic_vector:
            bpm_std = sonic_vector.get('bpm_std', 20.0)
            sonic_consistency = max(0, 100 - bpm_std * 3)
            scores.append(sonic_consistency)
            score_details['sonic_consistency'] = round(sonic_consistency, 1)

        # Cross-modal alignment
        if cross_modal:
            alignment = cross_modal.get('alignment_score', 0)
            scores.append(alignment)
            score_details['cross_modal_alignment'] = round(alignment, 1)

        overall = float(np.mean(scores)) if scores else 50.0

        if overall >= 80:
            assessment = 'strong — brand identity is cohesive across visual and sonic channels'
        elif overall >= 60:
            assessment = 'moderate — some consistency, but opportunities to tighten cross-modal alignment'
        elif overall >= 40:
            assessment = 'weak — visual and sonic identities diverge significantly'
        else:
            assessment = 'incoherent — brand identity is fragmented across channels'

        return {
            'overall_consistency': round(overall, 1),
            'assessment': assessment,
            'score_components': score_details,
            'has_visual_data': visual_vector is not None,
            'has_sonic_data': sonic_vector is not None,
        }

    @classmethod
    def generate_recommendations(cls, visual_vector: dict, sonic_vector: dict,
                                 cross_modal: dict, consistency: dict) -> list:
        """Generate actionable recommendations from analysis results."""
        recs = []

        if not visual_vector and not sonic_vector:
            return ['Provide at least one image URL or audio URL for analysis.']

        if consistency.get('overall_consistency', 50) >= 80:
            recs.append('Brand consistency is strong — focus on maintaining and documenting the current identity.')
            return recs

        if visual_vector:
            if len(visual_vector.get('top_styles', [])) >= 3:
                recs.append(
                    f"Visual style is fragmented ({len(visual_vector['top_styles'])} styles detected). "
                    "Consider narrowing to 1-2 dominant visual styles for brand consistency."
                )
            if visual_vector.get('aesthetic_std', 0) > 2.0:
                recs.append(
                    f"Visual quality varies significantly (std: {visual_vector['aesthetic_std']}). "
                    "Standardize image quality, lighting, and composition across brand assets."
                )
            brand_colors = visual_vector.get('brand_colors', [])
            if brand_colors and len(brand_colors) >= 5:
                recs.append(
                    f"Brand uses {len(brand_colors)} distinct colors — "
                    f"consider defining a 3-4 color palette for visual consistency."
                )

        if sonic_vector:
            if sonic_vector.get('genre_diversity', 1) >= 3:
                recs.append(
                    f"{sonic_vector['genre_diversity']} different genres detected in audio. "
                    "Define a consistent sonic identity (e.g., same genre family, similar BPM range)."
                )
            bpm_std = sonic_vector.get('bpm_std', 0)
            if bpm_std > 15:
                recs.append(
                    f"Tempo varies widely (std: {bpm_std} BPM). "
                    "Aim for a consistent BPM range (±10 BPM) across brand audio."
                )

        if cross_modal and cross_modal.get('alignment_score', 100) < 50:
            vis_energy = cross_modal.get('visual_energy_level', 0.5)
            son_energy = cross_modal.get('sonic_energy_level', 0.5)
            energy_diff = abs(vis_energy - son_energy)
            if energy_diff > 0.3:
                recs.append(
                    f"Energy misalignment between visual ({vis_energy:.2f}) and sonic ({son_energy:.2f}). "
                    "Match the emotional energy of visual and audio content "
                    "(e.g., bright/high-contrast visuals should pair with higher energy audio)."
                )

            vis_mood = cross_modal.get('visual_mood_suggestions', [])
            son_mood = cross_modal.get('sonic_mood_detected', '')
            if vis_mood and son_mood:
                recs.append(
                    f"Visuals suggest '{vis_mood[0]}' mood while audio is '{son_mood}'. "
                    "Aim for a consistent mood across channels."
                )

        if not recs:
            recs.append('Brand identity shows reasonable alignment. Monitor consistency as new content is added.')

        return recs


# ═══════════════════════════════════════════════════════════════
# FILE HELPERS
# ═══════════════════════════════════════════════════════════════

def download_file(url: str, suffix: str = '') -> Optional[str]:
    """Download a file from URL to a temp file. Returns path or None."""
    try:
        _, ext = os.path.splitext(url.split('?')[0])
        if not ext:
            ext = suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            urllib.request.urlretrieve(url, f.name)
            return f.name
    except Exception:
        return None


def load_image(file_path: str) -> Optional[np.ndarray]:
    """Load an image file as numpy array."""
    try:
        from PIL import Image
        img = Image.open(file_path)
        img = img.convert('RGB')
        return np.array(img)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# APIFY SDK WRAPPER
# ═══════════════════════════════════════════════════════════════

async def main():
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        image_urls = actor_input.get('imageUrls', [])
        audio_urls = actor_input.get('audioUrls', [])
        brand_name = actor_input.get('brandName', 'Unnamed Brand')

        Actor.log.info(f"Starting brand analysis for '{brand_name}'")
        Actor.log.info(f"  Images: {len(image_urls)}, Audio: {len(audio_urls)}")

        if not image_urls and not audio_urls:
            await Actor.push({
                'error': 'No content provided',
                'message': 'Provide at least one imageUrl or audioUrl for analysis.',
            })
            return

        # ─── Phase 1: Analyze all images ─────
        visual_results = []
        for i, url in enumerate(image_urls):
            Actor.log.info(f"Analyzing image {i + 1}/{len(image_urls)}: {url[:60]}...")
            file_path = download_file(url, '.jpg')
            if not file_path:
                visual_results.append({'error': f'Failed to download: {url[:60]}'})
                continue
            try:
                img_array = load_image(file_path)
                if img_array is None:
                    visual_results.append({'error': f'Failed to load image: {url[:60]}'})
                else:
                    result = VisualAnalyzer.analyze_image(img_array)
                    result['source_url'] = url
                    visual_results.append(result)
            finally:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

        # ─── Phase 2: Analyze all audio ──────
        sonic_results = []
        for i, url in enumerate(audio_urls):
            Actor.log.info(f"Analyzing audio {i + 1}/{len(audio_urls)}: {url[:60]}...")
            file_path = download_file(url, '.wav')
            if not file_path:
                sonic_results.append({'error': f'Failed to download: {url[:60]}'})
                continue
            try:
                result = SonicAnalyzer.analyze_audio(file_path)
                result['source_url'] = url
                sonic_results.append(result)
            finally:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

        # ─── Phase 3: Aggregate and cross-analyze ──
        visual_vector = BrandConsistencyAnalyzer.compute_visual_mood_vector(visual_results)
        sonic_vector = BrandConsistencyAnalyzer.compute_sonic_mood_vector(sonic_results)
        cross_modal = BrandConsistencyAnalyzer.compute_cross_modal_alignment(visual_vector, sonic_vector)
        consistency = BrandConsistencyAnalyzer.compute_brand_consistency(visual_vector, sonic_vector, cross_modal)
        recommendations = BrandConsistencyAnalyzer.generate_recommendations(
            visual_vector, sonic_vector, cross_modal, consistency
        )

        # ─── Phase 4: Build output ───
        output = {
            'brand_name': brand_name,
            'visual_identity': visual_vector if visual_vector else {'error': 'No valid image data'},
            'sonic_identity': sonic_vector if sonic_vector else {'error': 'No valid audio data'},
            'cross_modal_alignment': cross_modal,
            'brand_consistency': consistency,
            'recommendations': recommendations,
            '_meta': {
                'images_requested': len(image_urls),
                'images_analyzed': sum(1 for v in visual_results if 'error' not in v),
                'audio_requested': len(audio_urls),
                'audio_analyzed': sum(1 for s in sonic_results if 'error' not in s),
            }
        }

        await Actor.push(output)
        Actor.log.info(f"Brand analysis complete for '{brand_name}'")
        Actor.log.info(f"  Consistency score: {consistency.get('overall_consistency', 'N/A')}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
