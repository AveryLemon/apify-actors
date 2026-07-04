"""
Background Remover + Enhancement Actor for Apify.
Removes backgrounds from images using rembg (ONNX-based).
Optional: shadow compositing, background replacement, auto-enhancement.
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS  # Fallback for Pillow < 10.0

logger = logging.getLogger(__name__)

# ─── Pure logic class (testable without apify SDK) ──────────────


class BackgroundRemover:
    """Pure logic class for background removal and enhancement.
    
    Designed for testability: rembg is imported lazily inside the classmethod,
    and all image processing is stateless Pillow/numpy operations.
    """

    ALLOWED_INPUT_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    MAX_IMAGE_PIXELS = 50_000_000  # ~50MP limit
    MAX_BATCH_SIZE = 20

    @classmethod
    def download_image(cls, url: str, timeout: int = 60) -> bytes:
        """Download an image from URL and return raw bytes."""
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        # Validate it's actually an image by content type
        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL returned non-image content-type: {content_type}")
        return resp.content

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Check if URL looks valid for an image."""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        ext = os.path.splitext(parsed.path.lower())[1]
        if ext and ext not in cls.ALLOWED_INPUT_FORMATS:
            return False
        return True

    @classmethod
    def remove_background(cls, image_bytes: bytes) -> Optional[bytes]:
        """Remove background from image bytes using rembg.
        
        Returns PNG bytes with transparency, or None on failure.
        """
        try:
            from rembg import remove as rembg_remove
            result_bytes = rembg_remove(image_bytes)
            return result_bytes
        except Exception as e:
            logger.error(f"rembg removal failed: {e}")
            return None

    @classmethod
    def remove_background_pil(cls, pil_image: Image.Image) -> Optional[Image.Image]:
        """Remove background from PIL Image.
        
        Converts to bytes, runs rembg, returns PIL Image with alpha.
        """
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        buf.seek(0)
        result_bytes = cls.remove_background(buf.getvalue())
        if result_bytes is None:
            return None
        return Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    @classmethod
    def add_shadow(cls, image: Image.Image, blur_radius: int = 15,
                   offset: tuple = (10, 10), opacity: float = 0.5,
                   shadow_color: tuple = (0, 0, 0)) -> Image.Image:
        """Add a realistic drop shadow behind the foreground object.
        
        Args:
            image: RGBA image with transparent background
            blur_radius: Gaussian blur radius for shadow softness
            offset: (x, y) shadow offset
            opacity: Shadow opacity (0.0 - 1.0)
            shadow_color: RGB color for shadow
        
        Returns:
            New RGBA image with shadow composited behind
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create shadow from alpha channel
        alpha = image.split()[3]
        shadow = Image.new("RGBA", image.size, (*shadow_color, 0))

        # Create flat shadow shape from alpha
        shadow_shape = Image.new("L", image.size, 0)
        shadow_shape.paste(255, mask=alpha)

        # Blur shadow for realism
        shadow_shape = shadow_shape.filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )

        # Apply opacity to shadow
        shadow_np = np.array(shadow_shape, dtype=np.float32)
        shadow_np = (shadow_np * opacity).astype(np.uint8)

        # Paint shadow
        shadow.putalpha(Image.fromarray(shadow_np, mode="L"))

        # Composite: shadow behind foreground
        canvas_size = (
            image.size[0] + abs(offset[0]),
            image.size[1] + abs(offset[1])
        )
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        canvas.paste(shadow, (max(0, offset[0]), max(0, offset[1])))
        canvas.paste(image, (max(0, -offset[0]), max(0, -offset[1])), image)
        return canvas

    @classmethod
    def composite_background(cls, foreground: Image.Image,
                             background: Image.Image,
                             shadow: bool = True) -> Image.Image:
        """Composite foreground (with transparency) onto a background image.
        
        Args:
            foreground: RGBA image with transparent background
            background: Background image (will be resized to match)
            shadow: Add drop shadow before compositing
        
        Returns:
            Composited RGBA image
        """
        fg_rgba = foreground.convert("RGBA")

        # Resize background to match foreground
        bg_rgb = background.convert("RGB").resize(
            fg_rgba.size, _RESAMPLE
        )
        bg_rgba = bg_rgb.convert("RGBA")

        if shadow:
            # Add shadow first, then composite onto background
            shadowed = cls.add_shadow(fg_rgba)

            # Resize background to match shadowed canvas
            bg_resized = background.convert("RGB").resize(
                shadowed.size, _RESAMPLE
            ).convert("RGBA")
            bg_resized.paste(shadowed, (0, 0), shadowed)
            return bg_resized
        else:
            bg_rgba.paste(fg_rgba, (0, 0), fg_rgba)
            return bg_rgba

    @classmethod
    def auto_enhance(cls, image: Image.Image) -> Image.Image:
        """Apply auto-contrast and brightness normalization."""
        img = image.convert("RGB")

        # Auto contrast (stretch histogram)
        img = ImageOps.autocontrast(img, cutoff=1)

        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)

        if image.mode == "RGBA":
            r, g, b, a = image.split()
            img_rgba = img.convert("RGBA")
            img_rgba.putalpha(a)
            return img_rgba
        return img

    @classmethod
    def to_format(cls, image: Image.Image, fmt: str = "png") -> bytes:
        """Convert PIL Image to bytes in requested format."""
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
    def encode_base64(cls, image_bytes: bytes) -> str:
        """Encode bytes as base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    @classmethod
    def process_image(cls, image_bytes: bytes, mode: str = "transparent",
                      background_url: Optional[str] = None,
                      add_shadow_flag: bool = True,
                      enhance: bool = False,
                      output_format: str = "png"
                      ) -> Dict[str, Any]:
        """Process a single image: remove bg, optionally enhance/composite.

        Args:
            image_bytes: Raw image bytes
            mode: 'transparent' | 'white' | 'composite'
            background_url: Background image URL for composite mode
            add_shadow_flag: Add shadow in composite mode
            enhance: Apply auto-enhancement
            output_format: 'png' | 'jpeg' | 'webp'

        Returns:
            dict with keys: success, image_base64 (or error), format,
                            original_size, result_size
        """
        try:
            original_size = len(image_bytes)

            # Remove background
            result_bytes = cls.remove_background(image_bytes)
            if result_bytes is None:
                return {
                    "success": False,
                    "error": "Background removal failed (rembg returned None)"
                }

            result_img = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
            original_img = Image.open(io.BytesIO(image_bytes))

            # Apply mode
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
                except Exception as e:
                    logger.warning(f"Composite background download failed: {e}")
                    # Fall back to transparent
                    pass

            # Apply enhancement
            if enhance:
                result_img = cls.auto_enhance(result_img)

            # Convert to output format
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
            logger.error(f"Image processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    def process_url(cls, url: str, **kwargs) -> Dict[str, Any]:
        """Download image from URL and process it."""
        if not cls.validate_url(url):
            return {"success": False, "error": f"Invalid URL: {url}"}
        try:
            image_bytes = cls.download_image(url)
            return cls.process_image(image_bytes, **kwargs)
        except requests.RequestException as e:
            return {"success": False, "error": f"Download failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Processing failed: {e}"}

    @classmethod
    def process_batch(cls, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Process multiple images from URLs."""
        if len(urls) > cls.MAX_BATCH_SIZE:
            urls = urls[:cls.MAX_BATCH_SIZE]
        results = []
        for url in urls:
            result = cls.process_url(url, **kwargs)
            result["url"] = url
            results.append(result)
        return results


# ─── Apify SDK wrapper (runs in Docker) ─────────────────────────


async def main():
    """Apify actor entry point."""
    from apify import Actor

    async with Actor:
        Actor.log.info("Background Remover + Enhancer actor starting")

        # Read input
        run_input: dict = await Actor.get_input() or {}
        image_url = run_input.get("imageUrl", "")
        image_urls = run_input.get("imageUrls", [])
        mode = run_input.get("mode", "transparent")
        bg_url = run_input.get("backgroundUrl", "")
        add_shadow_flag = run_input.get("addShadow", True)
        enhance = run_input.get("enhance", False)
        output_format = run_input.get("outputFormat", "png")

        # Validate at least one input
        if not image_url and not image_urls:
            await Actor.push({
                "success": False,
                "error": "No input provided. Provide imageUrl (single) or imageUrls (batch)."
            })
            return

        # Process single image
        if image_url and not image_urls:
            Actor.log.info(f"Processing single image: {image_url}")
            result = BackgroundRemover.process_url(
                image_url,
                mode=mode,
                background_url=bg_url if bg_url else None,
                add_shadow_flag=add_shadow_flag,
                enhance=enhance,
                output_format=output_format
            )
            result["url"] = image_url
            await Actor.push(result)
            return

        # Process batch
        if image_urls:
            Actor.log.info(f"Processing batch of {len(image_urls)} images")
            results = BackgroundRemover.process_batch(
                image_urls,
                mode=mode,
                background_url=bg_url if bg_url else None,
                add_shadow_flag=add_shadow_flag,
                enhance=enhance,
                output_format=output_format
            )
            for result in results:
                await Actor.push(result)
            return


if __name__ == "__main__":
    asyncio.run(main())
