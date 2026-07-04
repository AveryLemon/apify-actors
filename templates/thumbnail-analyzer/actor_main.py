"""Thumbnail CTR Analyzer & Generator — Apify Actor (SDK wrapper)

Runs inside Docker with apify SDK.
Calls the pure ThumbnailAnalyzer class for all image processing.
"""

import os
import tempfile

import requests

import apify
from apify import Actor

from main import ThumbnailAnalyzer, extract_youtube_id


async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        image_url = actor_input.get("imageUrl", "")
        image_path = actor_input.get("imagePath", "")
        youtube_url = actor_input.get("youtubeUrl", "")
        generate_variants = actor_input.get("generateVariants", False)
        variant_count = min(int(actor_input.get("variantCount", 3)), 5)

        local_path = None
        try:
            if image_url:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                tmp = tempfile.gettempdir()
                local_path = os.path.join(tmp, "thumbnail_input.png")
                with open(local_path, "wb") as f:
                    f.write(response.content)
            elif image_path:
                local_path = image_path
            elif youtube_url:
                vid_id = extract_youtube_id(youtube_url)
                if vid_id:
                    thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
                    response = requests.get(thumb_url, timeout=30)
                    response.raise_for_status()
                    tmp = tempfile.gettempdir()
                    local_path = os.path.join(tmp, "youtube_thumb.png")
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                else:
                    raise ValueError(f"Could not extract video ID from: {youtube_url}")
            else:
                raise ValueError("Must provide one of: imageUrl, imagePath, or youtubeUrl")

            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Image not found: {local_path}")

            # Analyze
            result = ThumbnailAnalyzer.analyze(local_path)

            # Generate variants if requested
            if generate_variants:
                result["variants"] = ThumbnailAnalyzer.generate_variants(local_path, variant_count)

            await Actor.push_data(result)

        except Exception as e:
            await Actor.push_data({"error": str(e), "error_type": type(e).__name__})
