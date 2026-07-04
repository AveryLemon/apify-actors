"""
Test suite for AestheticStyleAnalyzer — pure logic tests (no apify SDK needed).
Tests cover: color classification, harmony, composition, symmetry, style, aesthetic scoring.
"""
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Extract AestheticStyleAnalyzer class from main.py (skip apify import)
import re
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

class_match = re.search(r'class AestheticStyleAnalyzer:.*?(?=\nasync def main|\nif __name__)', source, re.DOTALL)
import_lines = "\n".join([
    line for line in source.split('\n')
    if line.startswith('import ') or line.startswith('from ')
    if 'apify' not in line and 'asyncio' not in line
])

namespace = {}
exec(import_lines + "\n\n" + class_match.group(0), namespace)
AestheticStyleAnalyzer = namespace['AestheticStyleAnalyzer']

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

print("\n📋 AestheticStyleAnalyzer Unit Tests")
print("=" * 55)

# ============================================================
# TEST GROUP 1: Color Classification
# ============================================================
print("\n1️⃣  Color Classification")
test("classify_color red", AestheticStyleAnalyzer.classify_color((200, 30, 30)) == "red")
test("classify_color blue", AestheticStyleAnalyzer.classify_color((30, 30, 200)) == "blue")
test("classify_color green", AestheticStyleAnalyzer.classify_color((30, 200, 30)) == "green")
test("classify_color white", AestheticStyleAnalyzer.classify_color((240, 240, 240)) == "white")
test("classify_color black", AestheticStyleAnalyzer.classify_color((10, 10, 10)) == "black")
test("classify_color gray", AestheticStyleAnalyzer.classify_color((128, 128, 128)) == "gray")
test("classify_color yellow", AestheticStyleAnalyzer.classify_color((230, 220, 30)) == "yellow")
test("classify_color purple", AestheticStyleAnalyzer.classify_color((150, 50, 150)) == "purple")
test("classify_color orange", AestheticStyleAnalyzer.classify_color((220, 120, 20)) == "orange")

# ============================================================
# TEST GROUP 2: Color Temperature
# ============================================================
print("\n2️⃣  Color Temperature")
test("temp warm (red-dominant)",
     AestheticStyleAnalyzer.assess_color_temperature(np.ones((10, 10, 3), dtype=np.uint8) * [220, 100, 50]) == "warm")
test("temp cool (blue-dominant)",
     AestheticStyleAnalyzer.assess_color_temperature(np.ones((10, 10, 3), dtype=np.uint8) * [50, 100, 220]) == "cool")
test("temp neutral",
     AestheticStyleAnalyzer.assess_color_temperature(np.ones((10, 10, 3), dtype=np.uint8) * [128, 128, 128]) == "neutral")

# ============================================================
# TEST GROUP 3: Harmony Analysis
# ============================================================
print("\n3️⃣  Color Harmony")
test("harmony monochrome", AestheticStyleAnalyzer.analyze_harmony([(200, 30, 30)]) == "monochrome")
test("harmony complementary red/green",
     AestheticStyleAnalyzer.analyze_harmony([(200, 30, 30), (30, 200, 30)]) == "complementary")
test("harmony complementary blue/orange",
     AestheticStyleAnalyzer.analyze_harmony([(30, 30, 200), (255, 140, 0)]) == "complementary")
test("harmony analogous warm",
     AestheticStyleAnalyzer.analyze_harmony([(200, 30, 30), (220, 120, 20)]) == "analogous_warm")
test("harmony analogous cool",
     AestheticStyleAnalyzer.analyze_harmony([(30, 30, 200), (150, 50, 150)]) == "analogous_cool")

# 3 distinct colors
triadic = AestheticStyleAnalyzer.analyze_harmony([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
test("harmony triadic or complementary", triadic in ("complementary", "triadic"))

# ============================================================
# TEST GROUP 4: Harmony Score
# ============================================================
print("\n4️⃣  Harmony Score")
test("harmony_score triadic = 9.0", AestheticStyleAnalyzer.score_harmony("triadic") == 9.0)
test("harmony_score complementary = 8.5", AestheticStyleAnalyzer.score_harmony("complementary") == 8.5)
test("harmony_score monochrome = 6.0", AestheticStyleAnalyzer.score_harmony("monochrome") == 6.0)
test("harmony_score unknown defaults to 5.0", AestheticStyleAnalyzer.score_harmony("unknown") == 5.0)

# ============================================================
# TEST GROUP 5: Brightness Analysis
# ============================================================
print("\n5️⃣  Brightness & Contrast")
test("brightness dark",
     AestheticStyleAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 20)['brightness_level'] == "dark")
test("brightness bright",
     AestheticStyleAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 220)['brightness_level'] == "bright")
test("brightness mid_tone",
     AestheticStyleAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 100)['brightness_level'] == "mid_tone")
# Zero-contrast = low_contrast
all_same = AestheticStyleAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 128)
test("contrast low_contrast (all same)", all_same['contrast_level'] == "low_contrast")
test("brightness has mean_brightness", 'mean_brightness' in all_same)
test("brightness has brightness_std", 'brightness_std' in all_same)

# ============================================================
# TEST GROUP 6: Color Diversity
# ============================================================
print("\n6️⃣  Color Diversity")
low_div = AestheticStyleAnalyzer.analyze_color_variance(np.ones((10, 10, 3), dtype=np.uint8) * 128)
test("diversity low (single color)", low_div == "low_diversity")

# High diversity: random values
np.random.seed(42)
high_div = AestheticStyleAnalyzer.analyze_color_variance(
    np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))
test("diversity not low for random image", high_div != "low_diversity")

# ============================================================
# TEST GROUP 7: Composition Balance
# ============================================================
print("\n7️⃣  Composition Balance")
# Uniform image should be balanced
uniform_balance = AestheticStyleAnalyzer.analyze_balance(np.ones((100, 100, 3), dtype=np.uint8) * 128)
test("balance balanced uniform", uniform_balance['score'] == "balanced")

# Dark TL, bright elsewhere = imbalanced
img = np.ones((100, 100, 3), dtype=np.uint8) * 200
img[:50, :50] = 10
imbalanced = AestheticStyleAnalyzer.analyze_balance(img)
test("balance returns score key", 'score' in imbalanced)
test("balance returns variance", 'variance' in imbalanced)
test("balance returns value", 'value' in imbalanced)
test("balance returns dominant_quadrant", 'dominant_quadrant' in imbalanced)
test("balance imbalanced not 'balanced'", imbalanced['score'] != 'balanced')

# ============================================================
# TEST GROUP 8: Symmetry
# ============================================================
print("\n8️⃣  Symmetry Analysis")
# Perfectly symmetric image
sym_img = np.zeros((100, 100, 3), dtype=np.uint8)
sym_img[:, :50] = [200, 200, 200]
sym_img[:, 50:] = [200, 200, 200]  # Symmetric halves
symmetry = AestheticStyleAnalyzer.analyze_symmetry(sym_img)
test("symmetry returns vertical", 'vertical_symmetry' in symmetry)
test("symmetry returns horizontal", 'horizontal_symmetry' in symmetry)
test("symmetry returns overall", 'overall' in symmetry)
test("symmetry overall >= 0 and <= 1", 0 <= symmetry['overall'] <= 1)

# ============================================================
# TEST GROUP 9: Rule of Thirds
# ============================================================
print("\n9️⃣  Rule of Thirds")
ro3 = AestheticStyleAnalyzer.analyze_rule_of_thirds(np.ones((100, 100, 3), dtype=np.uint8) * 128)
test("rule_of_thirds returns float 0-1", 0 <= ro3 <= 1)

# ============================================================
# TEST GROUP 10: Leading Lines
# ============================================================
print("\n🔟  Leading Lines")
lines = AestheticStyleAnalyzer.analyze_leading_lines(np.ones((100, 100, 3), dtype=np.uint8) * [200, 100, 50])
test("leading_lines returns score", 'score' in lines)
test("leading_lines returns description", 'description' in lines)
test("leading_lines returns edge_density", 'edge_density' in lines)
test("leading_lines score 0-1", 0 <= lines['score'] <= 1)
test("leading_lines description is known", lines['description'] in (
    'very_few_edges', 'moderate_edges', 'rich_edge_structure', 'busy_texture', 'very_busy_noisy'))

# ============================================================
# TEST GROUP 11: Style Classification
# ============================================================
print("\n1️⃣1️⃣  Style Classification")
bright = AestheticStyleAnalyzer.analyze_brightness(np.ones((10, 10, 3), dtype=np.uint8) * 220)
styles = AestheticStyleAnalyzer.classify_style(
    bright, "low_diversity", "neutral",
    {'score': 'balanced', 'value': 8.0, 'variance': 5.0, 'dominant_quadrant': 'top_left'}
)
test("style returns list", isinstance(styles, list))
test("style returns at least 1 match", len(styles) >= 1)
test("style entries are tuples", all(len(s) == 2 for s in styles))
test("style confidences are 0-1", all(0 <= c <= 1 for _, c in styles))
# A bright, low-diversity, balanced image should match 'minimalist' or 'clean_modern'
style_names = [s for s, _ in styles]
test("style matches expected archetypes",
     any(s in style_names for s in ('minimalist', 'clean_modern', 'pastel', 'monochrome')))

# ============================================================
# TEST GROUP 12: Aesthetic Score
# ============================================================
print("\n1️⃣2️⃣  Aesthetic Score")
score = AestheticStyleAnalyzer.compute_aesthetic_score(
    {'brightness_level': 'mid_tone', 'contrast_level': 'moderate_contrast', 'mean_brightness': 100, 'brightness_std': 50},
    "moderate_diversity",
    {'score': 'balanced', 'value': 8.0, 'variance': 15.0, 'dominant_quadrant': 'top_left'},
    {'vertical_symmetry': 0.8, 'horizontal_symmetry': 0.7, 'overall': 0.75},
    "complementary",
    0.7,
    {'score': 0.7, 'description': 'moderate_edges', 'edge_density': 0.03},
    "warm"
)
test("aesthetic_score is float", isinstance(score, float))
test("aesthetic_score 0-10", 0 <= score <= 10)

# ============================================================
# TEST GROUP 13: Improvements Generation
# ============================================================
print("\n1️⃣3️⃣  Improvements")
improvements = AestheticStyleAnalyzer.generate_improvements(
    "mixed",
    {'score': 'high_contrast_imbalance', 'value': 3.0, 'variance': 80.0, 'dominant_quadrant': 'top_left'},
    {'brightness_level': 'dark', 'contrast_level': 'high_contrast', 'mean_brightness': 30, 'brightness_std': 80},
    {'vertical_symmetry': 0.3, 'horizontal_symmetry': 0.2, 'overall': 0.25},
    0.3,
    {'score': 0.3, 'description': 'very_busy_noisy', 'edge_density': 0.4},
)
test("improvements returns list", isinstance(improvements, list))
test("improvements returns at most 3", len(improvements) <= 3)
if improvements:
    test("improvement has issue", 'issue' in improvements[0])
    test("improvement has suggestion", 'suggestion' in improvements[0])
    test("improvement has impact", 'impact' in improvements[0])
    # Should have at least 1 high-impact issue
    impacts = [i['impact'] for i in improvements]
    test("improvement has high impact issue", 'high' in impacts)

# Few issues with a well-composed image
few_improvements = AestheticStyleAnalyzer.generate_improvements(
    "complementary",
    {'score': 'balanced', 'value': 8.0, 'variance': 15.0, 'dominant_quadrant': 'top_left'},
    {'brightness_level': 'bright', 'contrast_level': 'moderate_contrast', 'mean_brightness': 180, 'brightness_std': 60},
    {'vertical_symmetry': 0.85, 'horizontal_symmetry': 0.75, 'overall': 0.8},
    0.75,
    {'score': 0.8, 'description': 'rich_edge_structure', 'edge_density': 0.08},
)
test("improvements returns few for good image", len(few_improvements) <= 2)

# ============================================================
# TEST GROUP 14: Full Pipeline Integration
# ============================================================
print("\n1️⃣4️⃣  Full Pipeline Integration")
print("  🎨 Generating synthetic test image...")
# Create a well-composed synthetic image
img = Image.new('RGB', (300, 200), (200, 50, 50))  # Red background
pixels = np.array(img)
# Add variation
pixels[50:150, 100:200] = [50, 50, 200]  # Blue rectangle (center-right)
pixels[80:120, 130:170] = [50, 200, 50]    # Green square inside (focal point)
img = Image.fromarray(pixels)

with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    temp_path = f.name
img.save(temp_path)

try:
    result = AestheticStyleAnalyzer.analyze(temp_path)
    test("analyze returns dict", isinstance(result, dict))
    test("analyze has aesthetic_score", 'aesthetic_score' in result)
    test("analyze has style_classification", 'style_classification' in result)
    test("analyze has composition_analysis", 'composition_analysis' in result)
    test("analyze has color_analysis", 'color_analysis' in result)
    test("analyze has lighting_analysis", 'lighting_analysis' in result)
    test("analyze has top_3_improvements", 'top_3_improvements' in result)
    test("analyze has dimensions", 'dimensions' in result)
    test("aesthetic_score is 0-10", 0 <= result['aesthetic_score'] <= 10)
    test("composition has balance", 'balance' in result['composition_analysis'])
    test("composition has symmetry", 'symmetry' in result['composition_analysis'])
    test("composition has rule_of_thirds_score", 'rule_of_thirds_score' in result['composition_analysis'])
    test("composition has leading_lines", 'leading_lines' in result['composition_analysis'])
    test("color has harmony_type", 'harmony_type' in result['color_analysis'])
    test("color has harmony_score", 'harmony_score' in result['color_analysis'])
    test("color has moods", 'moods' in result['color_analysis'])
    test("style has at least 1 match", len(result['style_classification']) >= 1)
    print(f"  🏆 Aesthetic Score: {result['aesthetic_score']}/10")
    print(f"  🎨 Styles: {[s['style'] for s in result['style_classification']]}")
    print(f"  🎨 Color Harmony: {result['color_analysis']['harmony_type']} ({result['color_analysis']['harmony_score']}/10)")
    print(f"  ⚖️  Balance: {result['composition_analysis']['balance']['score']}")
    print(f"  💡 Improvements: {len(result['top_3_improvements'])}")
    if result['composition_analysis']['symmetry']['overall'] >= 0:
        test("symmetry overall in range", 0 <= result['composition_analysis']['symmetry']['overall'] <= 1)
finally:
    os.unlink(temp_path)

# ============================================================
# TEST GROUP 15: Edge Cases
# ============================================================
print("\n1️⃣5️⃣  Edge Cases")
# Missing file
error_result = AestheticStyleAnalyzer.analyze("/tmp/nonexistent.png")
test("missing file returns dict", isinstance(error_result, dict))
test("missing file has error key", 'error' in error_result)

# Very small image (1x1)
small_result = AestheticStyleAnalyzer.analyze("/tmp/nonexistent.png")
# Already tested above

# All-black image
test("all-black image classification",
     AestheticStyleAnalyzer.classify_color((0, 0, 0)) == "black")

# All-white
test("all-white image classification",
     AestheticStyleAnalyzer.classify_color((255, 255, 255)) == "white")

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*55}")
print(f"📊 Results: {passed}/{passed+failed} passed", end="")
if failed > 0:
    print(f", {failed} FAILED ❌")
else:
    print(f" — ALL PASSED ✅")
