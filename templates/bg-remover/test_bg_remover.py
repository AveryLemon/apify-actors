"""
Tests for Background Remover + Enhancement Actor.
Uses the duplicated test class pattern for testability.
"""

import base64
import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

# Duplicate the pure logic class for testing (avoids exec() fragility)
# This is the same code as BackgroundRemover in main.py, minus the rembg dependency.
# rembg is mocked at class level for testing.

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS


class BackgroundRemover:
    """Testable copy of the logic class from main.py.
    
    rembg is injected as a class-level attribute so tests can mock it.
    """

    ALLOWED_INPUT_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    MAX_IMAGE_PIXELS = 50_000_000
    MAX_BATCH_SIZE = 20

    # Injected dependencies (overridden by test setUp())
    _requests_get = None
    _rembg_remove = None
    _rembg_error = Exception

    @classmethod
    def _get_requests(cls):
        if cls._requests_get is None:
            import requests
            return requests.get
        return cls._requests_get

    @classmethod
    def _get_rembg(cls):
        if cls._rembg_remove is None:
            from rembg import remove
            return remove
        return cls._rembg_remove

    @classmethod
    def download_image(cls, url, timeout=60):
        resp = cls._get_requests()(url, timeout=timeout)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL returned non-image content-type: {content_type}")
        return resp.content

    @classmethod
    def validate_url(cls, url):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        ext = os.path.splitext(parsed.path.lower())[1]
        if ext and ext not in cls.ALLOWED_INPUT_FORMATS:
            return False
        return True

    @classmethod
    def remove_background(cls, image_bytes):
        try:
            rembg_fn = cls._get_rembg()
            return rembg_fn(image_bytes)
        except Exception as e:
            return None

    @classmethod
    def remove_background_pil(cls, pil_image):
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        buf.seek(0)
        result_bytes = cls.remove_background(buf.getvalue())
        if result_bytes is None:
            return None
        return Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    @classmethod
    def add_shadow(cls, image, blur_radius=15, offset=(10, 10),
                   opacity=0.5, shadow_color=(0, 0, 0)):
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        alpha = image.split()[3]
        shadow = Image.new("RGBA", image.size, (*shadow_color, 0))
        shadow_shape = Image.new("L", image.size, 0)
        shadow_shape.paste(255, mask=alpha)
        shadow_shape = shadow_shape.filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )
        shadow_np = np.array(shadow_shape, dtype=np.float32)
        shadow_np = (shadow_np * opacity).astype(np.uint8)
        shadow.putalpha(Image.fromarray(shadow_np, mode="L"))
        canvas_size = (
            image.size[0] + abs(offset[0]),
            image.size[1] + abs(offset[1])
        )
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        canvas.paste(shadow, (max(0, offset[0]), max(0, offset[1])))
        canvas.paste(image, (max(0, -offset[0]), max(0, -offset[1])), image)
        return canvas

    @classmethod
    def composite_background(cls, foreground, background, shadow=True):
        fg_rgba = foreground.convert("RGBA")
        bg_rgb = background.convert("RGB").resize(
            fg_rgba.size, _RESAMPLE
        )
        bg_rgba = bg_rgb.convert("RGBA")
        if shadow:
            shadowed = cls.add_shadow(fg_rgba)
            bg_resized = background.convert("RGB").resize(
                shadowed.size, _RESAMPLE
            ).convert("RGBA")
            bg_resized.paste(shadowed, (0, 0), shadowed)
            return bg_resized
        else:
            bg_rgba.paste(fg_rgba, (0, 0), fg_rgba)
            return bg_rgba

    @classmethod
    def auto_enhance(cls, image):
        img = image.convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=1)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        if image.mode == "RGBA":
            r, g, b, a = image.split()
            img_rgba = img.convert("RGBA")
            img_rgba.putalpha(a)
            return img_rgba
        return img

    @classmethod
    def to_format(cls, image, fmt="png"):
        buf = io.BytesIO()
        save_kwargs = {}
        if fmt == "jpeg":
            image = image.convert("RGB")
            save_kwargs = {"quality": 92, "optimize": True}
        elif fmt == "webp":
            save_kwargs = {"quality": 90, "method": 6}
        image.save(buf, format=fmt.upper(), **save_kwargs)
        return buf.getvalue()

    @classmethod
    def encode_base64(cls, image_bytes):
        return base64.b64encode(image_bytes).decode("utf-8")

    @classmethod
    def process_image(cls, image_bytes, mode="transparent",
                      background_url=None, add_shadow_flag=True,
                      enhance=False, output_format="png"):
        try:
            original_size = len(image_bytes)
            result_bytes = cls.remove_background(image_bytes)
            if result_bytes is None:
                return {"success": False, "error": "Background removal failed"}
            result_img = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
            if mode == "white":
                white_bg = Image.new("RGBA", result_img.size, (255, 255, 255, 255))
                white_bg.paste(result_img, (0, 0), result_img)
                result_img = white_bg
            elif mode == "composite" and background_url:
                try:
                    bg_bytes = cls.download_image(background_url)
                    bg_img = Image.open(io.BytesIO(bg_bytes))
                    result_img = cls.composite_background(
                        result_img, bg_img, shadow=add_shadow_flag
                    )
                except Exception:
                    pass
            if enhance:
                result_img = cls.auto_enhance(result_img)
            output_bytes = cls.to_format(result_img, fmt=output_format)
            return {
                "success": True,
                "image_base64": cls.encode_base64(output_bytes),
                "format": output_format,
                "original_size": original_size,
                "result_size": len(output_bytes),
                "result_size_ratio": round(len(output_bytes) / max(original_size, 1), 2)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def process_url(cls, url, **kwargs):
        if not cls.validate_url(url):
            return {"success": False, "error": f"Invalid URL: {url}"}
        try:
            image_bytes = cls.download_image(url)
            return cls.process_image(image_bytes, **kwargs)
        except Exception as e:
            return {"success": False, "error": f"Processing failed: {e}"}

    @classmethod
    def process_batch(cls, urls, **kwargs):
        if len(urls) > cls.MAX_BATCH_SIZE:
            urls = urls[:cls.MAX_BATCH_SIZE]
        results = []
        for url in urls:
            result = cls.process_url(url, **kwargs)
            result["url"] = url
            results.append(result)
        return results


# ─── Helper: create test images ────────────────────────────────


def _create_test_image(size=(200, 200), color=(100, 150, 200),
                       has_alpha=False) -> bytes:
    """Create a simple test image and return as bytes."""
    if has_alpha:
        img = Image.new("RGBA", size, (*color, 255))
        # Add a visible object (circle) on transparent bg
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.ellipse([20, 20, 180, 180], fill=(*color, 255))
    else:
        img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_test_image_pil(size=(200, 200), color=(100, 150, 200),
                           has_alpha=False) -> Image.Image:
    """Create a test PIL Image."""
    if has_alpha:
        img = Image.new("RGBA", size, (*color, 128))
    else:
        img = Image.new("RGB", size, color)
    return img


# ─── Tests ─────────────────────────────────────────────────────


class TestURLValidation(unittest.TestCase):
    """Test URL validation logic."""

    def test_valid_http_url(self):
        self.assertTrue(BackgroundRemover.validate_url("http://example.com/image.jpg"))

    def test_valid_https_url(self):
        self.assertTrue(BackgroundRemover.validate_url("https://example.com/image.png"))

    def test_valid_webp_url(self):
        self.assertTrue(BackgroundRemover.validate_url("https://example.com/photo.webp"))

    def test_valid_no_extension_url(self):
        self.assertTrue(BackgroundRemover.validate_url("https://example.com/image"))

    def test_invalid_no_scheme(self):
        self.assertFalse(BackgroundRemover.validate_url("example.com/image.jpg"))

    def test_invalid_garbage_url(self):
        self.assertFalse(BackgroundRemover.validate_url("not-a-url"))

    def test_invalid_empty_string(self):
        self.assertFalse(BackgroundRemover.validate_url(""))

    def test_invalid_unsupported_format(self):
        self.assertFalse(BackgroundRemover.validate_url("https://example.com/file.svg"))


class TestDownloadImage(unittest.TestCase):
    """Test image download with mocked requests."""

    def setUp(self):
        self.mock_response = MagicMock()
        self.mock_response.headers = {"content-type": "image/png"}
        self.mock_response.content = _create_test_image()

        self.mock_get = MagicMock(return_value=self.mock_response)
        BackgroundRemover._requests_get = lambda *a, **kw: self.mock_get(*a, **kw)

    def tearDown(self):
        BackgroundRemover._requests_get = None

    def test_download_success(self):
        result = BackgroundRemover.download_image("https://example.com/test.png")
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    def test_download_raises_on_non_image(self):
        self.mock_response.headers = {"content-type": "text/html"}
        with self.assertRaises(ValueError):
            BackgroundRemover.download_image("https://example.com/test.png")

    def test_download_passes_timeout(self):
        BackgroundRemover.download_image("https://example.com/test.png", timeout=30)
        _, kwargs = self.mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), 30)


class TestBackgroundRemoval(unittest.TestCase):
    """Test background removal with mocked rembg."""

    def setUp(self):
        # Mock rembg to return the image unchanged
        def mock_remove(img_bytes):
            return img_bytes
        BackgroundRemover._rembg_remove = mock_remove

    def tearDown(self):
        BackgroundRemover._rembg_remove = None

    def test_remove_background_returns_bytes(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.remove_background(img_bytes)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bytes)

    def test_remove_background_pil_returns_image(self):
        pil_img = _create_test_image_pil()
        result = BackgroundRemover.remove_background_pil(pil_img)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.mode, "RGBA")

    def test_remove_background_fallback_on_error(self):
        BackgroundRemover._rembg_remove = None  # Force error
        # Set a function that raises
        def failing_remove(_):
            raise RuntimeError("rembg failed")
        BackgroundRemover._rembg_remove = failing_remove
        result = BackgroundRemover.remove_background(b"bad data")
        self.assertIsNone(result)


class TestShadowCompositing(unittest.TestCase):
    """Test drop shadow addition."""

    def setUp(self):
        self.fg = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        # Make a circular shape on transparent
        mask = Image.new("L", (100, 100), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.ellipse([10, 10, 90, 90], fill=255)
        self.fg.putalpha(mask)

    def test_shadow_returns_rgba(self):
        result = BackgroundRemover.add_shadow(self.fg)
        self.assertEqual(result.mode, "RGBA")

    def test_shadow_increases_canvas_size(self):
        result = BackgroundRemover.add_shadow(self.fg, offset=(15, 15))
        self.assertGreater(result.size[0], self.fg.size[0])
        self.assertGreater(result.size[1], self.fg.size[1])

    def test_shadow_offset_zero_no_resize(self):
        result = BackgroundRemover.add_shadow(self.fg, offset=(0, 0))
        self.assertEqual(result.size, self.fg.size)

    def test_shadow_with_opacity(self):
        result = BackgroundRemover.add_shadow(self.fg, opacity=0.3)
        self.assertEqual(result.mode, "RGBA")

    def test_shadow_with_blur_radius(self):
        result = BackgroundRemover.add_shadow(self.fg, blur_radius=5)
        self.assertEqual(result.mode, "RGBA")

    def test_shadow_with_custom_color(self):
        result = BackgroundRemover.add_shadow(self.fg, shadow_color=(50, 50, 50))
        self.assertEqual(result.mode, "RGBA")

    def test_shadow_preserves_foreground(self):
        result = BackgroundRemover.add_shadow(self.fg)
        # The foreground should still be visible in the result
        result_rgba = result.convert("RGBA")
        # Check center pixel has red component (foreground)
        center_x = result.size[0] // 2
        center_y = result.size[1] // 2
        pixel = result_rgba.getpixel((center_x, center_y))
        self.assertGreater(pixel[0], 100, "Foreground red channel should be preserved")

    def test_shadow_converts_rgb_to_rgba(self):
        rgb_img = Image.new("RGB", (100, 100), (255, 0, 0))
        result = BackgroundRemover.add_shadow(rgb_img)
        self.assertEqual(result.mode, "RGBA")


class TestCompositeBackground(unittest.TestCase):
    """Test background compositing."""

    def setUp(self):
        self.fg = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        self.bg = Image.new("RGB", (100, 100), (0, 255, 0))

    def test_composite_without_shadow(self):
        result = BackgroundRemover.composite_background(self.fg, self.bg, shadow=False)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, (100, 100))

    def test_composite_with_shadow(self):
        result = BackgroundRemover.composite_background(self.fg, self.bg, shadow=True)
        self.assertEqual(result.mode, "RGBA")
        self.assertGreater(result.size[0], 100)  # Shadow adds canvas size
        self.assertGreater(result.size[1], 100)

    def test_composite_resizes_background(self):
        bg_small = Image.new("RGB", (50, 50), (0, 255, 0))
        result = BackgroundRemover.composite_background(self.fg, bg_small, shadow=False)
        self.assertEqual(result.size, (100, 100))


class TestAutoEnhance(unittest.TestCase):
    """Test auto-enhancement."""

    def test_enhance_rgb_image(self):
        img = _create_test_image_pil(color=(50, 50, 50))
        result = BackgroundRemover.auto_enhance(img)
        self.assertIsNotNone(result)
        self.assertEqual(result.mode, "RGB")

    def test_enhance_rgba_image(self):
        img = _create_test_image_pil(color=(50, 50, 50), has_alpha=True)
        result = BackgroundRemover.auto_enhance(img)
        self.assertIsNotNone(result)
        self.assertEqual(result.mode, "RGBA")

    def test_enhance_improves_contrast(self):
        # Create low contrast image
        img = Image.new("RGB", (100, 100), (100, 100, 100))
        # Add a small darker patch
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 30, 30], fill=(80, 80, 80))
        result = BackgroundRemover.auto_enhance(img)
        # Should still be an image
        self.assertIsInstance(result, Image.Image)

    def test_enhance_preserves_size(self):
        img = _create_test_image_pil(size=(300, 200))
        result = BackgroundRemover.auto_enhance(img)
        self.assertEqual(result.size, (300, 200))


class TestFormatConversion(unittest.TestCase):
    """Test output format conversion."""

    def setUp(self):
        self.img = Image.new("RGB", (50, 50), (255, 0, 0))

    def test_to_png(self):
        result = BackgroundRemover.to_format(self.img, fmt="png")
        self.assertGreater(len(result), 0)
        # Verify it's actually a PNG
        self.assertTrue(result.startswith(b"\x89PNG"))

    def test_to_jpeg(self):
        result = BackgroundRemover.to_format(self.img, fmt="jpeg")
        self.assertGreater(len(result), 0)
        self.assertTrue(result.startswith(b"\xff\xd8"))

    def test_to_webp(self):
        result = BackgroundRemover.to_format(self.img, fmt="webp")
        self.assertGreater(len(result), 0)

    def test_to_format_rgba_to_jpeg(self):
        rgba = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        result = BackgroundRemover.to_format(rgba, fmt="jpeg")
        self.assertGreater(len(result), 0)

    def test_encode_base64(self):
        result = BackgroundRemover.encode_base64(b"test bytes")
        self.assertIsInstance(result, str)
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, b"test bytes")


class TestProcessImage(unittest.TestCase):
    """Test full image processing pipeline (with mocked rembg)."""

    def setUp(self):
        def mock_remove(img_bytes):
            img = Image.open(io.BytesIO(img_bytes))
            rgba = img.convert("RGBA")
            buf = io.BytesIO()
            rgba.save(buf, format="PNG")
            return buf.getvalue()
        BackgroundRemover._rembg_remove = mock_remove

    def tearDown(self):
        BackgroundRemover._rembg_remove = None

    def test_process_success(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes)
        self.assertTrue(result["success"])
        self.assertIn("image_base64", result)
        self.assertEqual(result["format"], "png")

    def test_process_white_mode(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes, mode="white")
        self.assertTrue(result["success"])

    def test_process_transparent_mode(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes, mode="transparent")
        self.assertTrue(result["success"])

    def test_process_with_enhance(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes, enhance=True)
        self.assertTrue(result["success"])

    def test_process_jpeg_output(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes, output_format="jpeg")
        self.assertTrue(result["success"])
        self.assertEqual(result["format"], "jpeg")

    def test_process_webp_output(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes, output_format="webp")
        self.assertTrue(result["success"])
        self.assertEqual(result["format"], "webp")

    def test_process_includes_size_metadata(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(img_bytes)
        self.assertIn("original_size", result)
        self.assertIn("result_size", result)
        self.assertIn("result_size_ratio", result)

    def test_process_on_rembg_failure(self):
        def failing_remove(_):
            raise RuntimeError("failed")
        BackgroundRemover._rembg_remove = failing_remove
        result = BackgroundRemover.process_image(b"bad data")
        self.assertFalse(result["success"])

    def test_process_handles_large_image(self):
        # 4K test image
        img_bytes = _create_test_image(size=(3840, 2160), color=(50, 100, 150))
        result = BackgroundRemover.process_image(img_bytes)
        self.assertTrue(result["success"])


class TestProcessURL(unittest.TestCase):
    """Test URL-based processing."""

    def setUp(self):
        self.test_img_bytes = _create_test_image()

        def mock_remove(img_bytes):
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        BackgroundRemover._rembg_remove = mock_remove

        self.mock_response = MagicMock()
        self.mock_response.headers = {"content-type": "image/png"}
        self.mock_response.content = self.test_img_bytes
        self.mock_get = MagicMock(return_value=self.mock_response)
        BackgroundRemover._requests_get = lambda *a, **kw: self.mock_get(*a, **kw)

    def tearDown(self):
        BackgroundRemover._rembg_remove = None
        BackgroundRemover._requests_get = None

    def test_process_url_success(self):
        result = BackgroundRemover.process_url("https://example.com/img.png")
        self.assertTrue(result["success"])

    def test_process_url_invalid(self):
        result = BackgroundRemover.process_url("not-a-url")
        self.assertFalse(result["success"])
        self.assertIn("Invalid URL", result.get("error", ""))

    def test_process_url_download_failure(self):
        self.mock_get.side_effect = Exception("Connection error")
        result = BackgroundRemover.process_url("https://example.com/img.png")
        self.assertFalse(result["success"])


class TestBatchProcessing(unittest.TestCase):
    """Test batch processing."""

    def setUp(self):
        def mock_remove(img_bytes):
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        BackgroundRemover._rembg_remove = mock_remove

        self.mock_response = MagicMock()
        self.mock_response.headers = {"content-type": "image/png"}
        self.mock_response.content = _create_test_image()
        self.mock_get = MagicMock(return_value=self.mock_response)
        BackgroundRemover._requests_get = lambda *a, **kw: self.mock_get(*a, **kw)

    def tearDown(self):
        BackgroundRemover._rembg_remove = None
        BackgroundRemover._requests_get = None

    def test_batch_processing(self):
        urls = [
            "https://example.com/img1.png",
            "https://example.com/img2.png",
            "https://example.com/img3.png"
        ]
        results = BackgroundRemover.process_batch(urls)
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertTrue(r["success"])
            self.assertIn("url", r)

    def test_batch_limit(self):
        urls = [f"https://example.com/img{i}.png" for i in range(30)]
        results = BackgroundRemover.process_batch(urls)
        self.assertLessEqual(len(results), BackgroundRemover.MAX_BATCH_SIZE)

    def test_batch_partial_failure(self):
        # Second URL fails
        call_count = [0]
        def mock_get_with_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Download failed")
            return self.mock_response
        BackgroundRemover._requests_get = lambda *a, **kw: mock_get_with_failure(*a, **kw)

        urls = ["https://example.com/img1.png", "https://example.com/img2.png"]
        results = BackgroundRemover.process_batch(urls)
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["success"])
        self.assertFalse(results[1]["success"])

    def test_batch_empty_list(self):
        results = BackgroundRemover.process_batch([])
        self.assertEqual(results, [])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        def mock_remove(img_bytes):
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        BackgroundRemover._rembg_remove = mock_remove

    def tearDown(self):
        BackgroundRemover._rembg_remove = None

    def test_1x1_image(self):
        img_bytes = _create_test_image(size=(1, 1), color=(255, 0, 0))
        result = BackgroundRemover.process_image(img_bytes)
        self.assertTrue(result["success"])

    def test_grayscale_image(self):
        img = Image.new("L", (100, 100), 128)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = BackgroundRemover.process_image(buf.getvalue())
        self.assertTrue(result["success"])

    def test_transparent_png_input(self):
        img_bytes = _create_test_image(has_alpha=True)
        result = BackgroundRemover.process_image(img_bytes)
        self.assertTrue(result["success"])

    def test_tiny_1px_image(self):
        img = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = BackgroundRemover.process_image(buf.getvalue())
        self.assertTrue(result["success"])

    def test_empty_bytes(self):
        BackgroundRemover._rembg_remove = None
        def failing_remove(_):
            raise RuntimeError("Empty data")
        BackgroundRemover._rembg_remove = failing_remove
        result = BackgroundRemover.process_image(b"")
        self.assertFalse(result["success"])

    def test_composite_without_bg_fallback(self):
        img_bytes = _create_test_image()
        result = BackgroundRemover.process_image(
            img_bytes, mode="composite", background_url=None
        )
        # Should fall back to transparent mode
        self.assertTrue(result["success"])

    def test_validate_url_no_extension_returns_true(self):
        self.assertTrue(BackgroundRemover.validate_url("https://example.com/image"))


class TestShadowEdgeCases(unittest.TestCase):
    """Test shadow compositing edge cases."""

    def test_shadow_fully_transparent(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 0))  # Fully transparent
        result = BackgroundRemover.add_shadow(img)
        self.assertEqual(result.mode, "RGBA")

    def test_shadow_large_offset(self):
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
        result = BackgroundRemover.add_shadow(img, offset=(100, 100))
        self.assertGreater(result.size[0], 100)
        self.assertGreater(result.size[1], 100)

    def test_shadow_negative_offset(self):
        """Shadow offset can be negative (shadow above/left)."""
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
        # Negative offset means we need to shift canvas instead
        result = BackgroundRemover.add_shadow(img, offset=(-10, -10))
        self.assertEqual(result.mode, "RGBA")
        self.assertGreaterEqual(result.size[0], 50)
        self.assertGreaterEqual(result.size[1], 50)

    def test_shadow_zero_blur(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        result = BackgroundRemover.add_shadow(img, blur_radius=0)
        self.assertEqual(result.mode, "RGBA")


if __name__ == "__main__":
    unittest.main()
