# P1-10: Build Music Generation with Brand Voice Actor

## Goal
Build an Apify actor that generates original music from text prompts, with genre/mood/tempo controls and brand voice consistency.

## Why
Singlesurge has the only music gen actor (very new). OWL can differentiate with brand voice consistency, mood targeting, and "generative remixing." $1.00-2.00/run.

## Approach
- Input: text prompt, genre, mood, tempo, duration, brand style reference (optional)
- Process: generate using open-source music gen model (MusicGen, AudioCraft)
- Output: downloadable MP3 + metadata (BPM, key, mood match score)
- Key differentiator: brand voice consistency — generate music that matches an existing sonic identity

## Verification
- [ ] Actor builds on push
- [ ] Generates music from a text prompt
- [ ] Genre/mood controls produce audibly different results
- [ ] Brand voice mode creates consistent outputs from same brand reference

## File location
`~/Desktop/Apify-Actors/templates/music-brand-generator/`
