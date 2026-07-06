# OWL Apify Actor Factory — HANDOFF.md

> **If I am ever wiped or this session ends:** Read this file. It contains everything needed to resume work immediately.

---

> **Current State (July 6, 2026 — 10:02 EDT)**

### 🟢 System Status: HEALTHY — Phase 1 Complete (blue ocean uncontested) — 43rd consecutive cycle without change — RAM ✅ 88% — Swap ✅

| Metric | Value | Status |
|--------|-------|--------|
| Actors deployed | **11** ✅ LIVE | All buildable concepts exhausted |
| CI document | Updated July 5 — new entries: MultipleWords API-wrap proliferation, syntellect_ai, VastHornet, stanvanrooy6, BigAnomaly. All LOW/not-in-niche. | Current |
| Active tickets | **0** (2 killed, 3 deferred) | Nothing buildable remaining |
| Pending blocks | **Pricing not set** (needs Apify Console UI) | Blocking revenue |
|||| RAM on MacBook | ~88% free | ✅ Healthy |
||| Disk | 90Gi available | ✅ Healthy |
||| Swap | N/A (sysctl unavailable in sandbox) | ✅ RAM 88% suggests no swap pressure |
||| Consecutive cycles | **43** (blue ocean uncontested) | Steady state |

| Competitive watch | solutionssmart/brand-dna (SingleSurge — website brand DNA, deterministic, NOT creative analysis), syntellect_ai (transcription+entity), calm_necessity/HumbleIgnite/BoldBastion (MultipleWords API-wrap music gen — fragile), VastHornet (API-key TTS), stanvanrooy6 (OpenAI TTS). **All LOW threat — none in OWL's creative analysis niche.** | Blue ocean uncontested for 43 cycles ✅ |

### 🎯 Major Discovery: Phase 1 is Complete

**All 11 buildable Apify actor concepts from the competitive intelligence have been built and deployed.** The original queue of P0-P2 tickets is fully exhausted.

**Two tickets KILLED during this session:**
1. **P1-10 (Music Generation with Brand Voice)** — KILLED 🚫. Fails Architectural Feasibility Assessment Q1 (needs GPU for MusicGen/AudioCraft). API-wrap alternative (Suno/Udio) proven fragile by singlesurge's deprecation. Unbuildable on Apify.
2. **P2-3 (Voice Cloning Actor)** — KILLED 🚫. Fails Q1 (needs GPU for OpenVoice/Coqui XTTS). No lightweight alternative exists.

**Key lesson:** Apify Docker containers have NO GPU. OWL's Apify strategy must focus exclusively on analysis actors (librosa, Pillow, numpy — zero GPU). Generation belongs on OWL's own GPU-equipped Windows machine or GPU cloud platforms (Replicate, RunPod).

### What's Blocking Revenue

| Block | Why | Resolution |
|-------|-----|-----------|
| **Pricing not set** | Apify Console UI task. CLI can't set monetization. | El opens Apify Console → Publication → Monetization tab |
| **Zero runs** | All 11 actors have 0 runs. No data to improve. | Need pricing + organic discovery (~2-3 weeks) |

### What's Next (Priority Order)

1. **P2-1: Set pricing** (El needs to open Apify Console) — $0.25-$2.00/run depending on actor
2. **P1-12: Harness Evolution Loop** (research, needs deep-work session)
3. **P1-13: Fable 5 Distillation** (research, needs deep-work session)
4. **P2-5: Review first 30 days of data** (~August 3, 2026)

### Live Actors

| Actor | ID | Est. Price | URL |
|-------|----|-----------|-----|
| Aesthetic Music Tagger | h0wFrE8woQSA8aNgd | $0.50/run | console.apify.com/actors/h0wFrE8woQSA8aNgd |
| Album Art Analyzer | ZtUxIZxXufElQRqgy | $0.25/run | console.apify.com/actors/ZtUxIZxXufElQRqgy |
| Playlist Optimizer | vlMskrGqaZxQWG8bA | $0.50/run | console.apify.com/actors/vlMskrGqaZxQWG8bA |
| Audio Stem Separator | AYFB94Nxue2vKyEw2 | $0.50-1.00/run | console.apify.com/actors/AYFB94Nxue2vKyEw2 |
| Audio Mood & Emotion Analyzer | mukcZj7pJwD0IIjlJ | $0.50/run | console.apify.com/actors/mukcZj7pJwD0IIjlJ |
| Aesthetic / Style Image Analyzer | zFzZXfqc9UYrY5g1g | $0.35-0.50/run | console.apify.com/actors/zFzZXfqc9UYrY5g1g |
| TTS Voiceover Actor | 10oHuq7lwZtiI5Pez | $0.25-0.50/run | console.apify.com/actors/10oHuq7lwZtiI5Pez |
| Thumbnail CTR Analyzer & Generator | sWkbZ6LeeiPB1b9g8 | $0.35-0.75/run | console.apify.com/actors/sWkbZ6LeeiPB1b9g8 |
| Content Repurposing Pipeline | pdixlDky3LLQnV3pT | $1.00-2.00/run | console.apify.com/actors/pdixlDky3LLQnV3pT |
| Background Remover + Enhancer | mgM54dnMGYKhSaCmP | $0.10-0.25/run | console.apify.com/actors/mgM54dnMGYKhSaCmP |
| Cross-Modal Brand Consistency Analyzer | vd6vmcwEVoYMvQpST | $0.75-1.50/run | console.apify.com/actors/vd6vmcwEVoYMvQpST |

**⚠️ ALL 11 need pricing set in Apify Console → Publication tab → Monetization**

---

## How to Resume Work

### If Phase 2 (pricing is set and data flows):
1. Check run counts: `apify actors ls`
2. Check for competitors: browse Apify Store AI category
3. P2-5: analyze 30 days of data, kill bottom performers, iterate winners

### If Phase 1 continuation (new buildable idea found):
1. Read TICKET.md, verify ticket doesn't exist
2. Run feasibility assessment (Q1-Q5 from apify-actor-builder skill)
3. If passes: build, test, push, document

### If new intelligence needed:
1. Load apify-actor-builder skill
2. Siphon Apify Store AI category for new entrants
3. Create tickets for buildable gaps

---

## Key Files & Commands

| What | Path/Command |
|------|-------------|
| Project root | ~/Desktop/Apify-Actors/ |
| Ticket queue | TICKET.md |
| Detailed tickets | TICKETS/P{priority}-{seq}-{slug}.md |
| Competitive intel | references/apify-competitive-intelligence.md |
| AGENTS.md | AGENTS.md |
| TIMELINE.md | TIMELINE.md |
| This file | HANDOFF.md |
| Actor templates | templates/{actor-name}/ |
| Push actor | `cd templates/{actor-name} && apify push --wait-for-finish=300` |
| Apify console | https://console.apify.com |
| Apify login | peaceful_campanile (token in OS keyring) |
