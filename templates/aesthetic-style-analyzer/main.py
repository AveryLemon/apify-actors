"""
Aesthetic / Style Analysis Actor — Apify Actor
===============================================
Analyzes images for aesthetic quality, composition rules, visual style
classification, and color harmony scoring.

Outputs:
- aesthetic_score (0-10): Overall aesthetic quality
- composition_analysis: Rule of thirds, symmetry, leading lines, balance
- style_classification: Visual style tags (minimalist, grunge, vintage, etc.)
- color_harmony: Harmony type + score (0-10)
- lighting_quality: Darkness/brightness distribution
- top_3_improvements: Actionable suggestions to improve the image

RESTRICTED: This actor is a standalone tool. It does NOT contain any of OWL's
factory pipelines, brand strategy, or proprietary algorithms. It uses only
Pillow and numpy for image analysis and returns generic aesthetic judgments.

Usage:
    Input:  {"imageUrl": "https://example.com/photo.jpg"}
    Output: {"filename": "photo.jpg", "aesthetic_score": 7.2, ...}
"""

import json
import math
import os
import tempfile
import urllib.request
from collections import Counter
from typing import Optional

from apify import Actor
from PIL import Image, ImageStat, ImageFilter
import numpy as np


class AestheticStyleAnalyzer:
    """Analyze images for aesthetic quality, composition, and visual style."""

    # Style archetypes and their visual signatures
    STYLE_PROFILES = {
        'minimalist': {
            'brightness_level': 'bright',
            'color_diversity': 'low_diversity',
            'contrast': ['low_contrast', 'moderate_contrast'],
            'color_temperatures': ['neutral'],
        },
        'grunge': {
            'brightness_level': 'dark',
            'color_diversity': 'moderate_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['warm', 'neutral'],
        },
        'vintage': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'moderate_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['warm'],
        },
        'clean_modern': {
            'brightness_level': 'bright',
            'color_diversity': 'low_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'dark_moody': {
            'brightness_level': 'dark',
            'color_diversity': 'low_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'nature_organic': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'high_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['warm'],
        },
        'vibrant_colorful': {
            'brightness_level': 'bright',
            'color_diversity': 'high_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['warm', 'cool'],
        },
        'monochrome': {
            'brightness_level': 'mid_tone',
            'color_diversity': 'low_diversity',
            'contrast': ['moderate_contrast'],
            'color_temperatures': ['neutral'],
        },
        'noir': {
            'brightness_level': 'dark',
            'color_diversity': 'low_diversity',
            'contrast': ['high_contrast'],
            'color_temperatures': ['cool', 'neutral'],
        },
        'pastel': {
            'brightness_level': 'bright',
            'color_diversity': 'moderate_diversity',
            'contrast': ['low_contrast'],
            'color_temperatures': ['cool', 'warm'],
        },
    }

    # Common color-to-mood mappings (shared with album-art-analyzer pattern)
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

    # Complementary pairs for harmony analysis
    COMPLEMENTS = {
        'red': 'green', 'green': 'red',
        'blue': 'orange', 'orange': 'blue',
        'purple': 'yellow', 'yellow': 'purple',
        'pink': 'teal', 'teal': 'pink',
    }

    @staticmethod
    def classify_color(rgb):
        """Map an RGB value to a named color."""
        r, g, b = rgb
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

        if max_val == 0:
            return 'black'

        rn = r / max_val
        gn = g / max_val
        bn = b / max_val

        if rn > 0.8 and gn > 0.8 and bn < 0.3:
            return 'yellow'
        elif rn > 0.8 and gn < 0.4 and bn < 0.4:
            return 'red'
        elif rn > 0.8 and gn > 0.5 and bn > 0.6:
            return 'pink'
        elif rn > 0.8 and gn > 0.4 and bn < 0.3:
            return 'orange'
        elif gn > 0.8 and rn < 0.6 and bn < 0.6:
            return 'green'
        elif bn > 0.8 and rn < 0.6 and gn < 0.6:
            return 'blue'
        elif rn > 0.6 and gn > 0.2 and bn > 0.6:
            return 'purple'
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
    def get_dominant_colors(img_array, n=5):
        """Extract dominant colors via simple quantization."""
        flat = img_array.reshape(-1, 3)
        if len(flat) > 20000:
            indices = np.random.choice(len(flat), 20000, replace=False)
            flat = flat[indices]

        # Quantize to ~8 levels per channel
        quantized = (flat // 32) * 32 + 16
        quantized = np.clip(quantized, 0, 255)

        color_tuples = [tuple(c) for c in quantized]
        counter = Counter(color_tuples)
        dominant = counter.most_common(n)

        return [(list(rgb), count) for rgb, count in dominant]

    @staticmethod
    def assess_color_temperature(img_array):
        """Determine if the image is warm-toned, cool-toned, or neutral."""
        r_channel = img_array[:, :, 0].astype(float)
        b_channel = img_array[:, :, 2].astype(float)
        ratio = np.mean(r_channel) / max(np.mean(b_channel), 1.0)

        if ratio > 1.15:
            return 'warm'
        elif ratio < 0.85:
            return 'cool'
        else:
            return 'neutral'

    @staticmethod
    def analyze_harmony(colors):
        """Analyze color harmony from dominant colors."""
        if len(colors) < 2:
            return 'monochrome'

        color_names = [AestheticStyleAnalyzer.classify_color(c) for c in colors[:5]]

        # Check for complementary pairs
        for c1, c2 in [('red', 'green'), ('blue', 'orange'), ('purple', 'yellow'),
                        ('pink', 'teal'), ('teal', 'pink')]:
            if c1 in color_names and c2 in color_names:
                return 'complementary'

        # Check analogous (similar hues)
        warm = {'red', 'orange', 'yellow', 'pink', 'brown'}
        cool = {'blue', 'green', 'purple'}
        warm_count = sum(1 for c in color_names if c in warm)
        cool_count = sum(1 for c in color_names if c in cool)

        if warm_count >= 2:
            return 'analogous_warm'
        elif cool_count >= 2:
            return 'analogous_cool'

        if len(set(color_names)) >= 3:
            return 'triadic'

        return 'mixed'

    @staticmethod
    def score_harmony(harmony_type):
        """Score a harmony type from 0-10."""
        scores = {
            'complementary': 8.5,
            'analogous_warm': 7.0,
            'analogous_cool': 7.0,
            'triadic': 9.0,
            'monochrome': 6.0,
            'mixed': 5.0,
        }
        return scores.get(harmony_type, 5.0)

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
        flat = img_array.reshape(-1, 3)
        if len(flat) > 10000:
            indices = np.random.choice(len(flat), 10000, replace=False)
            flat = flat[indices]

        std_per_channel = np.std(flat, axis=0)
        mean_std = float(np.mean(std_per_channel))

        if mean_std < 30:
            return 'low_diversity'
        elif mean_std < 55:
            return 'moderate_diversity'
        else:
            return 'high_diversity'

    @staticmethod
    def analyze_balance(img_array):
        """Analyze compositional balance using luminance distribution."""
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

        if variance < 25:
            balance_score = 'balanced'
            balance_value = 8.0
        elif variance < 50:
            balance_score = 'moderately_imbalanced'
            balance_value = 5.5
        else:
            balance_score = 'high_contrast_imbalance'
            balance_value = 4.0

        # Determine which quadrant is dominant
        max_quad = max(range(4), key=lambda i: quadrants[i])
        quad_names = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        dominant_quadrant = quad_names[max_quad]

        return {
            'score': balance_score,
            'value': balance_value,
            'variance': round(variance, 1),
            'dominant_quadrant': dominant_quadrant,
        }

    @staticmethod
    def analyze_rule_of_thirds(img_array):
        """Score how well the image follows the rule of thirds."""
        h, w, _ = img_array.shape
        gray = np.mean(img_array, axis=2)

        # Third lines (both horizontal and vertical)
        third_h = [h // 3, 2 * h // 3]
        third_w = [w // 3, 2 * w // 3]

        # Measure variance along third lines vs center
        third_line_pixels = []
        for y in third_h:
            y = min(y, h - 1)
            start_x = max(0, w // 3)
            end_x = min(w, 2 * w // 3)
            third_line_pixels.extend(gray[y, start_x:end_x])

        for x in third_w:
            x = min(x, w - 1)
            start_y = max(0, h // 3)
            end_y = min(h, 2 * h // 3)
            third_line_pixels.extend(gray[start_y:end_y, x])

        if len(third_line_pixels) < 10:
            return 0.0

        # High variance along third lines = good composition
        variance = float(np.std(third_line_pixels))
        score = min(variance / 60.0, 1.0)

        return round(score, 2)

    @staticmethod
    def analyze_symmetry(img_array):
        """Measure horizontal and vertical symmetry."""
        h, w, _ = img_array.shape
        gray = np.mean(img_array, axis=2)

        # Vertical symmetry (left vs right flip)
        mid_w = w // 2
        if mid_w < 10:
            return 0.5
        left = gray[:, :mid_w]
        right = gray[:, mid_w:2 * mid_w]
        # Flip right to compare
        right_flipped = np.fliplr(right)
        # Resize if needed
        min_w = min(left.shape[1], right_flipped.shape[1])
        left = left[:, :min_w]
        right_flipped = right_flipped[:, :min_w]
        vert_diff = float(np.mean((left - right_flipped) ** 2))

        # Horizontal symmetry (top vs bottom)
        mid_h = h // 2
        if mid_h < 10:
            return 0.5
        top = gray[:mid_h, :]
        bottom = gray[mid_h:2 * mid_h, :]
        bottom_flipped = np.flipud(bottom)
        min_h = min(top.shape[0], bottom_flipped.shape[0])
        top = top[:min_h, :]
        bottom_flipped = bottom_flipped[:min_h, :]
        horiz_diff = float(np.mean((top - bottom_flipped) ** 2))

        # Normalize to 0-1 score (lower diff = more symmetric)
        vert_score = max(0, 1.0 - vert_diff / 10000.0)
        horiz_score = max(0, 1.0 - horiz_diff / 10000.0)

        return {
            'vertical_symmetry': round(vert_score, 2),
            'horizontal_symmetry': round(horiz_score, 2),
            'overall': round((vert_score + horiz_score) / 2, 2),
        }

    @staticmethod
    def analyze_leading_lines(img_array):
        """Detect potential leading lines via edge detection."""
        gray_img = np.mean(img_array, axis=2).astype(np.uint8)
        pil_img = Image.fromarray(gray_img)

        # Apply edge detection
        edges = pil_img.filter(ImageFilter.FIND_EDGES)
        edge_array = np.array(edges)

        # Ratio of edge pixels to total
        total_pixels = edge_array.size
        edge_pixels = np.sum(edge_array > 30)
        edge_density = edge_pixels / max(total_pixels, 1)

        # Score: some edges = good (compositional structure)
        # No edges = flat/boring. Too many = noisy.
        if edge_density < 0.01:
            leading_lines_score = 0.2  # Very few edges
            leading_lines_desc = 'very_few_edges'
        elif edge_density < 0.05:
            leading_lines_score = 0.7  # Moderate edges — good structure
            leading_lines_desc = 'moderate_edges'
        elif edge_density < 0.15:
            leading_lines_score = 0.9  # Rich edges — excellent structure
            leading_lines_desc = 'rich_edge_structure'
        elif edge_density < 0.3:
            leading_lines_score = 0.6  # Many edges — busy
            leading_lines_desc = 'busy_texture'
        else:
            leading_lines_score = 0.3  # Very busy — noisy
            leading_lines_desc = 'very_busy_noisy'

        return {
            'score': leading_lines_score,
            'description': leading_lines_desc,
            'edge_density': round(float(edge_density), 4),
        }

    @staticmethod
    def classify_style(brightness_info, color_diversity, color_temperature, balance_info):
        """Classify the image into one or more visual styles."""
        brightness = brightness_info['brightness_level']
        contrast = brightness_info['contrast_level']
        balance = balance_info['score']

        candidates = []
        for style, profile in AestheticStyleAnalyzer.STYLE_PROFILES.items():
            score = 0
            total_checks = 0

            # Brightness match
            if profile['brightness_level'] == brightness:
                score += 1
            total_checks += 1

            # Color diversity match
            if profile['color_diversity'] == color_diversity:
                score += 1
            total_checks += 1

            # Contrast match
            if contrast in profile['contrast']:
                score += 1
            total_checks += 1

            # Color temperature match
            temps = profile.get('color_temperatures', ['neutral'])
            if color_temperature in temps:
                score += 1
            total_checks += 1

            # Balance bonus
            if balance == 'balanced':
                if style in ('minimalist', 'clean_modern'):
                    score += 0.5
                    total_checks += 0.5

            confidence = score / max(total_checks, 1)
            if confidence >= 0.5:
                candidates.append((style, round(confidence, 2)))

        # Sort by confidence descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:3]

    @staticmethod
    def compute_aesthetic_score(brightness_info, color_diversity, balance_info,
                                symmetry_info, harmony_type, rule_of_thirds_score,
                                leading_lines_info, color_temperature):
        """Compute an overall aesthetic score (0-10)."""
        scores = []

        # Brightness & contrast (0-10)
        brightness = brightness_info['brightness_level']
        contrast = brightness_info['contrast_level']
        if brightness in ('mid_tone', 'bright') and contrast != 'low_contrast':
            scores.append(7.0)
        elif brightness == 'dark' and contrast == 'high_contrast':
            scores.append(8.0)  # Dramatic dark can be highly aesthetic
        else:
            scores.append(5.0)

        # Color diversity (0-10)
        if color_diversity == 'moderate_diversity':
            scores.append(7.5)  # Usually most aesthetically pleasing
        elif color_diversity == 'high_diversity':
            scores.append(6.5)
        else:
            scores.append(5.5)

        # Composition balance (0-10)
        scores.append(balance_info['value'])

        # Symmetry (0-10)
        scores.append(symmetry_info['overall'] * 10)

        # Color harmony (0-10)
        scores.append(AestheticStyleAnalyzer.score_harmony(harmony_type))

        # Rule of thirds (0-10)
        scores.append(rule_of_thirds_score * 10)

        # Leading lines structure (0-10)
        scores.append(leading_lines_info['score'] * 10)

        # Weighted average (balance and harmony matter more)
        weights = [0.10, 0.10, 0.20, 0.10, 0.20, 0.15, 0.15]
        weighted_score = sum(s * w for s, w in zip(scores, weights))

        return round(min(weighted_score, 10.0), 1)

    @staticmethod
    def generate_improvements(harmony_type, balance_info, brightness_info,
                              symmetry_info, rule_of_thirds_score, leading_lines_info):
        """Generate top 3 actionable improvements."""
        issues = []

        # Color harmony issues
        if harmony_type == 'mixed':
            issues.append({
                'issue': 'Color harmony could be improved',
                'suggestion': 'Consider using complementary or analogous color schemes. Reduce the number of competing hues.',
                'impact': 'high',
            })
        elif harmony_type == 'monochrome':
            issues.append({
                'issue': 'Monochrome palette may lack visual interest',
                'suggestion': 'Add a small accent of a complementary color to create focal points.',
                'impact': 'medium',
            })

        # Balance issues
        if balance_info['score'] != 'balanced':
            issues.append({
                'issue': f"Composition is {balance_info['score'].replace('_', ' ')}",
                'suggestion': f"The {balance_info['dominant_quadrant'].replace('_', ' ')} quadrant is visually heavier. "
                              "Consider shifting the main subject to balance the frame.",
                'impact': 'high',
            })

        # Symmetry issues
        if symmetry_info['overall'] < 0.4:
            issues.append({
                'issue': 'Asymmetry may be distracting',
                'suggestion': 'Use symmetry or intentional asymmetry with clear visual weight distribution.',
                'impact': 'medium',
            })

        # Rule of thirds
        if rule_of_thirds_score < 0.4:
            issues.append({
                'issue': 'Subject placement could be improved',
                'suggestion': 'Position the main subject along the rule of thirds grid lines for a more engaging composition.',
                'impact': 'medium',
            })

        # Lighting issues
        if brightness_info['brightness_level'] == 'dark' and brightness_info['contrast_level'] == 'low_contrast':
            issues.append({
                'issue': 'Image may be too dark with low contrast',
                'suggestion': 'Increase contrast or brighten midtones to reveal detail in shadows.',
                'impact': 'medium',
            })
        elif brightness_info['brightness_level'] == 'bright' and brightness_info['contrast_level'] == 'low_contrast':
            issues.append({
                'issue': 'Image appears flat or overexposed',
                'suggestion': 'Increase contrast or add deeper shadows for more dimensionality.',
                'impact': 'medium',
            })

        # Leading lines
        if leading_lines_info['description'] == 'very_few_edges':
            issues.append({
                'issue': 'Image lacks strong compositional structure',
                'suggestion': 'Incorporate leading lines, geometric patterns, or strong edges to guide the viewer\'s eye.',
                'impact': 'medium',
            })
        elif leading_lines_info['description'] == 'very_busy_noisy':
            issues.append({
                'issue': 'Image has excessive detail or noise',
                'suggestion': 'Simplify the composition. Remove clutter and focus on a single strong subject.',
                'impact': 'high',
            })

        # Sort by impact (high first) and return top 3
        impact_order = {'high': 0, 'medium': 1, 'low': 2}
        issues.sort(key=lambda x: impact_order.get(x['impact'], 99))
        return issues[:3]

    @staticmethod
    def analyze(file_path: str) -> dict:
        """Full aesthetic/style analysis pipeline for a single image."""
        try:
            img = Image.open(file_path).convert('RGB')
        except Exception as e:
            return {'error': f'Could not open image: {str(e)}'}

        img_array = np.array(img)
        if img_array.ndim != 3:
            return {'error': 'Image must be RGB (3 channels)'}

        h, w, _ = img_array.shape
        aspect_ratio = round(w / h, 2)

        # --- Lightweight analysis (all from a single pixel array) ---

        # 1. Dominant colors
        dominant_colors = AestheticStyleAnalyzer.get_dominant_colors(img_array, n=5)
        color_names = [AestheticStyleAnalyzer.classify_color(rgb) for rgb, _ in dominant_colors]
        dominant_palette = [
            {'rgb': rgb, 'name': name, 'weight': round(count / sum(c for _, c in dominant_colors), 3)}
            for (rgb, count), name in zip(dominant_colors, color_names)
        ]

        # 2. Color temperature
        color_temperature = AestheticStyleAnalyzer.assess_color_temperature(img_array)

        # 3. Color harmony
        harmony_type = AestheticStyleAnalyzer.analyze_harmony([rgb for rgb, _ in dominant_colors])
        harmony_score = AestheticStyleAnalyzer.score_harmony(harmony_type)

        # 4. Brightness & contrast
        brightness_info = AestheticStyleAnalyzer.analyze_brightness(img_array)

        # 5. Color diversity
        color_diversity = AestheticStyleAnalyzer.analyze_color_variance(img_array)

        # 6. Composition balance
        balance_info = AestheticStyleAnalyzer.analyze_balance(img_array)

        # 7. Symmetry
        symmetry_info = AestheticStyleAnalyzer.analyze_symmetry(img_array)

        # 8. Rule of thirds
        rule_of_thirds_score = AestheticStyleAnalyzer.analyze_rule_of_thirds(img_array)

        # 9. Leading lines
        leading_lines_info = AestheticStyleAnalyzer.analyze_leading_lines(img_array)

        # 10. Style classification
        style_matches = AestheticStyleAnalyzer.classify_style(
            brightness_info, color_diversity, color_temperature, balance_info
        )

        # 11. Overall aesthetic score
        aesthetic_score = AestheticStyleAnalyzer.compute_aesthetic_score(
            brightness_info, color_diversity, balance_info,
            symmetry_info, harmony_type, rule_of_thirds_score,
            leading_lines_info, color_temperature
        )

        # 12. Generate improvements
        improvements = AestheticStyleAnalyzer.generate_improvements(
            harmony_type, balance_info, brightness_info,
            symmetry_info, rule_of_thirds_score, leading_lines_info
        )

        # Build moods from dominant colors
        moods = []
        for name in color_names[:3]:
            if name in AestheticStyleAnalyzer.COLOR_MOODS:
                moods.extend(AestheticStyleAnalyzer.COLOR_MOODS[name])
        moods = list(set(moods))

        return {
            'aesthetic_score': aesthetic_score,
            'style_classification': [
                {'style': style, 'confidence': conf} for style, conf in style_matches
            ],
            'composition_analysis': {
                'balance': balance_info,
                'symmetry': symmetry_info,
                'rule_of_thirds_score': rule_of_thirds_score,
                'leading_lines': leading_lines_info,
                'dominant_palette': dominant_palette,
            },
            'color_analysis': {
                'harmony_type': harmony_type,
                'harmony_score': harmony_score,
                'color_diversity': color_diversity,
                'color_temperature': color_temperature,
                'moods': moods,
            },
            'lighting_analysis': brightness_info,
            'top_3_improvements': improvements,
            'dimensions': {'width': w, 'height': h, 'aspect_ratio': aspect_ratio},
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

            result = AestheticStyleAnalyzer.analyze(image_path)

            if 'error' in result:
                raise RuntimeError(result['error'])

            result['filename'] = os.path.basename(image_url) if image_url else os.path.basename(image_path)

            await Actor.push_data(result)
            Actor.log.info(
                f"Aesthetic analysis complete: {result['filename']} — "
                f"score: {result['aesthetic_score']}/10 — "
                f"styles: {[s['style'] for s in result['style_classification']]}"
            )

        finally:
            if temp_file:
                os.unlink(temp_file.name)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
