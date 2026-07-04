"""Thumbnail CTR Analyzer & Generator — Apify Actor

Analyzes YouTube/thumbnail images for click-through-rate likelihood
based on composition, contrast, text readability, color psychology,
and face presence. Generates optimized thumbnail variants.

INPUT:
  - imageUrl: str (URL to thumbnail image)
  OR
  - imagePath: str (local path to thumbnail image)
  - youtubeUrl: str (optional) — extracts thumbnail from YouTube URL
  - generateVariants: bool (default: false) — generate optimized variants
  - variantCount: int (default: 3, max 5)

OUTPUT:
  - ctr_score: float (0-100, higher = more clickable)
  - composition_score: float (0-100)
  - contrast_score: float (0-100)
  - text_readability_score: float (0-100)
  - color_psychology: dict
  - face_presence: dict
  - dimensions: dict
  - improvements: list[str]
  - variants: list[dict] (if generateVariants=true)
"""

import base64
import io
import math
import os
import re
import tempfile
from typing import Optional

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


# ═══════════════════════════════════════════════════════════════
# Pure logic class — zero apify imports, fully testable
# ═══════════════════════════════════════════════════════════════

# Color psychology reference: common YouTube emotions
COLOR_PSYCHOLOGY = {
    "red": {"emotion": "excitement/urgency", "ctr_boost": 15, "h_range": [(0, 10), (160, 180)]},
    "orange": {"emotion": "energy/enthusiasm", "ctr_boost": 12, "h_range": [(11, 25)]},
    "yellow": {"emotion": "optimism/happiness", "ctr_boost": 10, "h_range": [(26, 45)]},
    "green": {"emotion": "calm/trust", "ctr_boost": 5, "h_range": [(46, 75)]},
    "blue": {"emotion": "trust/professionalism", "ctr_boost": 8, "h_range": [(76, 135)]},
    "purple": {"emotion": "creativity/luxury", "ctr_boost": 6, "h_range": [(136, 155)]},
    "pink": {"emotion": "playfulness/feminine", "ctr_boost": 7, "h_range": [(156, 170)]},
    "white": {"emotion": "clean/simple", "ctr_boost": 3, "h_range": [(0, 360)]},
    "black": {"emotion": "premium/dramatic", "ctr_boost": 4, "h_range": [(0, 360)]},
}

# High-CTR color combinations (from YouTube analytics research)
HIGH_CTR_COMBOS = [
    ("red", "yellow"),
    ("red", "white"),
    ("blue", "yellow"),
    ("orange", "white"),
    ("green", "white"),
    ("red", "black"),
]

# YouTube URL pattern for ID extraction
YT_PATTERNS = [
    r"(?:youtube\.com/watch\?v=)([\w-]+)",
    r"(?:youtu\.be/)([\w-]+)",
    r"(?:youtube\.com/embed/)([\w-]+)",
    r"(?:youtube\.com/shorts/)([\w-]+)",
]


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    for p in YT_PATTERNS:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None


class ThumbnailAnalyzer:
    """Analyzes thumbnail images for CTR likelihood using pure image heuristics.

    All methods are @classmethod or @staticmethod for testability.
    No external ML dependencies — pure Pillow + numpy math.
    """

    @classmethod
    def analyze(cls, image_source: str) -> dict:
        """Analyze a thumbnail image for CTR likelihood.

        Args:
            image_source: Path to image file (local filesystem path)

        Returns:
            dict with all analysis results
        """
        img = Image.open(image_source)
        img_rgb = img.convert("RGB")
        arr = np.array(img_rgb)

        width, height = img.size
        total_pixels = width * height

        # 1. Composition analysis
        composition = cls._analyze_composition(arr, width, height)

        # 2. Color analysis
        colors = cls._analyze_colors(arr)

        # 3. Contrast analysis
        contrast = cls._analyze_contrast(arr, img_rgb)

        # 4. Text readability
        text_readability = cls._analyze_text_readability(arr, width, height)

        # 5. Face presence
        face = cls._detect_face_heuristic(arr, width, height)

        # 6. Color psychology
        dominant_hue = colors["dominant_hue"]
        color_psych = cls._analyze_color_psychology(arr, float(dominant_hue))

        # 7. Overall CTR score
        ctr_score = cls._calculate_ctr_score(
            composition=composition["score"],
            contrast=contrast["score"],
            text_readability=text_readability["score"],
            face_score=face["score"],
            color_boost=color_psych["ctr_boost"],
            brightness_ok=contrast["brightness_ok"],
        )

        # 8. Generate improvements
        improvements = cls._generate_improvements(
            composition, contrast, text_readability, face, color_psych
        )

        return {
            "ctr_score": round(float(ctr_score), 1),
            "composition_score": round(float(composition["score"]), 1),
            "contrast_score": round(float(contrast["score"]), 1),
            "text_readability_score": round(float(text_readability["score"]), 1),
            "color_psychology": {
                "dominant_color": colors["dominant_color_name"],
                "dominant_hue": round(float(colors["dominant_hue"]), 1),
                "dominant_emotion": color_psych["emotion"],
                "ctr_boost_from_color": color_psych["ctr_boost"],
                "color_variety_score": round(float(colors["variety"]), 1),
                "has_high_ctr_combination": bool(colors["has_high_ctr_combo"]),
            },
            "face_presence": {
                "detected": face["detected"],
                "score": round(float(face["score"]), 1),
                "position": face["position"],
                "size_percentage": round(float(face["size_pct"]), 1),
            },
            "dimensions": {
                "width": width,
                "height": height,
                "aspect_ratio": round(float(width) / float(height), 3),
            },
            "improvements": improvements[:5],
        }

    @classmethod
    def generate_variants(cls, image_source: str, count: int = 3) -> list[dict]:
        """Generate optimized thumbnail variants.

        Args:
            image_source: Path to source image
            count: Number of variants (1-5)

        Returns:
            List of dicts with variant info
        """
        count = max(1, min(count, 5))
        img = Image.open(image_source).convert("RGB")

        variants = [
            cls._make_variant(img, 1.6, 1.4, "neutral", False, 1.0, "High Contrast"),
            cls._make_variant(img, 1.3, 1.5, "warm", False, 1.0, "Warm & Vibrant"),
            cls._make_variant(img, 1.4, 1.2, "cool", True, 1.0, "Cool & Sharp"),
            cls._make_variant(img, 1.7, 1.1, "cool", False, 0.85, "Dramatic"),
            cls._make_variant(img, 1.2, 1.7, "neutral", False, 1.15, "Bright POP"),
        ]

        return variants[:count]

    # ── Private analysis methods ──────────────────────────────

    @classmethod
    def _analyze_composition(cls, arr: np.ndarray, width: int, height: int) -> dict:
        """Score composition using rule of thirds and focal point analysis."""
        third_w = max(1, width // 3)
        third_h = max(1, height // 3)

        grid_scores = []
        for row in range(3):
            for col in range(3):
                y1, y2 = row * third_h, min((row + 1) * third_h, height)
                x1, x2 = col * third_w, min((col + 1) * third_w, width)
                cell = arr[y1:y2, x1:x2]
                cell_size = cell.shape[0] * cell.shape[1]
                if cell_size < 4:
                    grid_scores.append(0.0)
                else:
                    grid_scores.append(float(np.std(cell)))

        if not grid_scores or max(grid_scores) == 0:
            return {"score": 50.0, "has_focal_point": False, "center_interest": 50.0}

        intersections = [grid_scores[0], grid_scores[2], grid_scores[6], grid_scores[8]]
        center_weight = float(grid_scores[4])
        max_intersection = max(intersections)
        mean_grid = float(np.mean(grid_scores))

        focal_score = min(100.0, (max_intersection / max(0.001, mean_grid)) * 25.0)
        center_score = min(100.0, (center_weight / max(0.001, mean_grid)) * 20.0)
        score = min(100.0, focal_score * 0.6 + center_score * 0.4)

        return {
            "score": score,
            "has_focal_point": focal_score > 30,
            "center_interest": round(center_score, 1),
        }

    @classmethod
    def _analyze_colors(cls, arr: np.ndarray) -> dict:
        """Extract dominant colors and measure variety."""
        hsv = cls._rgb_to_hsv(arr)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        hue_mask = s > 0.2
        if hue_mask.sum() > 0:
            dominant_hue = float(np.mean(h[hue_mask])) * 360.0
        else:
            dominant_hue = 0.0

        if hue_mask.sum() > 10:
            hue_variety = float(np.std(h[hue_mask])) * 360.0
            variety_score = min(100.0, hue_variety * 2.5)
        else:
            hue_variety = 0.0
            variety_score = 0.0

        color_name = cls._hue_to_color_name(dominant_hue, float(np.mean(s)), float(np.mean(v)))
        has_high_ctr = cls._check_high_ctr_combo(arr, hue_mask, h)

        return {
            "dominant_hue": dominant_hue,
            "dominant_color_name": color_name,
            "variety": variety_score,
            "hue_variety": round(hue_variety, 1),
            "has_high_ctr_combo": has_high_ctr,
        }

    @classmethod
    def _analyze_contrast(cls, arr: np.ndarray, img_rgb: Image.Image) -> dict:
        """Analyze contrast and brightness."""
        gray = img_rgb.convert("L")
        gray_arr = np.array(gray)

        contrast_val = float(np.std(gray_arr))
        contrast_score = min(100.0, (contrast_val / 80.0) * 100.0)

        mean_brightness = float(np.mean(gray_arr))
        brightness_ok = 64 < mean_brightness < 220

        p10, p90 = np.percentile(gray_arr, [10, 90])
        dynamic_range = float(p90 - p10)
        range_ok = dynamic_range > 80

        return {
            "score": round(contrast_score, 1),
            "brightness": round(mean_brightness, 1),
            "brightness_ok": brightness_ok,
            "dynamic_range": round(dynamic_range, 1),
            "dynamic_range_ok": range_ok,
        }

    @classmethod
    def _analyze_text_readability(cls, arr: np.ndarray, width: int, height: int) -> dict:
        """Score text readability based on contrast and edge presence."""
        gray = np.mean(arr, axis=2)
        grad_x = np.abs(np.diff(gray, axis=1))
        grad_y = np.abs(np.diff(gray, axis=0))

        grad_x_padded = np.pad(grad_x, ((0, 0), (0, 1)), mode="constant")
        grad_y_padded = np.pad(grad_y, ((0, 1), (0, 0)), mode="constant")

        edge_magnitude = np.sqrt(grad_x_padded**2 + grad_y_padded**2)
        edge_density = float(np.mean(edge_magnitude > 30)) * 100.0

        if edge_density > 15:
            text_score = min(100.0, edge_density * 3.5)
        elif edge_density > 5:
            text_score = 50.0 + (edge_density - 5.0) * 3.0
        else:
            text_score = edge_density * 5.0

        return {"score": round(min(100.0, text_score), 1), "edge_density": round(edge_density, 1)}

    @classmethod
    def _detect_face_heuristic(cls, arr: np.ndarray, width: int, height: int) -> dict:
        """Detect face-like regions using skin-color heuristics (no ML)."""
        if width * height < 16:
            return {
                "detected": False,
                "score": 0.0,
                "position": "none",
                "size_pct": 0.0,
            }

        hsv = cls._rgb_to_hsv(arr)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        # Skin color range in HSV (general human skin tones)
        skin_mask = (
            (h > 0.0) & (h < 0.1)
            & (s > 0.15) & (s < 0.65)
            & (v > 0.35) & (v < 0.95)
        )

        skin_pct = float(skin_mask.sum()) / float(width * height) * 100.0

        detected = skin_pct > 3
        position = "none"
        score = 0.0

        if detected:
            ys, xs = np.where(skin_mask)
            if len(ys) > 0:
                cy = float(np.mean(ys))
                cx = float(np.mean(xs))
                rel_y = cy / height
                if rel_y < 0.33:
                    position = "top"
                elif rel_y < 0.66:
                    position = "center"
                else:
                    position = "bottom"

                size_score = min(100.0, (skin_pct / 15.0) * 100.0)
                cy_rel = cy / height
                cx_rel = cx / width
                center_dist = math.sqrt((cy_rel - 0.5) ** 2 + (cx_rel - 0.5) ** 2)
                position_bonus = max(0.0, 20.0 - center_dist * 40.0)
                score = min(100.0, size_score * 0.7 + position_bonus)

        return {
            "detected": detected,
            "score": score,
            "position": position,
            "size_pct": round(skin_pct, 2),
        }

    @classmethod
    def _analyze_color_psychology(cls, arr: np.ndarray, dominant_hue: float) -> dict:
        """Map dominant colors to emotional response."""
        closest_color = "blue"
        closest_boost = 8
        closest_emotion = "trust/professionalism"

        for color_name, info in COLOR_PSYCHOLOGY.items():
            for h_range in info["h_range"]:
                low, high = h_range
                if low > high:
                    if dominant_hue >= low or dominant_hue <= high:
                        closest_color = color_name
                        closest_boost = info["ctr_boost"]
                        closest_emotion = info["emotion"]
                        break
                else:
                    if low <= dominant_hue <= high:
                        closest_color = color_name
                        closest_boost = info["ctr_boost"]
                        closest_emotion = info["emotion"]
                        break
            else:
                continue
            break

        # White/black: check saturation/value instead of hue
        hsv = cls._rgb_to_hsv(arr)
        mean_s = float(np.mean(hsv[:, :, 1]))
        mean_v = float(np.mean(hsv[:, :, 2]))

        if mean_s < 0.1 and mean_v > 0.8:
            closest_color = "white"
            closest_boost = 3
            closest_emotion = "clean/simple"
        elif mean_s < 0.15 and mean_v < 0.3:
            closest_color = "black"
            closest_boost = 4
            closest_emotion = "premium/dramatic"

        return {
            "color": closest_color,
            "emotion": closest_emotion,
            "ctr_boost": closest_boost,
        }

    @classmethod
    def _calculate_ctr_score(
        cls,
        composition: float,
        contrast: float,
        text_readability: float,
        face_score: float,
        color_boost: float,
        brightness_ok: bool,
    ) -> float:
        """Calculate overall CTR score from all components."""
        weights = {
            "composition": 0.20,
            "contrast": 0.25,
            "text_readability": 0.15,
            "face_score": 0.25,
            "color_boost_norm": 0.15,
        }

        color_boost_norm = min(100.0, (color_boost / 15.0) * 100.0)

        raw_score = (
            composition * weights["composition"]
            + contrast * weights["contrast"]
            + text_readability * weights["text_readability"]
            + face_score * weights["face_score"]
            + color_boost_norm * weights["color_boost_norm"]
        )

        if not brightness_ok:
            raw_score *= 0.85

        return min(100.0, raw_score)

    @classmethod
    def _generate_improvements(
        cls, composition: dict, contrast: dict, text_readability: dict, face: dict, color_psych: dict
    ) -> list[str]:
        """Generate actionable improvement suggestions."""
        improvements = []

        if composition["score"] < 50:
            improvements.append(
                "Improve composition: place the main subject at a rule-of-thirds intersection point"
            )

        if contrast["score"] < 50:
            improvements.append(
                f"Increase contrast (current: {contrast['score']}/100). "
                "Use strong light/dark separation"
            )

        if not contrast["brightness_ok"]:
            improvements.append(
                f"Adjust brightness (current: {contrast['brightness']}/255). "
                "Target 80-200 range"
            )

        if not contrast["dynamic_range_ok"]:
            improvements.append("Increase dynamic range. Ensure dark shadows AND bright highlights")

        if text_readability["score"] < 50:
            improvements.append(
                f"Improve text readability (current: {text_readability['score']}/100). "
                "Add text overlay with high contrast outline"
            )

        if face["score"] < 30 and not face["detected"]:
            improvements.append(
                "Add a face/expression. Thumbnails with expressive faces get 30%+ more clicks"
            )

        if face["detected"] and face["score"] < 50:
            improvements.append(
                "Make the face larger and more centered. Faces should occupy 10-15% of the thumbnail"
            )

        if color_psych["ctr_boost"] < 8:
            improvements.append(
                f"Use a warmer/more energetic color palette. "
                f"Current dominant color ({color_psych['color']}) has moderate CTR impact"
            )

        if not improvements:
            improvements.append("Thumbnail already well-optimized. Consider A/B testing with minor variations")

        return improvements

    # ── Variant generation ─────────────────────────────────────

    @classmethod
    def _make_variant(
        cls,
        img: Image.Image,
        contrast_boost: float = 1.0,
        sat_boost: float = 1.0,
        warmth: str = "neutral",
        sharpen: bool = False,
        brightness: float = 1.0,
        label: str = "Variant",
    ) -> dict:
        """Create an optimized variant of the input image."""
        variant = img.copy()

        # Contrast
        variant = ImageEnhance.Contrast(variant).enhance(contrast_boost)

        # Color (saturation)
        variant = ImageEnhance.Color(variant).enhance(sat_boost)

        # Brightness
        variant = ImageEnhance.Brightness(variant).enhance(brightness)

        # Warmth shift
        if warmth != "neutral":
            arr = np.array(variant).astype(np.float32)
            if warmth == "warm":
                arr[:, :, 0] *= 1.1
                arr[:, :, 2] *= 0.9
            elif warmth == "cool":
                arr[:, :, 0] *= 0.9
                arr[:, :, 2] *= 1.1
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            variant = Image.fromarray(arr)

        # Sharpen
        if sharpen:
            variant = variant.filter(ImageFilter.SHARPEN)

        # Save to bytes
        buf = io.BytesIO()
        variant.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "label": label,
            "description": cls._variant_description(label, contrast_boost, sat_boost, warmth, brightness),
            "image_base64": img_b64,
            "format": "png",
        }

    @staticmethod
    def _variant_description(label: str, contrast: float, sat: float, warmth: str, brightness: float) -> str:
        """Generate a human-readable description of the variant."""
        parts = [f"{label}: contrast {contrast:.1f}x, saturation {sat:.1f}x, brightness {brightness:.1f}x"]
        if warmth == "warm":
            parts.append("warm tone shift")
        elif warmth == "cool":
            parts.append("cool tone shift")
        return ", ".join(parts)

    # ── Utility methods ────────────────────────────────────────

    @staticmethod
    def _rgb_to_hsv(arr: np.ndarray) -> np.ndarray:
        """Convert RGB numpy array [0-255] to HSV [0-1, 0-1, 0-1]."""
        rgb_float = arr.astype(np.float32) / 255.0
        r, g, b = rgb_float[:, :, 0], rgb_float[:, :, 1], rgb_float[:, :, 2]

        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        delta = max_c - min_c

        h = np.zeros_like(max_c)
        mask = delta > 0
        r_mask = mask & (max_c == r)
        g_mask = mask & (max_c == g)
        b_mask = mask & (max_c == b)

        h[r_mask] = (60.0 * ((g[r_mask] - b[r_mask]) / delta[r_mask]) + 360.0) % 360.0
        h[g_mask] = (60.0 * ((b[g_mask] - r[g_mask]) / delta[g_mask]) + 120.0) % 360.0
        h[b_mask] = (60.0 * ((r[b_mask] - g[b_mask]) / delta[b_mask]) + 240.0) % 360.0
        h /= 360.0

        s = np.zeros_like(max_c)
        s[max_c > 0] = delta[max_c > 0] / max_c[max_c > 0]
        v = max_c

        return np.stack([h, s, v], axis=2)

    @staticmethod
    def _hue_to_color_name(hue: float, mean_s: float, mean_v: float) -> str:
        """Map a hue degree to a color name."""
        if mean_s < 0.1 and mean_v > 0.8:
            return "white"
        if mean_s < 0.15 and mean_v < 0.3:
            return "black"
        if mean_v < 0.15:
            return "black"

        if hue < 15 or hue >= 345:
            return "red"
        if hue < 35:
            return "orange"
        if hue < 55:
            return "yellow"
        if hue < 85:
            return "yellow-green"
        if hue < 145:
            return "green"
        if hue < 195:
            return "teal"
        if hue < 255:
            return "blue"
        if hue < 285:
            return "purple"
        if hue < 330:
            return "pink"
        return "red"

    @staticmethod
    def _check_high_ctr_combo(arr: np.ndarray, hue_mask: np.ndarray, h: np.ndarray) -> bool:
        """Check if the image contains any high-CTR color combinations."""
        if hue_mask.sum() < 50:
            return False

        present = set()
        for h_val in h[hue_mask]:
            deg = float(h_val) * 360.0
            for name, info in COLOR_PSYCHOLOGY.items():
                for low, high in info["h_range"]:
                    if low <= deg <= high:
                        present.add(name)
                        break

        for c1, c2 in HIGH_CTR_COMBOS:
            if c1 in present and c2 in present:
                return True
        return False
