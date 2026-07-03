# P0-4: Build Audio Mood/Emotion Analysis Actor

## Goal
Build an Apify actor that analyzes uploaded audio files and returns a comprehensive mood/emotion profile — the audio equivalent of OWL's aesthetic engine.

## Why
ZERO competitors on Apify. OWL's factory already has mood analysis methodology. Direct port of OWL's capability to the marketplace. $0.50/run.

## Approach
- Input: audio file URL (YouTube, SoundCloud, direct upload)
- Output: overall mood (happy, sad, tense, calm, etc.), energy curve over time, arousal-valence plot, segment-level mood tags (0-30s: calm, 30-60s: building, 60-90s: energetic), timbre/texture description

## Verification
- [ ] Actor builds on push
- [ ] Returns valid mood + energy curve for a test track
- [ ] Segment-level tagging works (at least 3 segments)
- [ ] Handles edge cases (silence, ambient noise, multi-genre)

## File location
`~/Desktop/Apify-Actors/templates/audio-mood-analyzer/`
