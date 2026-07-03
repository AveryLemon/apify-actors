# P0-3: Build Stem Separation Actor

## Goal
Build and deploy an Apify actor that takes an audio file URL and returns separated stems (vocals, drums, bass, other instruments) as downloadable files.

## Why
**No Apify actor offers this.** LALAL.AI and MVSEP prove massive demand. Creators, podcasters, DJs, and video editors all need stem separation. Estimated price: $0.50-1.00/run.

## Approach
- Use open-source stem separation model (Demucs / MVSEP / spleeter)
- Input: audio file URL (YouTube, SoundCloud, direct MP3)
- Output: URLs to individual stem files (vocals.wav, drums.wav, bass.wav, other.wav)
- Metadata: stem quality scores, duration, original format

## Verification
- [ ] Actor builds on `apify push`
- [ ] Separates stems from a YouTube audio URL
- [ ] Returns valid download URLs for each stem
- [ ] Handles edge cases (silence, short clips, mono audio)
