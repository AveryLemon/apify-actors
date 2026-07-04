"""
Test suite for AudioAnalyzer — pure logic tests.
These tests do NOT depend on apify SDK or Docker.
They test the audio analysis algorithms directly.
"""
import json
import sys
import os

# Add parent to path so we can import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch: remove apify import before importing main
import importlib.util
spec = importlib.util.spec_from_file_location(
    "main_patched",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"),
)
# Read the raw source
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

# Remove the `from apify import Actor` line and `import asyncio` for the async main
# We only need the AudioAnalyzer class
import ast
import re

# Extract just the AudioAnalyzer class using regex
class_match = re.search(r'class AudioAnalyzer:.*?(?=\nasync def main|\nif __name__)', source, re.DOTALL)
if not class_match:
    print("❌ Could not find AudioAnalyzer class in source")
    sys.exit(1)

class_source = class_match.group(0)

# Also extract the import lines
import_lines = "\n".join([
    line for line in source.split('\n')
    if line.startswith('import ') or line.startswith('from ')
    if 'apify' not in line and 'asyncio' not in line
])

# Build the test module source
test_module_source = import_lines + "\n\n" + class_source

# Execute it
namespace = {}
exec(test_module_source, namespace)
AudioAnalyzer = namespace['AudioAnalyzer']

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

print("\n📋 AudioAnalyzer Unit Tests")
print("=" * 50)

# Test 1: tag_energy
test("tag_energy low", AudioAnalyzer.tag_energy(0.1) == "low_energy")
test("tag_energy moderate", AudioAnalyzer.tag_energy(0.5) == "moderate_energy")
test("tag_energy high", AudioAnalyzer.tag_energy(0.8) == "high_energy")
test("tag_energy boundary low->moderate", AudioAnalyzer.tag_energy(0.35) == "moderate_energy")
test("tag_energy boundary moderate->high", AudioAnalyzer.tag_energy(0.65) == "high_energy")

# Test 2: tag_mood
test("tag_mood warm+soft+mellow", 
     set(AudioAnalyzer.tag_mood(0.2, 0.5)) == {"warm", "soft", "mellow"})
test("tag_mood bright", 
     "bright" in AudioAnalyzer.tag_mood(0.7, 0.5))
test("tag_mood airy", 
     "airy" in AudioAnalyzer.tag_mood(0.5, 0.9))
test("tag_mood dark", 
     "dark" in AudioAnalyzer.tag_mood(0.5, 0.3))
test("tag_mood bright+airy", 
     set(AudioAnalyzer.tag_mood(0.7, 0.9)) == {"bright", "airy"})

# Test 3: tag_danceability
import numpy as np
test("tag_danceability steady", 
     AudioAnalyzer.tag_danceability(np.array([[1, 2, 3, 1, 2, 3]])) == "steady_rhythm")
test("tag_danceability moderate", 
     AudioAnalyzer.tag_danceability(np.array([[5, 35, 8, 32, 3, 38]])) == "moderate_variation")
test("tag_danceability complex", 
     AudioAnalyzer.tag_danceability(np.array([[1, 50, 5, 80, 10, 90]])) == "complex_rhythm")
test("tag_danceability none", 
     AudioAnalyzer.tag_danceability(np.array([])) == "unknown" if hasattr(np, 'array') else True)

# Test 4: test with synthetic audio
print("\n  🎵 Generating synthetic audio for integration test...")
sr = 22050
duration = 3  # seconds
t = np.linspace(0, duration, int(sr * duration))
sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave
noise = 0.01 * np.random.randn(len(t))
test_audio = sine_wave + noise

# Save as temp wav
import tempfile
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    temp_path = f.name

# Write WAV manually (simple PCM)
import struct
n_samples = len(test_audio)
with open(temp_path, 'wb') as f:
    # WAV header
    data_size = n_samples * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + data_size))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16))  # chunk size
    f.write(struct.pack('<H', 1))   # PCM
    f.write(struct.pack('<H', 1))   # mono
    f.write(struct.pack('<I', sr))  # sample rate
    f.write(struct.pack('<I', sr * 2))  # byte rate
    f.write(struct.pack('<H', 2))   # block align
    f.write(struct.pack('<H', 16))  # bits per sample
    f.write(b'data')
    f.write(struct.pack('<I', data_size))
    # Write samples as int16
    scaled = np.int16(test_audio * 32767)
    f.write(scaled.tobytes())

try:
    result = AudioAnalyzer.analyze(temp_path)
    test("analyze returns dict", isinstance(result, dict))
    test("analyze has tags", 'tags' in result and len(result['tags']) > 0)
    test("analyze has analysis", 'analysis' in result)
    test("analyze duration ~3s", abs(result['analysis']['duration_sec'] - 3.0) < 0.5)
    test("analyze has bpm", result['analysis']['bpm'] > 0)
    test("analyze has rms_energy", 0 <= result['analysis']['rms_energy'] <= 1)
    test("analyze has spectral_centroid", 0 <= result['analysis']['spectral_centroid'] <= 1)
    print(f"  📊 Sample output tags: {result['tags']}")
    print(f"  📊 Sample analysis: {json.dumps(result['analysis'], indent=2)}")
finally:
    os.unlink(temp_path)

# Test 5: edge cases
empty_test = AudioAnalyzer.analyze("/tmp/nonexistent_file.mp3")
test("analyze missing file returns error", 'error' in empty_test)

print(f"\n{'='*50}")
print(f"📊 Results: {passed}/{passed+failed} passed", end="")
if failed > 0:
    print(f", {failed} FAILED ❌")
else:
    print(f" — ALL PASSED ✅")
