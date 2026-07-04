"""
Test suite for Cross-Modal Brand Consistency Analyzer.

Uses the duplicated test class pattern (Pattern B) to avoid complex imports.
Tests cover:
- VisualAnalyzer: color classification, dominant colors, temperature, brightness, style
- SonicAnalyzer: arousal, valence, mood quadrant, full analysis with synthetic audio
- BrandConsistencyAnalyzer: aggregation, cross-modal alignment, recommendations
"""

import json
import math
import os
import sys
import tempfile
import unittest
from collections import Counter
from io import BytesIO
from unittest.mock import MagicMock, patch

import numpy as np


# ═══════════════════════════════════════════════════════════════
# Import the module (exec-extraction pattern for the logic classes)
# ═══════════════════════════════════════════════════════════════

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location("brand_analyzer", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"))
mod = importlib.util.module_from_spec(spec)

# Read source to extract just the logic classes (skip apify SDk)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

# Execute into a namespace with numpy pre-loaded
namespace = {'np': np}
exec(source, namespace)

VisualAnalyzer = namespace['VisualAnalyzer']
SonicAnalyzer = namespace['SonicAnalyzer']
BrandConsistencyAnalyzer = namespace['BrandConsistencyAnalyzer']


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC TEST DATA GENERATORS
# ═══════════════════════════════════════════════════════════════

def make_rgb_image(height=100, width=100, r=255, g=0, b=0):
    """Create a solid-color RGB image as numpy array."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :, 0] = r
    img[:, :, 1] = g
    img[:, :, 2] = b
    return img


def make_gradient_image(height=100, width=100):
    """Create a gradient image (red -> blue) for testing."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(width):
        ratio = x / width
        img[:, x, 0] = int(255 * (1 - ratio))
        img[:, x, 1] = 0
        img[:, x, 2] = int(255 * ratio)
    return img


def make_sine_wav(frequency=440, duration=3.0, sample_rate=22050):
    """Generate a synthetic sine wave WAV file. Returns file path."""
    import struct
    import wave

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    samples = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)
    # Write as temp WAV
    fd, path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    import soundfile as sf
    sf.write(path, samples, sample_rate)
    return path


def make_noise_wav(duration=2.0, sample_rate=22050, amplitude=0.3):
    """Generate synthetic white noise WAV file."""
    samples = np.random.randn(int(sample_rate * duration)).astype(np.float32) * amplitude
    fd, path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    import soundfile as sf
    sf.write(path, samples, sample_rate)
    return path


# ═══════════════════════════════════════════════════════════════
# TESTS: VisualAnalyzer
# ═══════════════════════════════════════════════════════════════

class TestVisualAnalyzerColorClassification(unittest.TestCase):
    """Test color classification from RGB values."""

    def test_classify_red(self):
        self.assertEqual(VisualAnalyzer.classify_color((255, 0, 0)), 'red')

    def test_classify_green(self):
        self.assertEqual(VisualAnalyzer.classify_color((0, 255, 0)), 'green')

    def test_classify_blue(self):
        self.assertEqual(VisualAnalyzer.classify_color((0, 0, 255)), 'blue')

    def test_classify_yellow(self):
        self.assertEqual(VisualAnalyzer.classify_color((255, 255, 0)), 'yellow')

    def test_classify_black(self):
        self.assertEqual(VisualAnalyzer.classify_color((0, 0, 0)), 'black')

    def test_classify_white(self):
        self.assertEqual(VisualAnalyzer.classify_color((255, 255, 255)), 'white')

    def test_classify_gray(self):
        self.assertEqual(VisualAnalyzer.classify_color((128, 128, 128)), 'gray')

    def test_classify_orange(self):
        self.assertEqual(VisualAnalyzer.classify_color((255, 165, 0)), 'orange')

    def test_classify_purple(self):
        self.assertEqual(VisualAnalyzer.classify_color((128, 0, 128)), 'purple')

    def test_classify_pink(self):
        self.assertEqual(VisualAnalyzer.classify_color((255, 192, 203)), 'pink')

    def test_classify_brown(self):
        self.assertEqual(VisualAnalyzer.classify_color((139, 90, 43)), 'brown')


class TestVisualAnalyzerDominantColors(unittest.TestCase):
    """Test dominant color extraction."""

    def test_solid_red_image(self):
        img = make_rgb_image(50, 50, 255, 0, 0)
        colors = VisualAnalyzer.get_dominant_colors(img, n=3)
        self.assertGreater(len(colors), 0)
        # Should contain red-ish colors
        r_vals = [c[0] for c, _ in colors]
        g_vals = [c[1] for c, _ in colors]
        b_vals = [c[2] for c, _ in colors]
        self.assertTrue(all(r > 200 for r in r_vals))
        self.assertTrue(all(g < 50 for g in g_vals))

    def test_solid_green_image(self):
        img = make_rgb_image(50, 50, 0, 255, 0)
        colors = VisualAnalyzer.get_dominant_colors(img, n=3)
        self.assertGreater(len(colors), 0)
        g_vals = [c[1] for c, _ in colors]
        self.assertTrue(all(g > 200 for g in g_vals))

    def test_color_count(self):
        img = make_rgb_image(50, 50, 100, 150, 200)
        colors = VisualAnalyzer.get_dominant_colors(img, n=5)
        self.assertLessEqual(len(colors), 5)

    def test_large_image_resampling(self):
        img = make_rgb_image(500, 500, 255, 0, 0)
        # Should not throw on large images
        colors = VisualAnalyzer.get_dominant_colors(img, n=3)
        self.assertGreater(len(colors), 0)


class TestVisualAnalyzerTemperature(unittest.TestCase):
    """Test color temperature assessment."""

    def test_warm_red(self):
        img = make_rgb_image(50, 50, 255, 100, 50)
        self.assertEqual(VisualAnalyzer.assess_color_temperature(img), 'warm')

    def test_cold_blue(self):
        img = make_rgb_image(50, 50, 50, 100, 255)
        self.assertEqual(VisualAnalyzer.assess_color_temperature(img), 'cool')

    def test_neutral_gray(self):
        img = make_rgb_image(50, 50, 128, 128, 128)
        self.assertEqual(VisualAnalyzer.assess_color_temperature(img), 'neutral')


class TestVisualAnalyzerBrightness(unittest.TestCase):
    """Test brightness and contrast analysis."""

    def test_bright_image(self):
        img = make_rgb_image(50, 50, 255, 255, 255)
        result = VisualAnalyzer.analyze_brightness(img)
        self.assertEqual(result['brightness_level'], 'bright')

    def test_dark_image(self):
        img = make_rgb_image(50, 50, 10, 10, 10)
        result = VisualAnalyzer.analyze_brightness(img)
        self.assertEqual(result['brightness_level'], 'dark')

    def test_mid_tone(self):
        img = make_rgb_image(50, 50, 100, 100, 100)
        result = VisualAnalyzer.analyze_brightness(img)
        self.assertEqual(result['brightness_level'], 'mid_tone')

    def test_brightness_structure(self):
        img = make_rgb_image(50, 50, 200, 200, 200)
        result = VisualAnalyzer.analyze_brightness(img)
        self.assertIn('brightness_level', result)
        self.assertIn('contrast_level', result)
        self.assertIn('mean_brightness', result)
        self.assertIn('brightness_std', result)
        self.assertIsInstance(result['mean_brightness'], float)


class TestVisualAnalyzerColorVariance(unittest.TestCase):
    """Test color diversity detection."""

    def test_low_diversity(self):
        img = make_rgb_image(50, 50, 128, 128, 128)
        self.assertEqual(VisualAnalyzer.analyze_color_variance(img), 'low_diversity')

    def test_high_diversity_gradient(self):
        img = make_gradient_image(50, 50)
        diversity = VisualAnalyzer.analyze_color_variance(img)
        self.assertIn(diversity, ['high_diversity', 'moderate_diversity'])


class TestVisualAnalyzerFullAnalysis(unittest.TestCase):
    """Test the full analyze_image pipeline."""

    def test_red_image_analysis(self):
        img = make_rgb_image(100, 100, 255, 0, 0)
        result = VisualAnalyzer.analyze_image(img)
        self.assertIn('dominant_colors', result)
        self.assertIn('color_palette', result)
        self.assertIn('color_temperature', result)
        self.assertIn('style_classification', result)
        self.assertIn('aesthetic_score', result)
        self.assertIn('color_mood_palette', result)
        # Red is classified as 'red'
        self.assertIn('red', result['dominant_colors'])

    def test_gradient_analysis(self):
        img = make_gradient_image(100, 100)
        result = VisualAnalyzer.analyze_image(img)
        self.assertIn('aesthetic_score', result)
        self.assertIsInstance(result['aesthetic_score'], float)
        self.assertGreater(result['aesthetic_score'], 0)

    def test_analysis_structure(self):
        img = make_rgb_image(100, 100, 0, 255, 0)
        result = VisualAnalyzer.analyze_image(img)
        required_keys = ['dominant_colors', 'color_palette', 'color_temperature',
                          'harmony_type', 'brightness', 'contrast', 'style_classification',
                          'aesthetic_score', 'color_mood_palette']
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")


# ═══════════════════════════════════════════════════════════════
# TESTS: SonicAnalyzer
# ═══════════════════════════════════════════════════════════════

class TestSonicAnalyzerMath(unittest.TestCase):
    """Test the pure math functions of SonicAnalyzer."""

    def test_high_arousal(self):
        arousal = SonicAnalyzer.compute_arousal(0.8, 160, 0.18)
        self.assertGreaterEqual(arousal, 0.5)
        self.assertLessEqual(arousal, 1.0)

    def test_low_arousal(self):
        arousal = SonicAnalyzer.compute_arousal(0.01, 40, 0.01)
        self.assertGreaterEqual(arousal, 0.0)
        self.assertLessEqual(arousal, 0.5)

    def test_medium_arousal(self):
        arousal = SonicAnalyzer.compute_arousal(0.3, 100, 0.08)
        self.assertGreaterEqual(arousal, 0.2)
        self.assertLessEqual(arousal, 0.8)

    def test_high_valence(self):
        valence = SonicAnalyzer.compute_valence(5000, 0.2, 60)
        self.assertGreaterEqual(valence, 0.5)
        self.assertLessEqual(valence, 1.0)

    def test_low_valence(self):
        valence = SonicAnalyzer.compute_valence(500, 0.9, 5)
        self.assertLessEqual(valence, 0.6)

    def test_medium_valence(self):
        valence = SonicAnalyzer.compute_valence(3000, 0.5, 30)
        self.assertGreaterEqual(valence, 0.3)
        self.assertLessEqual(valence, 0.9)

    def test_mood_happy(self):
        """High arousal + high valence = happy/excited."""
        mood = SonicAnalyzer.classify_mood_quadrant(0.7, 0.8)
        self.assertEqual(mood, 'happy/excited')

    def test_mood_calm(self):
        """Low arousal + high valence = calm/peaceful."""
        mood = SonicAnalyzer.classify_mood_quadrant(0.2, 0.7)
        self.assertEqual(mood, 'calm/peaceful')

    def test_mood_tense(self):
        """High arousal + low valence = tense/angry."""
        mood = SonicAnalyzer.classify_mood_quadrant(0.7, 0.2)
        self.assertEqual(mood, 'tense/angry')

    def test_mood_sad(self):
        """Low arousal + low valence = sad/melancholic."""
        mood = SonicAnalyzer.classify_mood_quadrant(0.2, 0.2)
        self.assertEqual(mood, 'sad/melancholic')

    def test_mood_ambiguous(self):
        """Borderline values = ambiguous."""
        mood = SonicAnalyzer.classify_mood_quadrant(0.48, 0.5)
        self.assertEqual(mood, 'neutral/ambiguous')


class TestSonicAnalyzerFullAnalysis(unittest.TestCase):
    """Test full audio analysis with synthetic audio."""

    def test_sine_wave_analysis(self):
        path = make_sine_wav(440, 2.0)
        try:
            result = SonicAnalyzer.analyze_audio(path)
            self.assertNotIn('error', result, f"Error: {result.get('error')}")
            self.assertIn('bpm', result)
            self.assertIn('mood_quadrant', result)
            self.assertIn('arousal', result)
            self.assertIn('valence', result)
            self.assertIn('energy_curve', result)
            self.assertIsInstance(result['bpm'], float)
            self.assertGreater(result['bpm'], 0)
        finally:
            os.unlink(path)

    def test_noise_wave_analysis(self):
        path = make_noise_wav(1.5)
        try:
            result = SonicAnalyzer.analyze_audio(path)
            self.assertNotIn('error', result)
            self.assertIn('spectral_flatness_mean', result)
            # Noise has high spectral flatness
            self.assertGreater(result['spectral_flatness_mean'], 0.5)
        finally:
            os.unlink(path)

    def test_very_short_audio(self):
        path = make_sine_wav(440, 0.3)
        try:
            result = SonicAnalyzer.analyze_audio(path)
            self.assertIn('error', result)
            self.assertIn('too short', result['error'].lower())
        finally:
            os.unlink(path)

    def test_analysis_structure(self):
        path = make_sine_wav(440, 3.0)
        try:
            result = SonicAnalyzer.analyze_audio(path)
            keys = ['duration_sec', 'bpm', 'arousal', 'valence', 'mood_quadrant',
                    'genre_affinity', 'energy_curve', 'energy_trend',
                    'rms_energy_mean', 'spectral_centroid_mean']
            for key in keys:
                self.assertIn(key, result, f"Missing key: {key}")
            # energy_curve should have segments
            self.assertGreaterEqual(len(result['energy_curve']), 2)
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════
# TESTS: BrandConsistencyAnalyzer
# ═══════════════════════════════════════════════════════════════

class TestBrandConsistencyAnalyzer(unittest.TestCase):
    """Test cross-modal aggregation, alignment, and recommendations."""

    def setUp(self):
        # Sample visual results
        self.sample_visuals = [
            {
                'dominant_colors': ['red', 'orange', 'yellow'],
                'color_palette': [[255, 0, 0], [255, 165, 0], [255, 255, 0]],
                'color_temperature': 'warm',
                'harmony_type': 'analogous_warm',
                'harmony_score': 7.0,
                'brightness': 'bright',
                'contrast': 'high_contrast',
                'color_diversity': 'moderate_diversity',
                'style_classification': [('vibrant_colorful', 0.75), ('vintage', 0.5)],
                'aesthetic_score': 7.5,
                'color_mood_palette': ['passionate', 'intense', 'warm', 'playful'],
            },
            {
                'dominant_colors': ['red', 'orange'],
                'color_palette': [[200, 20, 20], [255, 140, 0]],
                'color_temperature': 'warm',
                'harmony_type': 'analogous_warm',
                'harmony_score': 7.5,
                'brightness': 'bright',
                'contrast': 'moderate_contrast',
                'color_diversity': 'low_diversity',
                'style_classification': [('vibrant_colorful', 0.7), ('minimalist', 0.55)],
                'aesthetic_score': 7.8,
                'color_mood_palette': ['passionate', 'energetic', 'warm'],
            },
        ]

        self.sample_sonic = [
            {
                'bpm': 120.0, 'rms_energy_mean': 0.5, 'rms_energy_std': 0.1,
                'spectral_centroid_mean': 3500.0, 'spectral_flatness_mean': 0.3,
                'spectral_contrast_mean': 40.0, 'zero_crossing_rate_mean': 0.08,
                'arousal': 0.7, 'valence': 0.65,
                'mood_quadrant': 'happy/excited', 'genre_affinity': 'pop/rock',
                'energy_curve': [], 'energy_trend': 'stable', 'duration_sec': 30.0,
            },
            {
                'bpm': 115.0, 'rms_energy_mean': 0.45, 'rms_energy_std': 0.12,
                'spectral_centroid_mean': 3200.0, 'spectral_flatness_mean': 0.35,
                'spectral_contrast_mean': 38.0, 'zero_crossing_rate_mean': 0.07,
                'arousal': 0.65, 'valence': 0.7,
                'mood_quadrant': 'happy/excited', 'genre_affinity': 'pop/rock',
                'energy_curve': [], 'energy_trend': 'stable', 'duration_sec': 25.0,
            },
        ]

    def test_visual_aggregation(self):
        vector = BrandConsistencyAnalyzer.compute_visual_mood_vector(self.sample_visuals)
        self.assertIsNotNone(vector)
        self.assertIn('mean_aesthetic_score', vector)
        self.assertIn('top_styles', vector)
        self.assertIn('brand_colors', vector)
        self.assertIn('top_moods', vector)
        self.assertEqual(vector['total_images_analyzed'], 2)

    def test_visual_aggregation_empty(self):
        self.assertIsNone(BrandConsistencyAnalyzer.compute_visual_mood_vector([]))

    def test_visual_aggregation_all_errors(self):
        result = BrandConsistencyAnalyzer.compute_visual_mood_vector([
            {'error': 'fail'}, {'error': 'fail2'}
        ])
        self.assertIsNone(result)

    def test_sonic_aggregation(self):
        vector = BrandConsistencyAnalyzer.compute_sonic_mood_vector(self.sample_sonic)
        self.assertIsNotNone(vector)
        self.assertIn('mean_arousal', vector)
        self.assertIn('mean_valence', vector)
        self.assertIn('mean_bpm', vector)
        self.assertIn('dominant_mood', vector)
        self.assertIn('dominant_genre', vector)
        self.assertEqual(vector['total_audio_analyzed'], 2)

    def test_sonic_aggregation_empty(self):
        self.assertIsNone(BrandConsistencyAnalyzer.compute_sonic_mood_vector([]))

    def test_sonic_aggregation_errors(self):
        result = BrandConsistencyAnalyzer.compute_sonic_mood_vector([
            {'error': 'failed'}, {'error': 'failed2'}
        ])
        self.assertIsNone(result)

    def test_cross_modal_alignment(self):
        vis = BrandConsistencyAnalyzer.compute_visual_mood_vector(self.sample_visuals)
        son = BrandConsistencyAnalyzer.compute_sonic_mood_vector(self.sample_sonic)
        alignment = BrandConsistencyAnalyzer.compute_cross_modal_alignment(vis, son)
        self.assertIn('alignment_score', alignment)
        self.assertIn('mood_alignment', alignment)
        self.assertIn('energy_alignment', alignment)
        self.assertIn('visual_mood_suggestions', alignment)
        self.assertIn('sonic_mood_detected', alignment)

    def test_cross_modal_alignment_empty(self):
        alignment = BrandConsistencyAnalyzer.compute_cross_modal_alignment(None, None)
        self.assertEqual(alignment['alignment_score'], 0)
        self.assertIn('Insufficient data', alignment['details'])

    def test_brand_consistency(self):
        vis = BrandConsistencyAnalyzer.compute_visual_mood_vector(self.sample_visuals)
        son = BrandConsistencyAnalyzer.compute_sonic_mood_vector(self.sample_sonic)
        cross = BrandConsistencyAnalyzer.compute_cross_modal_alignment(vis, son)
        consistency = BrandConsistencyAnalyzer.compute_brand_consistency(vis, son, cross)
        self.assertIn('overall_consistency', consistency)
        self.assertIn('assessment', consistency)
        self.assertIn('score_components', consistency)
        self.assertIn('has_visual_data', consistency)
        self.assertIn('has_sonic_data', consistency)

    def test_consistency_without_audio(self):
        vis = BrandConsistencyAnalyzer.compute_visual_mood_vector(self.sample_visuals)
        consistency = BrandConsistencyAnalyzer.compute_brand_consistency(vis, None, None)
        self.assertIn('overall_consistency', consistency)
        self.assertFalse(consistency['has_sonic_data'])

    def test_consistency_without_visual(self):
        son = BrandConsistencyAnalyzer.compute_sonic_mood_vector(self.sample_sonic)
        consistency = BrandConsistencyAnalyzer.compute_brand_consistency(None, son, None)
        self.assertIn('overall_consistency', consistency)
        self.assertFalse(consistency['has_visual_data'])

    def test_consistency_empty_none(self):
        result = BrandConsistencyAnalyzer.compute_brand_consistency(None, None, None)
        self.assertEqual(result['overall_consistency'], 0)

    def test_recommendations_generated(self):
        vis = BrandConsistencyAnalyzer.compute_visual_mood_vector(self.sample_visuals)
        son = BrandConsistencyAnalyzer.compute_sonic_mood_vector(self.sample_sonic)
        cross = BrandConsistencyAnalyzer.compute_cross_modal_alignment(vis, son)
        consistency = BrandConsistencyAnalyzer.compute_brand_consistency(vis, son, cross)
        recs = BrandConsistencyAnalyzer.generate_recommendations(vis, son, cross, consistency)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

    def test_recommendations_empty_input(self):
        recs = BrandConsistencyAnalyzer.generate_recommendations(None, None, None, {'overall_consistency': 0})
        self.assertEqual(len(recs), 1)
        self.assertIn('Provide', recs[0])


class TestBrandConsistencyAnalyzerVsMismatched(unittest.TestCase):
    """Test alignment scoring with intentionally mismatched visual/audio."""

    def test_mismatched_mood_penalizes_score(self):
        # High-energy visuals
        bright_visuals = [
            {
                'dominant_colors': ['yellow', 'red', 'orange'],
                'color_palette': [[255, 255, 0], [255, 0, 0], [255, 165, 0]],
                'color_temperature': 'warm',
                'harmony_type': 'analogous_warm',
                'harmony_score': 8.0,
                'brightness': 'bright',
                'contrast': 'high_contrast',
                'color_diversity': 'high_diversity',
                'style_classification': [('vibrant_colorful', 0.9)],
                'aesthetic_score': 8.0,
                'color_mood_palette': ['energetic', 'playful', 'cheerful'],
            }
        ]
        # Low-energy audio (sad)
        sad_audio = [
            {
                'bpm': 50.0, 'rms_energy_mean': 0.05, 'rms_energy_std': 0.02,
                'spectral_centroid_mean': 1800.0, 'spectral_flatness_mean': 0.7,
                'spectral_contrast_mean': 15.0, 'zero_crossing_rate_mean': 0.02,
                'arousal': 0.15, 'valence': 0.2,
                'mood_quadrant': 'sad/melancholic', 'genre_affinity': 'ambient/drone',
                'energy_curve': [], 'energy_trend': 'decreasing', 'duration_sec': 30.0,
            }
        ]
        vis = BrandConsistencyAnalyzer.compute_visual_mood_vector(bright_visuals)
        son = BrandConsistencyAnalyzer.compute_sonic_mood_vector(sad_audio)
        alignment = BrandConsistencyAnalyzer.compute_cross_modal_alignment(vis, son)
        # Mismatch should score low
        self.assertLess(alignment['alignment_score'], 50)


if __name__ == '__main__':
    unittest.main()
