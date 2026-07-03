"""
Album Art Analyzer — Apify Actor
==================================
Analyzes album cover images and returns aesthetic scores:
- Color harmony (complementary, analogous, monochrome, triadic)
- Visual contrast (brightness range, color variance)
- Composition balance (rule of thirds score, symmetry)
- Mood palette (dominant colors mapped to emotional associations)

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms. It uses only
Pillow for image analysis and returns generic aesthetic descriptions.
"""

import json
import os
import tempfile
import urllib.request
from collections import Counter
from typing import Optional

from apify import Actor
from PIL import Image
import numpy as np


class AlbumArtAnalyzer:
    """Lightweight image analysis for album art aesthetics."""

    # Common color-to-mood mappings
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

        # Achromatic check
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

        # Normalize
        if max_val == 0:
            return 'black'

        rn = r / max_val
        gn = g / max_val
        bn = b / max_val

        # Dominant channel heuristics
        if rn > 0.8 and gn < 0.6 and bn < 0.6:
            return 'red'
        elif rn > 0.8 and gn > 0.5 and bn < 0.3:
            return 'orange'
        elif rn > 0.8 and gn > 0.8 and bn < 0.3:
            return 'yellow'
        elif gn > 0.8 and rn < 0.6 and bn < 0.6:
            return 'green'
        elif bn > 0.8 and rn < 0.6 and gn < 0.6:
            return 'blue'
        elif rn > 0.6 and gn > 0.2 and bn > 0.6:
            return 'purple'
        elif rn > 0.8 and gn > 0.5 and bn > 0.6:
            return 'pink'
        elif rn > 0.5 and gn > 0.4 and bn < 0.3:
            return 'brown'
        else:
            # Fallback: find closest named color
            named = {
                'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
                'yellow': (255, 255, 0), 'purple': (128, 0, 128),
                'orange': (255, 165, 0), 'pink': (255, 192, 203),
            }
            distances = {name: sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, target))
                        for name, target in named.items()}
            return min(distances, key=distances.get)

    @staticmethod
    def analyze_harmony(colors):
        """Analyze color harmony from dominant colors."""
        if len(colors) < 2:
            return 'monochrome'

        color_names = [AlbumArtAnalyzer.classify_color(c) for c in colors[:5]]

        # Check for complementary pairs
        complements = [('red', 'green'), ('blue', 'orange'), ('purple', 'yellow')]
        for c1, c2 in complements:
            if c1 in color_names and c2 in color_names:
                return 'complementary'

        # Check analogous (similar hues)
        warm = {'red', 'orange', 'yellow', 'pink'}
        cool = {'blue', 'green', 'purple'}
        warm_count = sum(1 for c in color_names if c in warm)
        cool_count = sum(1 for c in color_names if c in cool)

        if warm_count >= 2:
            return 'analogous_warm'
        elif cool_count >= 2:
            return 'analogous_cool'

        # Check for triadic
        if len(set(color_names)) >= 3:
            return 'triadic'

        return 'mixed'

    @staticmethod
    def analyze_balance(img_array):
        """Analyze compositional balance using luminance."""
        h, w, _ = img_array.shape
        gray = np.mean(img_array, axis=2)

        # Divide into quadrants
        mid_h, mid_w = h // 2, w // 2
        tl = np.mean(gray[:mid_h, :mid_w])
        tr = np.mean(gray[:mid_h, mid_w:])
        bl = np.mean(gray[mid_h:, :mid_w])
        br = np.mean(gray[mid_h:, mid_w:])

        quadrants = [tl, tr, bl, br]
        variance = float(np.std(quadrants))

        if variance < 30:
            return {'score': 'balanced', 'variance': round(variance, 1)}
        elif variance < 60:
            return {'score': 'moderately_imbalanced', 'variance': round(variance, 1)}
        else:
            return {'score': 'high_contrast', 'variance': round(variance, 1)}

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
        # Sample pixels
        flat = img_array.reshape(-1, 3)
        if len(flat) > 10000:
            indices = np.random.choice(len(flat), 10000, replace=False)
            flat = flat[indices]

        std_per_channel = np.std(flat, axis=0)
        mean_std = float(np.mean(std_per_channel))
        max_std = float(np.max(std_per_channel))

        if mean_std < 30:
            return 'low_diversity'
        elif mean_std < 60:
            return 'moderate_diversity'
        else:
            return 'high_diversity'

    @staticmethod
    def get_dominant_colors(img_array, n=5):
        """Extract dominant colors via simple quantization."""
        flat = img_array.reshape(-1, 3)

        # Downsample for speed
        if len(flat) > 20000:
            indices = np.random.choice(len(flat), 20000, replace=False)
            flat = flat[indices]

        # Quantize to reduce colors
        quantized = (flat // 32) * 32 + 16  # Reduce to ~8 levels per channel
        quantized = np.clip(quantized, 0, 255)

        # Count unique colors
        color_tuples = [tuple(c) for c in quantized]
        counter = Counter(color_tuples)
        dominant = counter.most_common(n)

        return [(list(rgb), count) for rgb, count in dominant]

    @staticmethod
    def analyze(file_path: str) -> dict:
        """Full analysis pipeline for a single image."""
        try:
            img = Image.open(file_path).convert('RGB')
        except Exception as e:
            return {'error': f'Could not open image: {str(e)}'}

        img_array = np.array(img)
        if img_array.ndim != 3:
            return {'error': 'Image must be RGB (3 channels)'}

        h, w, _ = img_array.shape
        aspect_ratio = round(w / h, 2)

        # Dominant colors
        dominant_colors = AlbumArtAnalyzer.get_dominant_colors(img_array, n=5)
        color_names = [AlbumArtAnalyzer.classify_color(rgb) for rgb, _ in dominant_colors]
        dominant_palette = [{'rgb': rgb, 'name': name, 'weight': round(count / sum(c for _, c in dominant_colors), 3)}
                           for (rgb, count), name in zip(dominant_colors, color_names)]

        # Harmony
        harmony = AlbumArtAnalyzer.analyze_harmony([rgb for rgb, _ in dominant_colors])

        # Balance
        balance = AlbumArtAnalyzer.analyze_balance(img_array)

        # Brightness
        brightness = AlbumArtAnalyzer.analyze_brightness(img_array)

        # Diversity
        diversity = AlbumArtAnalyzer.analyze_color_variance(img_array)

        # Moods from dominant colors
        moods = []
        for name in color_names[:3]:
            if name in AlbumArtAnalyzer.COLOR_MOODS:
                moods.extend(AlbumArtAnalyzer.COLOR_MOODS[name])
        moods = list(set(moods))

        # Build final tags
        tags = [harmony] + [brightness['brightness_level']] + [brightness['contrast_level']] + [diversity] + moods[:5]
        tags = list(set(tags))

        return {
            'tags': tags,
            'analysis': {
                'dimensions': {'width': w, 'height': h, 'aspect_ratio': aspect_ratio},
                'color_harmony': harmony,
                'composition': balance,
                'brightness': brightness,
                'color_diversity': diversity,
                'dominant_palette': dominant_palette,
                'moods': moods,
            },
        }


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        image_url = actor_input.get('imageUrl', '')
        image_path = actor_input.get('imagePath', '')

        if not image_url and not image_path:
            raise ValueError('Either imageUrl or imagePath must be provided')

        temp_file = None
        try:
            if image_url:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                image_path = temp_file.name
                urllib.request.urlretrieve(image_url, image_path)

            if not os.path.exists(image_path):
                raise FileNotFoundError(f'File not found: {image_path}')

            result = AlbumArtAnalyzer.analyze(image_path)

            if 'error' in result:
                raise RuntimeError(result['error'])

            result['filename'] = os.path.basename(image_url) if image_url else os.path.basename(image_path)

            await Actor.push_data(result)
            Actor.log.info(f"Analysis complete: {result['filename']} — {len(result['tags'])} tags")

        finally:
            if temp_file:
                os.unlink(temp_file.name)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
