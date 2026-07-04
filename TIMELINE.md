# OWL Apify Actor Factory — TIMELINE.md

> **Chronological decision log.** Updated every session. If I am ever wiped, this is what happened and why.

---

### 05:00 EDT — Hourly Guardian — Health check only (gate: cron window)

| Time | Event | Impact |
|------|-------|--------|
| 05:00 | **Health check** — RAM 87%, disk 117Gi, no processes, swap 48% used | RAM ✅ Disk ✅ Processes ✅ |
| 05:00 | **Gate: 04:50-05:20 cron window** — 5AM Apify Actor Factory owns this slot | ⏭️ Skipping ticket work, deferring to 5AM cron |
| 05:00 | Updated HANDOFF.md with current state | Documentation fresh |

### 04:00 EDT — Hourly Guardian — P1-9: Background Removal + Enhancement COMPLETED

| Time | Event | Impact |
|------|-------|--------|
| 04:00 | **Health check** — RAM 87%, disk 117Gi, no processes | ✅ Gate passed |
| 04:00 | **P1-9: Background Remover pushed — SUCCEEDED ✅** (build 1.0.1) | **TENTH ACTOR LIVE** at console.apify.com/actors/mgM54dnMGYKhSaCmP |
| 04:00 | 61/61 unit tests ALL PASSED before push | Quality verified |
| 04:00 | ~50s total build (10s apt-build-essential + 18s pip + 22s push) | Reasonable build time |
| 04:00 | Actor shows `mgM54dnMGYKhSaCmP` | Ready for monetization |

### Key Decisions
1. **Decision:** Used rembg (ONNX-based) for background removal with Pillow for compositing/enhancement. Dropped shadow uses Gaussian blur on alpha channel. (Rationale: rembg is the most mature Python bg-removal package. ONNX runtime avoids the 2.9GB torch dependency. Build-essential added for ONNX C extensions — turns out rembg brings numba+pymatting+scikit-image which all need gcc. Overall build time is still reasonable at ~50s.)

### Known Issues
- P1-9 (Background Remover) is live but NOT priced/published to Store yet
- **10 actors live, 10 pending tickets** (P1-10 through P2-5)
- All 10 actors need pricing set in Apify Console → Publication tab → Monetization

---

### 07:04 UTC — Hourly Guardian — P1-8: Content Repurposing Pipeline COMPLETED

| Time | Event | Impact |
|------|-------|--------|
| 07:04 | **Health check** — RAM 87%, disk 117Gi, no processes | ✅ Gate passed |
| 07:04 | **P1-8: Content Repurposing Pipeline pushed — SUCCEEDED ✅** (build 1.0.1) | **NINTH ACTOR LIVE** at console.apify.com/actors/pdixlDky3LLQnV3pT |
| 07:04 | 50/50 unit tests ALL PASSED before push | Quality verified |
| 07:04 | ~60s total build (ffmpeg install 36s, pip install 7.6s, push 18s) | Reasonable build time |
| 07:04 | Actor shows `pdixlDky3LLQnV3pT` | Ready for monetization |

### Key Decisions
1. **Decision:** Built Content Repurposing Pipeline with Pillow+gTTS+yt-dlp — pure Python dependencies, no GPU needed. Quote cards use Pillow for image generation, gTTS for audiogram audio, yt-dlp for YouTube metadata/transcript extraction. (Rationale: Zero ML model loading, fully serverless. ffmpeg install adds 455MB to image but enables yt-dlp subtitles extraction.)

### Known Issues
- P1-8 (Content Repurposer) is live but NOT priced/published to Store yet
- **9 actors live, 11 pending tickets** (P1-9 through P2-5)
- All 9 actors need pricing set in Apify Console → Publication tab → Monetization

---

## 2026-07-04 — Empire Launch Day (continued)

### 02:12 EDT — Hourly Guardian
| Time | Event | Impact |
|------|-------|--------|
| 02:12 | **Health check** — RAM 87%, disk 117Gi, no processes | ✅ Gate passed |
| 02:12 | **P1-7: Thumbnail CTR Analyzer pushed — SUCCEEDED ✅** (build 1.0.1) | **EIGHTH ACTOR LIVE** at console.apify.com/actors/sWkbZ6LeeiPB1b9g8 |
| 02:12 | 63/63 unit tests ALL PASSED before push | Quality verified |
| 02:12 | 17s Docker build (Pillow+numpy, no C extensions) | Fast deployment |

### Key Decisions
1. **Decision:** Built Thumbnail CTR Analyzer using pure Pillow+numpy heuristics (no ML models). (Rationale: Zero C extension deps, 17s build, fully deterministic analysis. Face detection via HSV skin-color heuristic avoids dlib/gcc dependency.)

### Known Issues
- P1-7 (Thumbnail CTR Analyzer) is live but NOT priced/published to Store yet
- **8 actors live, 10 pending tickets** (P1-8 through P2-5)

---

### 01:06 UTC — Hourly Guardian

### 🎯 Major Milestones

| Time | Event | Impact |
|------|-------|--------|
| Pre-session | Apify CLI v1.7.0 installed, Python SDK v3.4.1 installed | Foundation |
| Pre-session | 3 actor templates built (aesthetic-music-tagger, album-art-analyzer, playlist-optimizer) | First code |
| Pre-session | 4 failed build attempts on aesthetic-music-tagger (actor.json schema issues) | Painful learning |
| Pre-session | actor.json fixed: version="1.0" (not "1.0.0"), envVars={} (not []), schemaVersion=1 (int) | Critical fix |
| Pre-session | Logged into Apify as peaceful_campanile | Auth established |
| Pre-session | Created apify-actor-builder skill & nightly cron | Infrastructure |
| 22:30 | **Full competitive siphoning: 3 parallel research tasks** | Intelligence |
| 22:30 | AI category: 6,337 actors mapped — <100 are creative/analysis | Blue ocean confirmed |
| 22:30 | Audio/music actors: only 3 exist (musicae dj-track, 2 transcribers) | 7+ gaps identified |
| 22:30 | Image analysis actors: 9 exist — NO aesthetic/style scoring | Competitive moat |
| 22:40 | **Written competitive intelligence doc** (10K+ words, feature matrices, ERRC grid) | Strategic asset |
| 22:40 | **10 new tickets created** (P0-3 through P2-4) | Ready queue |
| 22:41 | **PUSH aesthetic-music-tagger — SUCCEEDED ✅** (build 1.0.4) | FIRST ACTOR LIVE |
| 22:43 | **PUSH album-art-analyzer — SUCCEEDED ✅** (build 1.0.1) | SECOND ACTOR LIVE |
| 22:43 | **PUSH playlist-optimizer — SUCCEEDED ✅** (build 1.0.1) | THIRD ACTOR LIVE |
| 22:45 | TICKET.md updated with all live actors and new P0/P1/P2 queue | System current |
| 22:50 | 5AM nightly cron updated: BUILD→SIPHON→TICKET cycle with workdir | Automation |
| 22:50 | 7AM Evolution Engine updated: includes Apify intelligence siphon | Cross-pollination |
| 21:04 | **Hourly Guardian — PUSH stem-separator — SUCCEEDED ✅** (build 1.0.3) | FOURTH ACTOR LIVE at console.apify.com/actors/AYFB94Nxue2vKyEw2 |
|| 22:03 | **Hourly Guardian — P0-4: Build Audio Mood Analyzer — SUCCEEDED ✅** (build 1.0.1) | FIFTH ACTOR LIVE at console.apify.com/actors/mukcZj7pJwD0IIjlJ |
|| 23:01 | **Hourly Guardian — P0-5: Build Aesthetic Style Analyzer — SUCCEEDED ✅** (build 1.0.1) | **SIXTH ACTOR LIVE** at console.apify.com/actors/zFzZXfqc9UYrY5g1g |

### 🔑 Key Decisions Made

1. **Decision: Build 10+ actors, let 80/20 rule work.** (Rationale: Apify pays out $1.2M/month. Volume + patience = winners.)
2. **Decision: No factory/brand/pipeline code in any actor.** (Rationale: Zero IP exposure risk.)
3. **Decision: IT department model with tickets for everything.** (Rationale: User directive. Nothing forgotten.)
4. **Decision: Audio/music creative tools as primary blue ocean.** (Rationale: Critically empty on Apify. OWL has methodology.)
5. **Decision: No scraping actors, ever.** (Rationale: Red ocean. OWL's edge is creative analysis.)

|### 🚧 Known Issues
- Actors live but NOT yet priced/published to Store (need Apify Console UI)
- Actors currently at $0/run (free) — no revenue until priced
- 7 actors live, 12 pending tickets (P1-7 is next priority)

---

---

## 2026-07-04 — 08:03 EDT — Hourly Guardian — Phase 1 Complete

| Time | Event | Impact |
|------|-------|--------|
| 08:03 | **Health check** — RAM 86%, disk 117Gi, 0 processes | ✅ All gates pass |

### Phase 1 Complete — All 11 Buildable Actors LIVE

| Time | Event | Impact |
|------|-------|--------|
| 08:03 | **P1-10: Music Generation with Brand Voice** — 🚫 **KILLED** | Fails Q1 (GPU required for MusicGen/AudioCraft). Fails Q2 (API-wrap fragile — singlesurge deprecation). Apify Docker has NO GPU. |
| 08:03 | **P2-3: Voice Cloning Actor** — 🚫 **KILLED** | Fails Q1 (GPU required for OpenVoice/Coqui XTTS). No lightweight alternative. |
| 08:03 | **P2-4: Cross-Modal Brand Consistency Analyzer** — ✅ **CONFIRMED LIVE** | Already pushed (build 1.0.1, 57/57 tests pass). **11th actor LIVE.** |
| 08:03 | **TICKET.md restructured** — Phase 1 complete section, killed tickets added, deferred tickets categorized | Documentation reflects real state |
| 08:03 | **Competitive intel updated** — singlesurge deprecation noted, OWL's strategic advantage revised to focus on analysis (not generation) | Strategic clarity |

### 🔑 Key Decisions

1. **Decision: Kill P1-10 (Music Generation) and P2-3 (Voice Cloning).** (Rationale: Apify Docker has NO GPU. Generation actors requiring PyTorch/CUDA are fundamentally unbuildable. Singlesurge's deprecation proves API-wrap actors are equally fragile. OWL's Apify strategy pivots to pure analysis.)**
2. **Decision: Phase 1 of Apify strategy is declared complete.** (Rationale: All 11 buildable concepts from competitive intelligence have been built and deployed. Remaining tickets are killed, UI-gated, or data-gated. Next work should focus on monetization (P2-1) or deep research (P1-12, P1-13).)
3. **Decision: Generation actors move to GPU-equipped hardware.** (Rationale: OWL's Windows RTX 4070 machine or GPU cloud — Replicate, RunPod, Banana — can handle music gen, voice cloning, and other generation tasks that Apify cannot support.)

### Known Issues
- All 11 actors are LIVE but NONE have pricing set — $0 revenue until El configures monetization in Apify Console
- TICKET.md, HANDOFF.md, TIMELINE.md all updated to reflect Phase 1 completion
- No new buildable Apify actor gaps remain — next siphon session should check for new competitors, not new gaps

| Time | Event | Impact |
||------|-------|--------|
|| 09:03 | **Health check** — RAM 86%, disk 117Gi, 0 processes | ✅ All gates pass |

### 09:03 EDT — Hourly Guardian — Health check only (Phase 1 complete, no tickets)

| Time | Event | Impact |
|------|-------|--------|
| 09:03 | **Health check** — RAM 86%, disk 117Gi, 0 processes, swap healthy | ✅ All gates pass |
| 09:03 | **Competitive siphon** — Found "AI Content Repurposer" by enezli @ $40/1K formats (Under maintenance) | ⚠️ Competitor exists but not active |
| 09:03 | **All 11 actors confirmed LIVE** — apify actors ls shows all with 0 runs | ✅ Ready for pricing |
| 09:03 | **TICKET.md, HANDOFF.md, TIMELINE.md all current** — no actionable tickets | ✅ Documentation reflects state |

### Key Decisions
1. **Decision:** No new tickets created — enezli's AI Content Repurposer is "Under maintenance" (broken/deprecated), not a viable competitor that demands counter-action. OWL's Content Repurposing Pipeline at a fraction of the price ($1-2/run vs $40/1k) has a different pricing model entirely. Blue ocean remains secure.

### Known Issues
- All 11 actors have 0 runs (not priced) — revenue blocked on Apify Console UI access

|---

## 2026-07-04 — 10:04 EDT — Hourly Guardian — Health check only (Phase 1 complete, no tickets)

| Time | Event | Impact |
|------|-------|--------|
| 10:04 | **Health check** — RAM 86%, disk 117Gi, 0 processes, swap healthy | ✅ All gates pass |
| 10:04 | **Competitive siphon** — Scanned Apify Store AI category (6,415 actors). No new creative/analysis entrants since last check. | ✅ Blue ocean remains uncontested |
| 10:04 | **All 11 actors confirmed LIVE** — 0 runs (not priced) | ✅ Phase 1 complete |
| 10:04 | **TICKET.md, HANDOFF.md, TIMELINE.md all current** — no actionable tickets | ✅ Documentation reflects state |

### Key Decisions
1. **Decision:** No new tickets created — competitive landscape unchanged. enezli's AI Content Repurposer still under maintenance. OWL's 11-actor beachhead remains uncontested in creative/analysis.
2. **Decision:** Continue hourly health-only checks until pricing is set (P2-1, blocking on El) or new intelligence appears.

### Known Issues
- All 11 actors have 0 runs (not priced) — revenue blocked on Apify Console UI access
