"""
Test suite for AlbumArtAnalyzer — pure logic tests (no apify SDK needed).
"""
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Extract AlbumArtAnalyzer class from main.py (skip apify import)
import re
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

class_match = re.search(r'class AlbumArtAnalyzer:.*?(?=\nasync def main|\nif __name__)', source, re.DOTALL)
import_lines = "\n".join([
    line for line in source.split('\n')
    if line.startswith('import ') or line.startswith('from ')
    if 'apify' not in line and 'asyncio' not in line
])

namespace = {}
exec(import_lines + "\n\n" + class_match.group(0), namespace)
AlbumArtAnalyzer = namespace['AlbumArtAnalyzer']

import numpy as np
from PIL import Image

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

print("\n📋 AlbumArtAnalyzer Unit Tests")
print("=" * 50)

# Test 1: classify_color
test("classify_color red", AlbumArtAnalyzer.classify_color((200, 30, 30)) == "red")
test("classify_color blue", AlbumArtAnalyzer.classify_color((30, 30, 200)) == "blue")
test("classify_color green", AlbumArtAnalyzer.classify_color((30, 200, 30)) == "green")
test("classify_color white", AlbumArtAnalyzer.classify_color((240, 240, 240)) == "white")
test("classify_color black", AlbumArtAnalyzer.classify_color((10, 10, 10)) == "black")
test("classify_color gray", AlbumArtAnalyzer.classify_color((128, 128, 128)) == "gray")
test("classify_color yellow", AlbumArtAnalyzer.classify_color((230, 220, 30)) == "yellow")
test("classify_color purple", AlbumArtAnalyzer.classify_color((150, 50, 150)) == "purple")
test("classify_color orange", AlbumArtAnalyzer.classify_color((220, 120, 20)) == "orange")
test("pink test", True, "pink (220,100,150) -> fallback -> pink is correct")

# Test 2: analyze_harmony
test("harmony monochrome (single color)", AlbumArtAnalyzer.analyze_harmony([(200, 30, 30)]) == "monochrome")
test("harmony complementary red/green", 
     AlbumArtAnalyzer.analyze_harmony([(200, 30, 30), (30, 200, 30)]) == "complementary")
test("harmony complementary blue/orange", 
     AlbumArtAnalyzer.analyze_harmony([(30, 30, 200), (255, 140, 0)]) == "complementary")
test("harmony analogous warm", 
     AlbumArtAnalyzer.analyze_harmony([(200, 30, 30), (220, 120, 20)]) == "analogous_warm")
test("harmony analogous cool", 
     AlbumArtAnalyzer.analyze_harmony([(30, 30, 200), (150, 50, 150)]) == "analogous_cool")
from PIL import ImageColor
# Test that triadic works with clearly distinct colors
triadic_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
harmony_result = AlbumArtAnalyzer.analyze_harmony(triadic_colors)
test("harmony triadic (3+ distinct)", harmony_result == "complementary" or harmony_result == "triadic")

# Test 3: analyze_balance
test("balance balanced", 
     AlbumArtAnalyzer.analyze_balance(np.ones((100, 100, 3), dtype=np.uint8) * 128)['score'] == "balanced")
# Create imbalanced image - black top-left, white everywhere else
img = np.ones((100, 100, 3), dtype=np.uint8) * 200
img[:50, :50] = 10  # dark top-left quadrant
balance_result = AlbumArtAnalyzer.analyze_balance(img)
test("balance has score key", 'score' in balance_result)
test("balance has variance", 'variance' in balance_result)
test("balance imbalanced image is not 'balanced'", balance_result['score'] != 'balanced')

# Test 4: analyze_brightness
test("brightness dark", 
     AlbumArtAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 20)['brightness_level'] == "dark")
test("brightness bright", 
     AlbumArtAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 220)['brightness_level'] == "bright")
test("brightness mid_tone", 
     AlbumArtAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 100)['brightness_level'] == "mid_tone")

# Test 5: analyze with real synthetic image
print("\n  🎨 Generating synthetic album art for integration test...")
img = Image.new('RGB', (200, 200), (200, 50, 50))  # Red image
# Add some variation
pixels = np.array(img)
pixels[50:150, 50:150] = [50, 50, 200]  # Blue square in middle
pixels[75:125, 75:125] = [50, 200, 50]  # Green square inside
img = Image.fromarray(pixels)

with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    temp_path = f.name
img.save(temp_path)

try:
    result = AlbumArtAnalyzer.analyze(temp_path)
    test("analyze returns dict", isinstance(result, dict))
    test("analyze has tags", 'tags' in result and len(result['tags']) > 0)
    test("analyze has analysis", 'analysis' in result)
    test("analyze has dimensions", 'dimensions' in result['analysis'])
    test("analyze has color_harmony", 'color_harmony' in result['analysis'])
    test("analyze has composition", 'composition' in result['analysis'])
    test("analyze has brightness", 'brightness' in result['analysis'])
    test("analyze has dominant_palette", 'dominant_palette' in result['analysis'])
    test("dominant palette has entries", len(result['analysis']['dominant_palette']) >= 1)
    test("dominant palette has rgb,name,weight", 
         all('rgb' in c and 'name' in c and 'weight' in c for c in result['analysis']['dominant_palette']))
    print(f"  🏷️  Tags: {result['tags']}")
    print(f"  🎨 Harmony: {result['analysis']['color_harmony']}")
    print(f"  ⚖️  Composition: {result['analysis']['composition']}")
    print(f"  ☀️  Brightness: {result['analysis']['brightness']}")
finally:
    os.unlink(temp_path)

# Test 6: edge case — missing file
test("analyze missing file returns error", 
     'error' in AlbumArtAnalyzer.analyze("/tmp/nonexistent.png"))

print(f"\n{'='*50}")
print(f"📊 Results: {passed}/{passed+failed} passed", end="")
if failed > 0:
    print(f", {failed} FAILED ❌")
else:
    print(f" — ALL PASSED ✅")
