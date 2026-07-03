# Test file for PlaylistOptimizer — imports the class directly, not the full module
import json
import sys
sys.path.insert(0, '/Users/averylemonflower/Desktop/Apify-Actors/templates/playlist-optimizer')

# Extract the class from the module file directly (skip apify import)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "playlist_optimizer",
    "/Users/averylemonflower/Desktop/Apify-Actors/templates/playlist-optimizer/main.py"
)

# First let's parse the file and extract just the class
source = open(spec.origin).read()

# Create a clean module with the class defined but without the apify import
# We'll exec the class definition block
class_code = []
capture = False
brace_count = 0
for line in source.split('\n'):
    if line.strip().startswith('class PlaylistOptimizer'):
        capture = True
        brace_count = line.count('{') - line.count('}')
    if capture:
        class_code.append(line)
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0 and capture and len(class_code) > 1:
            break

exec('\n'.join(class_code))

# Test data
test_tracks = [
    {'title': 'Gentle Dawn', 'artist': 'OWL', 'energy': 0.2, 'mood': 'calm'},
    {'title': 'Storm Rising', 'artist': 'OWL', 'energy': 0.8, 'mood': 'intense'},
    {'title': 'Deep Waters', 'artist': 'OWL', 'energy': 0.4, 'mood': 'melancholic'},
    {'title': 'Solar Flare', 'artist': 'OWL', 'energy': 0.9, 'mood': 'powerful'},
    {'title': 'Forest Path', 'artist': 'OWL', 'energy': 0.3, 'mood': 'serene'},
    {'title': 'City Pulse', 'artist': 'OWL', 'energy': 0.7, 'mood': 'upbeat'},
]

errors = 0

# Test 1: All strategies return results
for strategy in ['energy_flow', 'build_up', 'wind_down', 'alternating', 'mood_clusters']:
    result, meta = PlaylistOptimizer.optimize(test_tracks, strategy)
    assert len(result) == 6, f'{strategy}: Expected 6 tracks, got {len(result)}'
    assert 'avg_transition_smoothness' in meta, f'{strategy}: Missing smoothness'
    assert meta['total_tracks'] == 6, f'{strategy}: Wrong track count'
    print(f'✅ {strategy}: smoothness={meta["avg_transition_smoothness"]}')

# Test 2: build_up orders by energy ascending
result, meta = PlaylistOptimizer.optimize(test_tracks, 'build_up')
energies = [t['energy'] for t in result]
assert energies == sorted(energies), 'build_up: tracks not sorted by energy ascending'
print(f'✅ build_up: energies ascending = {energies}')

# Test 3: wind_down orders by energy descending
result, meta = PlaylistOptimizer.optimize(test_tracks, 'wind_down')
energies = [t['energy'] for t in result]
assert energies == sorted(energies, reverse=True), 'wind_down: tracks not sorted by energy descending'
print(f'✅ wind_down: energies descending = {energies}')

# Test 4: Single track returns as-is
result, meta = PlaylistOptimizer.optimize([test_tracks[0]], 'energy_flow')
assert len(result) == 1
print('✅ Single track: handled correctly')

# Test 5: Empty list
result, meta = PlaylistOptimizer.optimize([], 'energy_flow')
assert len(result) == 0
print('✅ Empty list: handled correctly')

# Test 6: Transition scores are 0-1
result, meta = PlaylistOptimizer.optimize(test_tracks, 'energy_flow')
for t in meta.get('transitions', []):
    assert 0 <= t['score'] <= 1, f'Transition score out of range: {t}'
print(f'✅ All transition scores in [0,1] range')

# Test 7: Energy arc building
tracks = [
    {'title': 'A', 'artist': 'X', 'energy': 0.1, 'mood': 'calm'},
    {'title': 'B', 'artist': 'X', 'energy': 0.5, 'mood': 'moderate'},
    {'title': 'C', 'artist': 'X', 'energy': 0.9, 'mood': 'intense'},
]
result, meta = PlaylistOptimizer.optimize(tracks, 'build_up')
arc = meta['energy_arc']
assert arc['pattern'] == 'building', f"Expected building, got {arc['pattern']}"
print(f'✅ Energy arc correct: {arc["pattern"]}')

# Test 8: mood_compatibility
assert PlaylistOptimizer.mood_compatibility('calm', 'calm') == 1.0, 'Same mood should be 1.0'
assert PlaylistOptimizer.mood_compatibility('sad', 'melancholic') >= 0.8, 'Compatible mood too low'
assert PlaylistOptimizer.mood_compatibility('upbeat', 'sad') <= 0.5, 'Incompatible mood too high'
print('✅ Mood compatibility scoring correct')

# Test 9: energy_distance
assert PlaylistOptimizer.energy_distance(0.2, 0.8) == 0.6
assert PlaylistOptimizer.energy_distance(0.5, 0.5) == 0.0
print('✅ Energy distance correct')

print(f'\n🎉 All tests passed! (0 errors)')
