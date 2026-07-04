"""
Test suite for PlaylistOptimizer — pure logic tests (no apify SDK needed).
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Extract PlaylistOptimizer class from main.py (skip apify import)
import re
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")) as f:
    source = f.read()

class_match = re.search(r'class PlaylistOptimizer:.*?(?=\nasync def main|\nif __name__)', source, re.DOTALL)
import_lines = "\n".join([
    line for line in source.split('\n')
    if line.startswith('import ') or line.startswith('from ')
    if 'apify' not in line and 'asyncio' not in line
])

namespace = {}
exec(import_lines + "\n\n" + class_match.group(0), namespace)
PlaylistOptimizer = namespace['PlaylistOptimizer']

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

def make_track(title, energy=0.5, mood="neutral", artist="Test", duration=180, genre="pop"):
    return {"title": title, "artist": artist, "energy": energy, "mood": mood, "duration": duration, "genre": genre}

print("\n📋 PlaylistOptimizer Unit Tests")
print("=" * 50)

# Test 1: parse_param
test("parse_param from float", PlaylistOptimizer.parse_param(0.7, 'energy') == 0.7)
test("parse_param from int", PlaylistOptimizer.parse_param(5, 'energy') == 5.0)
test("parse_param from string", PlaylistOptimizer.parse_param("0.8", 'energy') == 0.8)
test("parse_param invalid string defaults", PlaylistOptimizer.parse_param("abc", 'energy') == 0.5)

# Test 2: mood_compatibility
test("mood_compatibility same mood", PlaylistOptimizer.mood_compatibility("upbeat", "upbeat") == 1.0)
test("mood_compatibility compatible", PlaylistOptimizer.mood_compatibility("upbeat", "energetic") == 0.8)
test("mood_compatibility compatible reverse", PlaylistOptimizer.mood_compatibility("energetic", "upbeat") == 0.8)
test("mood_compatibility unrelated", PlaylistOptimizer.mood_compatibility("upbeat", "melancholic") == 0.3)

# Test 3: energy_distance
test("energy_distance same", PlaylistOptimizer.energy_distance(0.5, 0.5) == 0)
test("energy_distance different", abs(PlaylistOptimizer.energy_distance(0.2, 0.8) - 0.6) < 0.001)

# Test 4: transition_score
test("transition_score perfect match (same mood+energy)", 
     PlaylistOptimizer.transition_score(make_track("A", energy=0.5, mood="calm"), 
                                       make_track("B", energy=0.5, mood="calm")) == 1.0)
test("transition_score clash (different mood+energy)", 
     0 <= PlaylistOptimizer.transition_score(make_track("A", energy=0.1, mood="melancholic"), 
                                            make_track("B", energy=0.9, mood="upbeat")) <= 1.0)

# Test 5: build_energy_arc
empty_arc = PlaylistOptimizer.build_energy_arc([])
test("build_energy_arc empty", empty_arc['pattern'] == "empty")

single_arc = PlaylistOptimizer.build_energy_arc([make_track("A", energy=0.5)])
test("build_energy_arc single", single_arc['pattern'] != "empty")

tracks = [make_track("A", energy=0.2), make_track("B", energy=0.8), make_track("C", energy=0.9)]
arc = PlaylistOptimizer.build_energy_arc(tracks)
test("build_energy_arc has pattern", 'pattern' in arc)
test("build_energy_arc has start_energy", 'start_energy' in arc)
test("build_energy_arc has peak_energy", 'peak_energy' in arc)
test("build_energy_arc building pattern", arc['pattern'] == "building")

# Test 6: optimize with various strategies
tracks_5 = [
    make_track("Song A", energy=0.1, mood="melancholic"),
    make_track("Song B", energy=0.9, mood="upbeat"),
    make_track("Song C", energy=0.3, mood="calm"),
    make_track("Song D", energy=0.8, mood="energetic"),
    make_track("Song E", energy=0.5, mood="happy"),
]

# Single track
single_track = [make_track("Only", energy=0.5)]
result_single, meta_single = PlaylistOptimizer.optimize(single_track)
test("optimize single track returns track", len(result_single) == 1)
test("optimize single track message", 'Need 2+ tracks' in meta_single['message'])

# Default energy_flow
result_flow, meta_flow = PlaylistOptimizer.optimize(tracks_5)
test("optimize energy_flow returns all tracks", len(result_flow) == 5)
test("optimize energy_flow has strategy", meta_flow['strategy'] == "energy_flow")
test("optimize energy_flow has avg_smoothness", 'avg_transition_smoothness' in meta_flow)
test("optimize energy_flow has energy_arc", 'energy_arc' in meta_flow)
test("optimize energy_flow has transitions", len(meta_flow['transitions']) == 4)
test("optimize energy_flow avg_smoothness >= 0", meta_flow['avg_transition_smoothness'] >= 0)

# Build up
result_up, meta_up = PlaylistOptimizer.optimize(tracks_5, 'build_up')
test("optimize build_up has correct strategy", meta_up['strategy'] == "build_up")
# First track should be lowest energy, last should be highest
first_energy = PlaylistOptimizer.parse_param(result_up[0].get('energy', 0.5), 'energy')
last_energy = PlaylistOptimizer.parse_param(result_up[-1].get('energy', 0.5), 'energy')
test("optimize build_up first < last", first_energy <= last_energy)

# Wind down
result_down, meta_down = PlaylistOptimizer.optimize(tracks_5, 'wind_down')
first_down = PlaylistOptimizer.parse_param(result_down[0].get('energy', 0.5), 'energy')
last_down = PlaylistOptimizer.parse_param(result_down[-1].get('energy', 0.5), 'energy')
test("optimize wind_down first > last", first_down >= last_down)

# Mood clusters
result_mood, meta_mood = PlaylistOptimizer.optimize(tracks_5, 'mood_clusters')
test("optimize mood_clusters has correct strategy", meta_mood['strategy'] == "mood_clusters")
test("optimize mood_clusters returns all tracks", len(result_mood) == 5)

# Alternating
result_alt, meta_alt = PlaylistOptimizer.optimize(tracks_5, 'alternating')
test("optimize alternating has correct strategy", meta_alt['strategy'] == "alternating")
test("optimize alternating returns all tracks", len(result_alt) == 5)

# Test 7: edge cases
test("optimize empty list", 
     PlaylistOptimizer.optimize([])[1]['message'] == 'Need 2+ tracks for optimization')

test("optimize missing energy field defaults to 0.5", 
     PlaylistOptimizer.parse_param(
         PlaylistOptimizer.optimize([{"title": "A", "mood": "calm"}, {"title": "B", "mood": "upbeat"}])[0][0].get('energy', 0.5), 
         'energy') == 0.5)

print(f"\n{'='*50}")
print(f"📊 Results: {passed}/{passed+failed} passed", end="")
if failed > 0:
    print(f", {failed} FAILED ❌")
else:
    print(f" — ALL PASSED ✅")
