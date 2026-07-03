import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

# Mock the apify Actor module before importing our code
with patch('apify.Actor', create=True) as mock_actor_class:
    mock_actor_instance = MagicMock()
    mock_actor_class.return_value = mock_actor_instance
    mock_actor_class.__aenter__.return_value = mock_actor_instance
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from main import AudioAnalyzer


class TestAudioAnalyzerEnergy:
    """Test the energy tagging logic."""

    def test_low_energy(self):
        assert AudioAnalyzer.tag_energy(0.1) == 'low_energy'

    def test_low_energy_boundary(self):
        assert AudioAnalyzer.tag_energy(0.349) == 'low_energy'

    def test_moderate_energy(self):
        assert AudioAnalyzer.tag_energy(0.5) == 'moderate_energy'

    def test_moderate_energy_boundary(self):
        assert AudioAnalyzer.tag_energy(0.35) == 'moderate_energy'

    def test_high_energy(self):
        assert AudioAnalyzer.tag_energy(0.8) == 'high_energy'

    def test_high_energy_boundary(self):
        assert AudioAnalyzer.tag_energy(0.65) == 'high_energy'

    def test_max_energy(self):
        assert AudioAnalyzer.tag_energy(1.0) == 'high_energy'

    def test_zero_energy(self):
        assert AudioAnalyzer.tag_energy(0.0) == 'low_energy'


class TestAudioAnalyzerMood:
    """Test the mood tagging logic."""

    def test_warm_soft_below_threshold(self):
        """Very low spectral centroid -> warm, soft, mellow"""
        tags = AudioAnalyzer.tag_mood(0.1, 0.5)
        assert 'warm' in tags
        assert 'soft' in tags
        assert 'mellow' in tags
        assert 'bright' not in tags

    def test_bright_above_threshold(self):
        """High spectral centroid -> bright but not warm"""
        tags = AudioAnalyzer.tag_mood(0.7, 0.5)
        assert 'bright' in tags
        assert 'warm' not in tags

    def test_airy_high_rolloff(self):
        tags = AudioAnalyzer.tag_mood(0.5, 0.9)
        assert 'airy' in tags

    def test_dark_low_rolloff(self):
        tags = AudioAnalyzer.tag_mood(0.5, 0.3)
        assert 'dark' in tags

    def test_both_airy_and_dark_not_possible(self):
        """Rolloff can't be both high and low"""
        tags = AudioAnalyzer.tag_mood(0.5, 0.6)
        assert 'airy' not in tags
        assert 'dark' not in tags

    def test_boundary_acoustic(self):
        tags = AudioAnalyzer.tag_mood(0.3, 0.5)
        assert 'warm' not in tags  # not below threshold
        assert 'soft' not in tags
        assert 'mellow' not in tags

    def test_boundary_airy(self):
        tags = AudioAnalyzer.tag_mood(0.5, 0.85)
        assert 'airy' in tags

    def test_boundary_dark(self):
        tags = AudioAnalyzer.tag_mood(0.5, 0.4)
        assert 'dark' in tags


class TestAudioAnalyzerDanceability:
    """Test rhythm/complexity tagging."""

    def test_steady_rhythm(self):
        tempogram = np.array([[5.0, 6.0, 5.0, 7.0, 5.0]])  # low std
        assert AudioAnalyzer.tag_danceability(tempogram) == 'steady_rhythm'

    def test_moderate_variation(self):
        tempogram = np.array([[10.0, 30.0, 15.0, 25.0, 20.0]])  # moderate std
        assert AudioAnalyzer.tag_danceability(tempogram) == 'moderate_variation'

    def test_complex_rhythm(self):
        tempogram = np.array([[50.0, 10.0, 80.0, 5.0, 90.0]])  # high std
        assert AudioAnalyzer.tag_danceability(tempogram) == 'complex_rhythm'

    def test_empty_tempogram(self):
        tempogram = np.array([[]])
        result = AudioAnalyzer.tag_danceability(tempogram)
        assert isinstance(result, str)

    def test_none_tempogram(self):
        assert AudioAnalyzer.tag_danceability(None) == 'unknown'

    def test_zero_tempogram(self):
        result = AudioAnalyzer.tag_danceability(np.array([[0, 0, 0, 0]]))
        assert result == 'steady_rhythm'


class TestAudioAnalyzerAnalyze:
    """Test the full analysis pipeline with a synthetic audio signal."""

    def generate_sine_wave(self, freq=440, duration_sec=5, sr=22050):
        t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
        return (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)

    def test_analyze_with_sine_wave(self, tmp_path):
        import librosa
        y = self.generate_sine_wave()
        sr = 22050
        file_path = tmp_path / 'test_sine.wav'
        import soundfile as sf
        sf.write(str(file_path), y, sr)

        result = AudioAnalyzer.analyze(str(file_path))
        print(f"Sine wave analysis: {result}")

        assert 'error' not in result, f"Got error: {result['error']}"
        assert 'tags' in result
        assert 'analysis' in result
        assert len(result['tags']) > 0
        assert result['analysis']['duration_sec'] == pytest.approx(5.0, rel=0.1)

    def test_analyze_with_bass_frequency(self, tmp_path):
        import librosa
        y = self.generate_sine_wave(freq=60, duration_sec=3)
        sr = 22050
        file_path = tmp_path / 'test_bass.wav'
        import soundfile as sf
        sf.write(str(file_path), y, sr)

        result = AudioAnalyzer.analyze(str(file_path))
        print(f"Bass analysis: {result}")

        assert 'error' not in result
        assert result['analysis']['bpm'] >= 0

    def test_analyze_empty_file_error(self, tmp_path):
        import librosa
        file_path = tmp_path / 'empty.wav'
        file_path.write_text('')

        result = AudioAnalyzer.analyze(str(file_path))
        assert 'error' in result

    def test_analyze_broken_file_error(self, tmp_path):
        import librosa
        file_path = tmp_path / 'broken.data'
        file_path.write_bytes(b'\x00\x01\x02\x03')

        result = AudioAnalyzer.analyze(str(file_path))
        assert 'error' in result

    def test_analyze_noise_signal(self, tmp_path):
        import librosa
        y = np.random.randn(44100).astype(np.float32) * 0.3
        sr = 22050
        file_path = tmp_path / 'test_noise.wav'
        import soundfile as sf
        sf.write(str(file_path), y, sr)

        result = AudioAnalyzer.analyze(str(file_path))
        assert 'error' not in result
        # Noise should have high spectral flatness
        assert 'noisy_texture' in result['tags'] or 'mixed_texture' in result['tags']

    def test_duration_reasonable(self, tmp_path):
        import librosa
        y = self.generate_sine_wave(duration_sec=2.5)
        sr = 22050
        file_path = tmp_path / 'test_duration.wav'
        import soundfile as sf
        sf.write(str(file_path), y, sr)

        result = AudioAnalyzer.analyze(str(file_path))
        assert abs(result['analysis']['duration_sec'] - 2.5) < 0.3


class TestAudioAnalyzerIntegration:
    """Integration-style tests using real audio processing."""

    def test_at_boundary_conditions(self, tmp_path):
        """Test analysis handles edge cases gracefully."""
        import librosa
        import soundfile as sf

        # Very short signal (0.1 sec)
        y = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 2205)).astype(np.float32)
        file_path = tmp_path / 'very_short.wav'
        sf.write(str(file_path), y, 22050)
        result = AudioAnalyzer.analyze(str(file_path))
        assert 'error' not in result or 'empty' not in result.get('error', '')
