# P1-6: Build Text-to-Speech / Voiceover Actor

## Goal
Build an Apify actor that converts text to natural-sounding speech with multiple voice options, SSML support, and downloadable WAV/MP3 output.

## Why
**Zero TTS actors on Apify Store.** Massive creator economy demand for voiceovers, narration, ads, audiobooks. Podcastle/Descript prove the market. $0.25-0.50/run.

## Approach
- Use open-source TTS (Coqui TTS, Piper, or MeloTTS API)
- Input: text, voice selection, speed, pitch, format
- Output: downloadable audio file (MP3/WAV)
- Voice presets: narrator, friendly, professional, energetic

## Verification
- [ ] Actor builds on push
- [ ] Generates clear, natural speech from text
- [ ] Multiple voice options work
- [ ] Edge cases: long text, special characters, multiple languages

## File location
`~/Desktop/Apify-Actors/templates/tts-voiceover-actor/`
