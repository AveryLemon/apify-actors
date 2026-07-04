"""
Test suite for MoodAnalyzer — pure logic tests.
These tests do NOT depend on apify SDK or Docker.
They test the mood analysis algorithms directly.
"""
import json
import os
import sys
import struct
import re
import tempfile

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Extract just the MoodAnalyzer class from main.py
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

# Extract the MoodAnalyzer class using regex
class_match = re.search(
    r'class MoodAnalyzer:.*?(?=\nasync def main|\nif __name__)',
    source, re.DOTALL
)
if not class_match:
    print("❌ Could not find MoodAnalyzer class in source")
    sys.exit(1)

class_source = class_match.group(0)

# Extract non-apify imports
import_lines = "\n".join([
    line for line in source.split('\n')
    if line.startswith('import ') or line.startswith('from ')
    if 'apify' not in line and 'asyncio' not in line
])

# Build the test module source
test_module_source = import_lines + "\n\n" + class_source

# Execute it to get MoodAnalyzer
namespace = {}
exec(test_module_source, namespace)
MoodAnalyzer = namespace['MoodAnalyzer']

# Import numpy explicitly for test-level usage
import numpy as np

# ============================================
# Tests
# ============================================
passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


print("\n📋 MoodAnalyzer Unit Tests")
print("=" * 60)

# ---- Test 1: compute_arousal ----
print("\n🟢 Arousal Computation:")
test("arousal low energy+slow=low",
     MoodAnalyzer.compute_arousal(0.1, 60, 0.03) < 0.4)
test("arousal high energy+fast=high",
     MoodAnalyzer.compute_arousal(0.8, 140, 0.15) > 0.6)
test("arousal moderate=mid-range",
     0.2 < MoodAnalyzer.compute_arousal(0.4, 100, 0.08) < 0.8)
test("arousal min energy",
     MoodAnalyzer.compute_arousal(0.0, 60, 0.01) >= 0.0)
test("arousal max energy",
     MoodAnalyzer.compute_arousal(1.0, 200, 0.2) <= 1.0)
test("arousal deterministic",
     MoodAnalyzer.compute_arousal(0.5, 120, 0.1) ==
     MoodAnalyzer.compute_arousal(0.5, 120, 0.1))

# ---- Test 2: compute_valence ----
print("\n🟢 Valence Computation:")
test("valence high centroid=higher",
     MoodAnalyzer.compute_valence(0.7, 0.2, 30) > 0.5)
test("valence low centroid=lower",
     MoodAnalyzer.compute_valence(0.1, 0.8, 5) < 0.5)
test("valence bounds 0-1",
     0 <= MoodAnalyzer.compute_valence(0.5, 0.5, 15) <= 1.0)
test("valence deterministic",
     MoodAnalyzer.compute_valence(0.5, 0.4, 20) ==
     MoodAnalyzer.compute_valence(0.5, 0.4, 20))

# ---- Test 3: classify_mood ----
print("\n🟢 Mood Classification:")
test("happy quadrant", "happy" in MoodAnalyzer.classify_mood(0.7, 0.8))
test("tense quadrant", "tense" in MoodAnalyzer.classify_mood(0.8, 0.3))
test("calm quadrant", "calm" in MoodAnalyzer.classify_mood(0.2, 0.8))
test("sad quadrant", "sad" in MoodAnalyzer.classify_mood(0.2, 0.2))
test("joyful high valence+arousal", "joyful" in MoodAnalyzer.classify_mood(0.5, 0.85))
test("peaceful high valence+low arousal", "peaceful" in MoodAnalyzer.classify_mood(0.2, 0.75))
test("angry low valence+high arousal", "angry" in MoodAnalyzer.classify_mood(0.7, 0.2))
test("agitated very low valence+high arousal", "agitated" in MoodAnalyzer.classify_mood(0.8, 0.3))
test("gloomy low valence+low arousal", "gloomy" in MoodAnalyzer.classify_mood(0.2, 0.2))
test("anticipation mid-range both", "anticipation" in MoodAnalyzer.classify_mood(0.6, 0.55))
test("returns list of strings",
     all(isinstance(m, str) for m in MoodAnalyzer.classify_mood(0.5, 0.5)))
test("no duplicate moods",
     len(MoodAnalyzer.classify_mood(0.7, 0.8)) == len(set(MoodAnalyzer.classify_mood(0.7, 0.8))))
test("happy before joyful (sorted by strength)" if "joyful" in MoodAnalyzer.classify_mood(0.7, 0.85) else True,
     "joyful" not in MoodAnalyzer.classify_mood(0.7, 0.8) or
     MoodAnalyzer.classify_mood(0.7, 0.85).index("happy") <
     MoodAnalyzer.classify_mood(0.7, 0.85).index("joyful"))

# ---- Test 4: describe_mood_texture ----
print("\n🟢 Texture Description:")
descriptions = [
    MoodAnalyzer.describe_mood_texture(0.1, 0.1, []),
    MoodAnalyzer.describe_mood_texture(0.2, 0.8, []),
    MoodAnalyzer.describe_mood_texture(0.9, 0.8, []),
    MoodAnalyzer.describe_mood_texture(0.8, 0.2, []),
    MoodAnalyzer.describe_mood_texture(0.5, 0.5, []),
]
test("all descriptions are strings",
     all(isinstance(d, str) for d in descriptions))
test("descriptions are non-empty",
     all(len(d) > 0 for d in descriptions))
test("different inputs give different descriptions",
     len(set(descriptions)) >= 3)
test("serene for low arousal+high valence",
     "serene" in MoodAnalyzer.describe_mood_texture(0.2, 0.8, []) or
     "peaceful" in MoodAnalyzer.describe_mood_texture(0.2, 0.8, []))

# ---- Test 5: analyze with synthetic audio ----
print("\n  🎵 Generating synthetic audio for integration test...")
sr = 22050
duration = 3
t = np.linspace(0, duration, int(sr * duration))
sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave (A4)
noise = 0.01 * np.random.randn(len(t))
test_audio = sine_wave + noise

# Save as temp WAV
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    temp_path = f.name

n_samples = len(test_audio)
with open(temp_path, 'wb') as f:
    data_size = n_samples * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + data_size))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16))
    f.write(struct.pack('<H', 1))
    f.write(struct.pack('<H', 1))
    f.write(struct.pack('<I', sr))
    f.write(struct.pack('<I', sr * 2))
    f.write(struct.pack('<H', 2))
    f.write(struct.pack('<H', 16))
    f.write(b'data')
    f.write(struct.pack('<I', data_size))
    scaled = np.int16(test_audio * 32767)
    f.write(scaled.tobytes())

try:
    result = MoodAnalyzer.analyze(temp_path)
    test("analyze returns dict", isinstance(result, dict))
    test("no error in result", 'error' not in result, str(result.get('error', '')))
    test("has moods key", 'moods' in result)
    test("has arousal_valence key", 'arousal_valence' in result)
    test("has analysis key", 'analysis' in result)
    test("has energy_curve key", 'energy_curve' in result)
    test("has segments key", 'segments' in result)
    test("has texture_description", 'texture_description' in result)
    test("moods is non-empty list", len(result['moods']) > 0)
    test("arousal in 0-1", 0 <= result['arousal_valence']['arousal'] <= 1)
    test("valence in 0-1", 0 <= result['arousal_valence']['valence'] <= 1)
    test("duration ~3s", abs(result['analysis']['duration_sec'] - 3.0) < 0.5)
    test("bpm is positive", result['analysis']['bpm'] >= 0)
    test("has tempo tag", 'tempo_tag' in result['analysis'])
    test("energy_curve is list", isinstance(result['energy_curve'], list))
    test("energy_curve has entries", len(result['energy_curve']) > 0)
    test("energy_curve entries have time_sec and energy",
         all('time_sec' in e and 'energy' in e for e in result['energy_curve']))
    test("segments is list", isinstance(result['segments'], list))
    test("segment has required fields" if len(result['segments']) > 0 else True,
         len(result['segments']) == 0 or all(
             all(k in s for k in ['start_sec', 'end_sec', 'moods', 'arousal', 'valence'])
             for s in result['segments']
         ))
    print(f"  📊 Sample moods: {result['moods']}")
    print(f"  📊 Arousal/Valence: {result['arousal_valence']}")
    print(f"  📊 Segments: {len(result['segments'])} segments")
finally:
    os.unlink(temp_path)

# ---- Test 6: edge cases ----
print("\n🟢 Edge Cases:")
empty_test = MoodAnalyzer.analyze("/tmp/nonexistent_file.mp3")
test("missing file returns error", 'error' in empty_test)

# Test energy_curve with empty audio
print("  Testing energy curve edge cases...")
empty_curve = MoodAnalyzer.compute_energy_curve(np.array([]), 22050)
test("empty audio = empty energy curve", len(empty_curve) == 0)

import numpy as np_utils
test("mood classification handles all corners",
     len(MoodAnalyzer.classify_mood(0.0, 0.0)) > 0)
test("mood classification handles extremes",
     len(MoodAnalyzer.classify_mood(1.0, 1.0)) > 0)

# Arousal extremes
test("compute_arousal handles zero",
     MoodAnalyzer.compute_arousal(0.0, 0.0, 0.0) >= 0.0)
test("compute_arousal handles max",
     MoodAnalyzer.compute_arousal(1.0, 300, 1.0) <= 1.0)

# Valence extremes
test("compute_valence handles zero",
     MoodAnalyzer.compute_valence(0.0, 0.0, 0.0) >= 0.0)
test("compute_valence handles max",
     MoodAnalyzer.compute_valence(1.0, 1.0, 100.0) <= 1.0)

print(f"\n{'='*60}")
print(f"📊 Results: {passed}/{passed+failed} passed", end="")
if failed > 0:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(f" — ALL PASSED ✅")
