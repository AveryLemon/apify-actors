# P2-3: Build Voice Cloning Actor

**Status: 🚫 KILLED** (July 4, 2026 — Hourly Guardian 08:03)

**Kill reason:** Fails Architectural Feasibility Assessment Q1 (GPU requirement).

The ticket proposed OpenVoice or Coqui TTS XTTS — both require PyTorch/CUDA. Apify Docker containers have NO GPU. Voice cloning is fundamentally a GPU-based task (neural audio processing, speaker embedding, vocoder inference). The lightweight alternatives (gTTS, Kokoro ONNX) do not support voice cloning. This actor cannot run on Apify.

**Replacement:** None viable. Voice cloning requires GPU inference or a stable external API (ElevenLabs). See also P1-6 (TTS Voiceover Actor) which handles TTS without voice cloning via gTTS — the closest buildable alternative.

## Original Ticket (for reference)

## Goal
Build an Apify actor that clones a voice from a short audio sample (30-120 seconds) and generates new speech in that voice.

## Why
Frontier tech. Zero competition on Apify. ElevenLabs proves massive demand. High-value, higher-priced. $1.00-3.00/run.

## Verification
- [ ] Actor builds on push
- [ ] Cloned voice is recognizable from a 30s sample
- [ ] Generated speech has natural intonation
- [ ] Handles multiple languages (if model supports)
