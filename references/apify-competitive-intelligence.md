# Apify Competitive Intelligence — Updated July 4, 2026

> **Living document.** Every siphon session updates this file. Gaps found create tickets in TICKETS/.

## Competitive Landscape Overview

The Apify Store has **47,173 actors** — overwhelmingly **web scrapers** (95%+). The AI/Creative category has ~6,337 actors, but the vast majority of those are also scrapers labeled as "AI" because they feed LLM pipelines.

**Key insight for OWL:** The creative/analysis niche is virtually empty. Audio tools have 3 actors total. Image analysis beyond OCR has ~5 actors. Video generation: zero. This is OWL's blue ocean.

---

## Category 1: Web Scraping (Top 10 by runs — all scrapers)

| # | Actor | Developer | Users | Price | Notes |
|---|-------|-----------|-------|-------|-------|
| 1 | Google Maps Scraper | compass | 426K+ | $2.10/1K | Most popular on platform |
| 2 | Instagram Scraper | apify | 276K+ | $2.30/1K | Official Apify actor |
| 3 | TikTok Scraper | clockworks | 185K+ | PPE | Social media data |
| 4 | Instagram Profile Scraper | apify | 138K+ | $1.60-2.60/1K | Official |
| 5 | Google Search Results Scraper | apify | 129K+ | $1.80/1K | Also in AI category |
| 6 | Website Content Crawler | apify | 127K+ | $0.20-5/1K | Feeds LLM pipelines |
| 7 | Web Scraper | apify | 117K+ | Platform only | Generic |
| 8 | Instagram Reel Scraper | apify | 102K+ | PPR | — |
| 9 | Instagram Post Scraper | apify | 95K+ | PPR | — |
| 10 | LinkedIn Jobs Scraper | curious_coder | 84K+ | PPR | — |

**OUR ENTRY STRATEGY:** Do NOT compete in scraping. OWL builds creative/analysis tools only.

---

## Category 2: Image Analysis (Existing Actors)

| Actor | Developer | What It Does | Runs | Gaps |
|-------|-----------|-------------|------|------|
| AI Image Intel (SEO) | marielise.dev | Alt text, SEO metadata via GPT-4o | Low | Text metadata only, no aesthetic analysis |
| Analyze Image | akash9078 | Objects, colors, emotions | Low | Shallow analysis, no composition scoring |
| Image-to-text | calm_necessity | Scene descriptions | Low | Basic captioning only |
| Image Captioner | HumbleIgnite | Molmo 2-based captions | Low | Single model, no comparison |
| Face Recognition | syntellect_ai | DeepFace-based | Low | Niche use case |
| Image Quality | marielise.dev | Photo quality score | Low | No style/aesthetic assessment |
| Text-to-Image | mult. actors | Image generation (Flux, Imagen) | Medium | No branded/consistent style gen |
| Image Upscaler | akash9078 | Face restoration | Low | No batch processing |
| Image Compressor | lighterimage | WebP batch compression | Low | — |

**OUR ENTRY STRATEGY:** Aesthetic/style analysis (unique), brand consistency scoring, multi-model comparison.

---

## Category 3: Audio/Music (Existing Actors — CRITICALLY EMPTY)

| Actor | Developer | What It Does | Runs | Gaps |
|-------|-----------|-------------|------|------|
| dj-track-audio-analyzer | musicae | BPM, key, Camelot, DJ scores from Spotify | Low | Spotify-only, no audio file upload |
| speech-to-text | hgservices | Whisper transcription | Low | Many alternatives exist |
| podcast-transcriber | hgservices | Podcast transcription | Low | Niche of a niche |
| YouTube Audio Segment Downloader | entertained_rattlesnake | Download + transcribe | 17 runs | Near zero adoption |
| AI Music Studio Generator | singlesurge | Music generation + remix | Very new | Only 1 competitor |
| Audio Overlayer | dead_minds | Overlay audio files | Zero | Dead product |

**BLUE OCEAN: 7+ high-value audio gaps with ZERO competition.**

---

## Category 4: Video (Existing Actors)

| Actor | What It Does | Gaps |
|-------|-------------|------|
| TikTok Viral AI Hunter | Video hook analysis | Only TikTok, analysis only |
| YouTube scrapers | Metadata, transcripts | Data extraction only |

**BLUE OCEAN: Whole video generation + analysis category is empty.**

---

## Feature Matrix: Audio Analysis Actors

| Feature | musicae dj-track | gservices STT | OWL (planned) |
|---------|-----------------|---------------|---------------|
| BPM detection | ✅ (Spotify) | ❌ | ✅ (audio file) |
| Key detection | ✅ (Spotify) | ❌ | ✅ (audio file) |
| Mood/emotion analysis | ❌ | ❌ | ✅ — UNIQUE |
| Energy curve | ❌ | ❌ | ✅ — UNIQUE |
| Stem separation | ❌ | ❌ | ✅ — UNIQUE |
| Genre classification | ❌ | ❌ | ✅ |
| Segment-level analysis | ❌ | ❌ | ✅ — UNIQUE |
| Works with uploaded audio | ❌ | ✅ | ✅ |
| Works with Spotify/URL | ✅ | ❌ | ✅ |
| Batch processing | ❌ | ❌ | ✅ — UNIQUE |

**OWL's competitive moat:** Full audio analysis from ANY source (URL or upload), with music-specific features no Apify actor offers.

---

## Feature Matrix: Image Analysis Actors

| Feature | akash9078 | marielise | HumbleIgnite | OWL (planned) |
|---------|-----------|-----------|-------------|---------------|
| Object detection | ✅ | ❌ | ❌ | — |
| Color extraction | ✅ | ❌ | ❌ | ✅ (refined) |
| Emotion detection | ✅ | ❌ | ❌ | ✅ (deeper) |
| Aesthetic scoring | ❌ | ❌ | ❌ | ✅ — UNIQUE |
| Composition analysis | ❌ | ❌ | ❌ | ✅ — UNIQUE |
| Style classification | ❌ | ❌ | ❌ | ✅ — UNIQUE |
| Brand consistency | ❌ | ❌ | ❌ | ✅ — UNIQUE |
| Alt text generation | ❌ | ✅ | ❌ | — |
| Scene description | ✅ | ❌ | ✅ | — |
| Quality score | ❌ | ✅ | ❌ | — |

**OWL's competitive moat:** Aesthetic intelligence — no competitor scores images for beauty, composition, or style.

---

## ERRC Grid

| ELIMINATE | RAISE |
|-----------|-------|
| Generic/shallow analysis (single metric) | Aesthetic depth — score EVERY dimension |
| "It works on Spotify" limitation | Works with ANY audio source |
| Single model dependency | Multi-model comparison (best-of-N) |
| Poor documentation | Beautiful, professional README for every actor |
| Zero input validation | Graceful error handling for every edge case |

| REDUCE | CREATE |
|--------|--------|
| Feature bloat (do one thing perfectly per actor) | Aesthetic/style analysis — no Apify actor does this |
| Compute cost per run | Music segment-level mood/energy profiling |
| Time to first run | Stem separation from any audio URL |
| | Brand consistency scoring |
| | Content repurposing pipeline (video→clips→social) |
| | Cross-modal analysis (audio + image together) |

---

## Gaps Identified (All Blue Ocean)

### 🔥 P0 Gaps — Direct Revenue Opportunities

| # | Gap | Why | Estimated Price |
|---|-----|-----|----------------|
| G-01 | **Stem Separation Actor** | No Apify actor. Massive creator/producer demand. LALAL.AI proves the market. | $0.50-1.00/run |
| G-02 | **Audio Mood/Emotion Analysis Actor** | No competitor. OWL's aesthetic engine directly applicable. Mood profile + energy curve. | $0.50/run |
| G-03 | **Aesthetic / Style Analysis Actor** | No competitor. Score images for composition, style, beauty. Brand consistency checking. | $0.35-0.50/run |
| G-04 | **Music Generation with Brand Voice** | Suno/Udio-style but for brands. Generate consistent jingles/brand music. | $1.00-2.00/run |
| G-05 | **Background Removal + Enhancement** | Remove.bg for Apify. E-commerce product photos. Surprising gap. | $0.10-0.25/run |

### 🟡 P1 Gaps — High Value, This Month

| # | Gap | Why |
|---|-----|-----|
| G-06 | **Text-to-Speech / Voiceover Actor** | Zero existing actors. Podcastle/Descript trend. |
| G-07 | **Thumbnail CTR Analysis + Generator** | YouTube creator demand. No Apify competitor. |
| G-08 | **Content Repurposing Pipeline Actor** | Long vid→short clips, audiograms, quote cards. #1 creator need. |
| G-09 | **Voice Cloning Actor** | Frontier tech. No competition. |
| G-10 | **Video Scene Detection Actor** | Split video by scenes, analyze each. Enables downstream. |

### 🟢 P2 Gaps — This Quarter

| # | Gap | Why |
|---|-----|-----|
| G-11 | **Audio Watermarking Actor** | Content protection for creators. |
| G-12 | **Bulk Image Style Transfer Actor** | Marketing teams batch-processing. |
| G-13 | **Automated Subtitle/Caption Generator** | Accessibility + social media. |
| G-14 | **Podcast Production Pipeline Actor** | Transcribe→analyze→show notes→clips. |
| G-15 | **Cross-Modal Brand Analysis Actor** | Image + audio analysis together. |

---

## Key Competitors (to watch)

| Developer | Territory | Threat Level | Notes |
|-----------|-----------|-------------|-------|
| musicae | Spotify/DJ audio features | LOW — limited to Spotify API, no audio file analysis | |
| akash9078 | Image utilities (basic) | LOW — shallow analysis, broad but shallow collection | |
| marielise.dev | Image SEO/quality | LOW — narrow focus on SEO metadata | |
| milastream | Image generation | LOW — generation only, no analysis | |
| singlesurge | Music generation | MEDIUM — only 1 competitor, very new | |

**OWL's strategic advantage:** OWL is the ONLY developer on Apify doing deep creative *analysis* — aesthetic scoring, mood profiling, style classification, cross-modal brand intelligence. OWL's 11 actors cover audio analysis, image analysis, TTS, content repurposing, and brand analysis — all without GPU. Generation (music, voice cloning) moves to OWL's own GPU-equipped hardware.

---

## Siphoning Notes

### Musicae's dj-track-audio-analyzer — What to Steal
- **Input:** Spotify track URL → returns BPM, key, Camelot, rhythm, harmony, DJ scores
- **Weakness:** ONLY works with Spotify. NO audio file upload. NO mood/emotion. NO energy curve. NO stem separation.
- **Our move:** Build the same DJ-friendly output BUT from ANY audio source + add mood + add energy arc + add stem quality score.

### milastream's ai-image-generator — What to Steal
- **Input:** Text prompt → image
- **Weakness:** Generic text-to-image. No style consistency, no brand voice, no batch mode.
- **Our move:** Brand voice image generator — generate images consistent with a brand's existing visual identity.

### singlesurge's ai-music-studio-generator — What to Watch (NOW DEPRECATED)
- **Status:** Deprecated — confirms API-wrap fragility for music generation actors
- **Lesson for OWL:** Music generation requires GPU (not available on Apify Docker) or a stable external API (proven unstable). Both P1-10 (Music Gen) and P2-3 (Voice Cloning) have been killed for this reason.
- **OWL's revised move:** Focus on music *analysis* (librosa-based, no GPU) which OWL has mastered (Aesthetic Music Tagger, Audio Mood Analyzer). Generation moves to OWL's own GPU-equipped Windows machine.
- **Apify platform limitation confirmed:** Docker containers have NO GPU. Any actor requiring PyTorch/CUDA inference is unbuildable. Only analysis + lightweight ONNX (rembg, audio-separator) are viable.
- **Input:** Text prompt → song + remix + instrumental + cover art
- **Strength:** Multi-format output. First mover in music gen on Apify.
- **Weakness:** Generic prompts. No brand voice. No mood targeting.
- **Our move:** Mood-targeted music generation with brand consistency. "Generate brand-consistent background music for [brand] with [mood] energy."
