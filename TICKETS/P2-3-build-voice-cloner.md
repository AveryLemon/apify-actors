# P2-3: Build Voice Cloning Actor

## Goal
Build an Apify actor that clones a voice from a short audio sample (30-120 seconds) and generates new speech in that voice.

## Why
Frontier tech. Zero competition on Apify. ElevenLabs proves massive demand. High-value, higher-priced. $1.00-3.00/run.

## Approach
- Input: voice sample URL, text to speak
- Process: clone voice using open-source model (OpenVoice, Coqui TTS XTTS)
- Output: downloadable speech audio in the cloned voice
- Quality targets: < 30s sample needed, natural prosody, 16kHz+ output

## Verification
- [ ] Actor builds on push
- [ ] Cloned voice is recognizable from a 30s sample
- [ ] Generated speech has natural intonation
- [ ] Handles multiple languages (if model supports)

## File location
`~/Desktop/Apify-Actors/templates/voice-cloner/`
