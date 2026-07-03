"""
Playlist Optimizer — Apify Actor
==================================
Orders a list of tracks for optimal emotional flow.

Input: JSON array of tracks, each with {title, artist, duration, energy, mood}
Output: Reordered playlist with energy arc analysis and transition scores.

RESTRICTED: This actor is a standalone tool. No OWL factory code.
"""

import json
from typing import Optional
from apify import Actor


class PlaylistOptimizer:
    """Playlist ordering optimization using energy arcs and mood transitions."""

    MOOD_COMPATIBILITY = {
        'upbeat': ['energetic', 'happy', 'bright', 'playful'],
        'energetic': ['upbeat', 'powerful', 'intense', 'dramatic'],
        'happy': ['upbeat', 'warm', 'playful', 'bright'],
        'melancholic': ['sad', 'dark', 'mellow', 'serene'],
        'sad': ['melancholic', 'dark', 'serene', 'mellow'],
        'calm': ['serene', 'mellow', 'soft', 'warm'],
        'serene': ['calm', 'mellow', 'soft', 'gentle'],
        'dark': ['melancholic', 'intense', 'moody', 'dramatic'],
        'bright': ['upbeat', 'happy', 'playful', 'energetic'],
        'warm': ['happy', 'calm', 'soft', 'romantic'],
        'intense': ['dramatic', 'powerful', 'energetic', 'dark'],
        'dramatic': ['intense', 'powerful', 'moody', 'dark'],
        'playful': ['upbeat', 'happy', 'bright', 'quirky'],
        'mellow': ['calm', 'soft', 'melancholic', 'serene'],
        'soft': ['calm', 'mellow', 'gentle', 'warm'],
        'powerful': ['intense', 'dramatic', 'upbeat', 'energetic'],
        'gentle': ['soft', 'calm', 'serene', 'warm'],
        'moody': ['dark', 'melancholic', 'intense', 'dramatic'],
        'romantic': ['warm', 'soft', 'gentle', 'calm'],
        'quirky': ['playful', 'bright', 'upbeat', 'happy'],
    }

    @staticmethod
    def parse_param(value, param_name):
        """Safely parse a parameter that might be string or number."""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return 0.5  # default

    @staticmethod
    def mood_compatibility(mood1, mood2):
        """Score how well two moods transition (0-1)."""
        if mood1 == mood2:
            return 1.0
        if mood1 in PlaylistOptimizer.MOOD_COMPATIBILITY:
            compatible = PlaylistOptimizer.MOOD_COMPATIBILITY[mood1]
            if mood2 in compatible:
                return 0.8
        if mood2 in PlaylistOptimizer.MOOD_COMPATIBILITY:
            compatible = PlaylistOptimizer.MOOD_COMPATIBILITY[mood2]
            if mood1 in compatible:
                return 0.8
        return 0.3

    @staticmethod
    def energy_distance(e1, e2):
        """Energy change between tracks (smaller = smoother)."""
        return abs(e1 - e2)

    @staticmethod
    def transition_score(track_a, track_b):
        """Calculate smoothness of transition between two tracks (0-1)."""
        energy_a = PlaylistOptimizer.parse_param(track_a.get('energy', 0.5), 'energy')
        energy_b = PlaylistOptimizer.parse_param(track_b.get('energy', 0.5), 'energy')

        mood_a = track_a.get('mood', 'neutral')
        mood_b = track_b.get('mood', 'neutral')

        mood_score = PlaylistOptimizer.mood_compatibility(mood_a, mood_b)
        energy_diff = PlaylistOptimizer.energy_distance(energy_a, energy_b)

        # Closer energy = smoother
        energy_score = max(0, 1.0 - energy_diff)

        # Combine: mood matters more than energy
        score = (mood_score * 0.6) + (energy_score * 0.4)
        return round(score, 3)

    @staticmethod
    def build_energy_arc(tracks):
        """Build and describe the energy arc of the playlist."""
        if not tracks:
            return {'pattern': 'empty', 'description': 'No tracks'}

        energies = []
        for t in tracks:
            energy = PlaylistOptimizer.parse_param(t.get('energy', 0.5), 'energy')
            energies.append(energy)

        start = energies[0]
        end = energies[-1]
        mid = sum(energies) / len(energies)
        peak = max(energies)
        valley = min(energies)

        total_change = sum(abs(energies[i] - energies[i-1]) for i in range(1, len(energies)))
        avg_change = total_change / len(energies) if len(energies) > 1 else 0

        # Classify arc pattern
        if end > start + 0.3:
            pattern = 'building'  # ends higher than starts
        elif start > end + 0.3:
            pattern = 'descending'  # starts higher than ends
        elif peak - valley < 0.3:
            pattern = 'uniform'
        else:
            pattern = 'dynamic'

        return {
            'pattern': pattern,
            'start_energy': round(start, 3),
            'end_energy': round(end, 3),
            'average_energy': round(mid, 3),
            'peak_energy': round(peak, 3),
            'valley_energy': round(valley, 3),
            'total_energy_change': round(total_change, 3),
            'avg_transition_change': round(avg_change, 3),
        }

    @staticmethod
    def optimize(tracks, strategy='energy_flow'):
        """Optimize playlist order based on strategy.

        Strategies:
        - 'energy_flow': Smooth energy arc (default)
        - 'mood_clusters': Group similar moods
        - 'build_up': Start calm, end intense
        - 'wind_down': Start intense, end calm
        - 'alternating': Alternate high/low energy
        """
        if not tracks or len(tracks) < 2:
            return tracks, {'strategy': strategy, 'message': 'Need 2+ tracks for optimization'}

        if strategy == 'build_up':
            sorted_tracks = sorted(tracks, key=lambda t: PlaylistOptimizer.parse_param(t.get('energy', 0.5), 'energy'))
        elif strategy == 'wind_down':
            sorted_tracks = sorted(tracks, key=lambda t: PlaylistOptimizer.parse_param(t.get('energy', 0.5), 'energy'), reverse=True)
        elif strategy == 'mood_clusters':
            # Group by mood
            mood_groups = {}
            for t in tracks:
                mood = t.get('mood', 'unknown')
                if mood not in mood_groups:
                    mood_groups[mood] = []
                mood_groups[mood].append(t)
            sorted_tracks = []
            for mood, group in mood_groups.items():
                sorted_tracks.extend(group)
        elif strategy == 'alternating':
            sorted_by_energy = sorted(tracks, key=lambda t: PlaylistOptimizer.parse_param(t.get('energy', 0.5), 'energy'))
            low = sorted_by_energy[:len(sorted_by_energy)//2]
            high = sorted_by_energy[len(sorted_by_energy)//2:]
            sorted_tracks = []
            l, h = 0, 0
            for i in range(len(tracks)):
                if i % 2 == 0 and h < len(high):
                    sorted_tracks.append(high[h])
                    h += 1
                elif l < len(low):
                    sorted_tracks.append(low[l])
                    l += 1
                else:
                    sorted_tracks.append(tracks[i])
        else:  # energy_flow (default)
            # Greedy nearest-neighbor ordering for smooth transitions
            remaining = list(tracks)
            sorted_tracks = [remaining.pop(0)]
            while remaining:
                current = sorted_tracks[-1]
                best_idx = 0
                best_score = -1
                for i, candidate in enumerate(remaining):
                    score = PlaylistOptimizer.transition_score(current, candidate)
                    if score > best_score:
                        best_score = score
                        best_idx = i
                sorted_tracks.append(remaining.pop(best_idx))

        # Calculate transition scores for the optimized order
        transitions = []
        total_smoothness = 0
        for i in range(len(sorted_tracks) - 1):
            score = PlaylistOptimizer.transition_score(sorted_tracks[i], sorted_tracks[i + 1])
            transitions.append({'from': sorted_tracks[i].get('title', '?'), 
                               'to': sorted_tracks[i + 1].get('title', '?'),
                               'score': score})
            total_smoothness += score

        avg_smoothness = total_smoothness / len(transitions) if transitions else 1.0
        energy_arc = PlaylistOptimizer.build_energy_arc(sorted_tracks)

        return sorted_tracks, {
            'strategy': strategy,
            'total_tracks': len(sorted_tracks),
            'avg_transition_smoothness': round(avg_smoothness, 3),
            'energy_arc': energy_arc,
            'transitions': transitions[:50],  # limit output size
        }


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        tracks = actor_input.get('tracks', [])
        strategy = actor_input.get('strategy', 'energy_flow')

        if not tracks:
            raise ValueError('Must provide at least 2 tracks in the "tracks" array')

        optimized, metadata = PlaylistOptimizer.optimize(tracks, strategy)

        result = {
            'input_count': len(tracks),
            'strategy': strategy,
            'optimized_order': [{
                'title': t.get('title', 'Unknown'),
                'artist': t.get('artist', 'Unknown'),
                'energy': PlaylistOptimizer.parse_param(t.get('energy', 0.5), 'energy'),
                'mood': t.get('mood', 'unknown'),
                'position': i + 1,
            } for i, t in enumerate(optimized)],
            'analysis': metadata,
        }

        await Actor.push_data(result)
        Actor.log.info(f"Playlist optimized: {len(tracks)} tracks via {strategy} strategy")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
