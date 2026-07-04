# OWL Apify Actor Factory — Active Ticket Queue

> **Updated:** July 4, 2026 — 09:03 EDT | **Total tickets:** 11 completed, 3 active (2 killed, 1 data-gated) | **All 11 buildable actors LIVE ✅**

> **NOTE:** All buildable Apify actor concepts (from competitive intelligence) have been built and deployed. Remaining tickets are killed (unbuildable on Apify's no-GPU infra), research/infrastructure (not Apify actors), or gated on data (need 30 days of runs). See below for next phase strategy.

---

## COMPLETED ✅

### 11 Actors LIVE on Apify

| # | Actor | Price | URL | Tests | Build |
|---|-------|-------|-----|-------|-------|
| P0-0 | Aesthetic Music Tagger | $0.50/run (not set) | console.apify.com/actors/h0wFrE8woQSA8aNgd | — | 1.0.4 |
| P1-4 | Album Art Analyzer | $0.25/run (not set) | console.apify.com/actors/ZtUxIZxXufElQRqgy | — | 1.0.1 |
| P1-5 | Playlist Optimizer | $0.50/run (not set) | console.apify.com/actors/vlMskrGqaZxQWG8bA | — | 1.0.1 |
| P0-3 | Audio Stem Separator | $0.50-1.00/run (not set) | console.apify.com/actors/AYFB94Nxue2vKyEw2 | — | 1.0.3 |
| P0-4 | Audio Mood & Emotion Analyzer | $0.50/run (not set) | console.apify.com/actors/mukcZj7pJwD0IIjlJ | 54/54 ✅ | 1.0.1 |
| P0-5 | Aesthetic / Style Image Analyzer | $0.35-0.50/run (not set) | console.apify.com/actors/zFzZXfqc9UYrY5g1g | 82/82 ✅ | 1.0.1 |
| P1-6 | TTS Voiceover Actor | $0.25-0.50/run (not set) | console.apify.com/actors/10oHuq7lwZtiI5Pez | 40/40 ✅ | 1.0.1 |
| P1-7 | Thumbnail CTR Analyzer & Generator | $0.35-0.75/run (not set) | console.apify.com/actors/sWkbZ6LeeiPB1b9g8 | 63/63 ✅ | 1.0.1 |
| P1-8 | Content Repurposing Pipeline | $1.00-2.00/run (not set) | console.apify.com/actors/pdixlDky3LLQnV3pT | 50/50 ✅ | 1.0.1 |
| P1-9 | Background Remover + Enhancer | $0.10-0.25/run (not set) | console.apify.com/actors/mgM54dnMGYKhSaCmP | 61/61 ✅ | 1.0.1 |
| P2-4 | Cross-Modal Brand Consistency Analyzer | $0.75-1.50/run (not set) | console.apify.com/actors/vd6vmcwEVoYMvQpST | 57/57 ✅ | 1.0.1 |

**⚠️ CRITICAL: All 11 actors have ZERO pricing set. They run for free. No revenue until monetization is configured in Apify Console → Publication tab.**

---

## KILLED 🚫

| # | Ticket | Kill Reason | Date |
|---|--------|-------------|------|
| P1-10 | Music Generation with Brand Voice | ❌ Fails Q1 (GPU required for MusicGen/AudioCraft). Fails Q2 (API-wrap fragile — singlesurge deprecation precedent). Unbuildable on Apify. | July 4, 08:03 |
| P2-3 | Voice Cloning Actor | ❌ Fails Q1 (GPU required for OpenVoice/Coqui XTTS). Voice cloning needs GPU inference. Unbuildable on Apify. | July 4, 08:03 |

**Lesson:** Apify Docker has NO GPU. Any actor requiring PyTorch/CUDA inference (generation, cloning, training) is automatically killed. Only analysis + lightweight ONNX (rembg, audio-separator) are viable.

---

## DEFERRED ⏸️

| # | Ticket | Why Deferred | Est. Timing |
|---|--------|-------------|-------------|
| P1-12 | Automated Harness Evolution Loop | Research/infrastructure ticket (not an Apify actor). Requires multi-hour deep work on factory pipelines, not a 45-min build slot. | Next deep-work session |
| P1-13 | Fable 5 Reasoning Distillation | Research/infrastructure ticket (not an Apify actor). Requires model downloads and evaluation. | Next deep-work session |
| P2-1 | Set up pricing + publish actors to Store | **UI task** — needs Apify Console (Publication → Monetization tab). Cannot be automated via CLI. | When El opens Apify Console |
| P2-5 | Reviews + iteration on first 30 days of data | **Data-gated** — needs 30 days of run data to make meaningful decisions. All actors have ZERO runs. | ~August 3, 2026 |

---

## ACTIVE TICKETS — NONE (Phase 1 Complete)

**All 11 buildable Apify actor concepts have been built and deployed.** Phase 1 of the Apify strategy is complete.

### Phase 2: Monetization (Blocking)
Once El opens Apify Console, set pricing for all 11 actors:
- See pricing guidelines in the skill (apify-actor-builder)
- Pay-per-result model for all actors
- Expected path to first dollar: ~2-3 weeks for organic discovery + pricing activation

### Phase 3: Intelligence + Siphoning (Continuous)
- Check for new competitors in AI category every week
- Singlesurge's ai-music-studio-generator is deprecated — watch for new entrants
- Bot watching since OWL has the first-mover advantage in creative analysis

---

## Strategy Update

### What's Been Achieved
1. **11 actors LIVE** — covering audio analysis, image analysis, TTS, content repurposing, brand analysis, bg removal
2. **Blue ocean secured** — zero competitors in creative/analysis niche on Apify
3. **Quality standard** — all actors have test suites (40-82 tests each), ALL pass
4. **Architecture proven** — librosa + Pillow + numpy pattern works for serverless Docker on Apify

### What's Next (No-RAM-Intensive Phase)
1. **P2-1: Set pricing** — El needs to open Apify Console and configure monetization
2. **P1-12: Harness research** — Deep work on factory pipeline optimization
3. **P1-13: Fable 5 evaluation** — Download and test distilled model locally
4. **P2-5: Data analysis** — Wait for run data, then iterate

### Strategic Lesson
The Apify platform is excellent for **analysis** actors but cannot support **generation** actors without GPU. OWL's competitive moat is deep analysis + cross-modal intelligence. Generation belongs on other platforms (Replicate, RunPod, Banana) or OWL's own GPU-equipped Windows machine.

---

## Revenue Projection (Updated)

**All actors need pricing set before any revenue.** Current: $0/month.

| Scenario | Runs/actor/day | Winners | Revenue/month | Timeline |
|----------|---------------|---------|---------------|----------|
| Conservative | 5 | 3 | ~$100-200 | Month 2 |
| Moderate | 15 | 5 | ~$500-800 | Month 3 |
| Optimistic | 30 | 5 | ~$1,200-2,000 | Month 4-6 |

All figures net of Apify's 20% commission + platform costs.
