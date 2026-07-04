"""
Stem Separator — Apify Actor
=============================
Separates audio files into individual stems (vocals, drums, bass, other).
Uses audio-separator's MDX models for lightweight, high-quality separation.

Input:  {"fileUrl": "https://example.com/song.mp3"}
Output: {"filename": "song.mp3", "stems": {"vocals": {...}, "drums": {...}, ...}}

RESTRICTED: Standalone tool. No OWL factory code, brand strategy, or pipelines.
"""

import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from apify import Actor
from audio_separator.separator import Separator


async def main() -> None:
    async with Actor:
        # Read input
        actor_input = await Actor.get_input() or {}
        file_url = actor_input.get('fileUrl', '')
        file_path = actor_input.get('filePath', '')

        if not file_url and not file_path:
            await Actor.fail(
                status_code=400,
                message='Either "fileUrl" or "filePath" must be provided.',
            )
            return

        Actor.log.info(f'Processing audio: {file_url or file_path}')

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize separator (default model is loaded automatically)
            Actor.log.info('Loading stem separator model...')
            separator = Separator(
                log_level=30,  # WARNING
                output_dir=tmpdir,
                output_format='WAV',
            )
            Actor.log.info('Model loaded.')

            # Determine input file path
            if file_url:
                input_path = os.path.join(tmpdir, 'input_audio.mp3')
                Actor.log.info('Downloading audio from URL...')
                try:
                    urllib.request.urlretrieve(file_url, input_path)
                except Exception as e:
                    await Actor.fail(
                        status_code=400,
                        message=f'Failed to download audio: {str(e)}',
                    )
                    return
            else:
                input_path = file_path
                if not os.path.exists(input_path):
                    await Actor.fail(
                        status_code=400,
                        message=f'File not found: {input_path}',
                    )
                    return

            # Verify input file is valid audio
            file_size = os.path.getsize(input_path)
            if file_size == 0:
                await Actor.fail(
                    status_code=400,
                    message='Input audio file is empty.',
                )
                return

            # Perform separation
            Actor.log.info('Separating stems (this may take a minute)...')
            try:
                out_files = separator.separate(input_path)
            except Exception as e:
                await Actor.fail(
                    status_code=500,
                    message=f'Stem separation failed: {str(e)}',
                )
                return

            if not out_files:
                await Actor.fail(
                    status_code=500,
                    message='Stem separation produced no output files.',
                )
                return

            Actor.log.info(f'Separation complete: {len(out_files)} files produced')

            # Map output files to stem names
            STEM_NAMES = ['vocals', 'drums', 'bass', 'other', 'guitar', 'piano']
            stem_files = {}
            for fname in out_files:
                fname_lower = fname.lower()
                matched = False
                for stem in STEM_NAMES:
                    if stem in fname_lower:
                        fpath = os.path.join(tmpdir, fname)
                        stem_files[stem] = {
                            'url': f'file://{fpath}',
                            'filename': fname,
                            'size_bytes': os.path.getsize(fpath) if os.path.exists(fpath) else 0,
                        }
                        matched = True
                        break
                if not matched:
                    # Place unknown stems under 'other'
                    fpath = os.path.join(tmpdir, fname)
                    stem_files[f'stem_{len(stem_files)}'] = {
                        'url': f'file://{fpath}',
                        'filename': fname,
                        'size_bytes': os.path.getsize(fpath) if os.path.exists(fpath) else 0,
                    }

            # Build result
            result = {
                'filename': Path(input_path).name,
                'stems': stem_files,
                'metadata': {
                    'num_stems': len(stem_files),
                    'stems_found': list(stem_files.keys()),
                    'source_size_bytes': file_size,
                    'model': 'default_mdx_model',
                },
            }

            Actor.log.info(f'Pushing result: {json.dumps(result, indent=2)}')
            await Actor.push_data(result)


if __name__ == '__main__':
    Actor.run(main())
