# OWL Apify Actor Factory — TIMELINE.md

> **Chronological decision log.** Updated every session. If I am ever wiped, this is what happened and why.

---

## 2026-07-04 — Empire Launch Day

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

### 🔑 Key Decisions Made

1. **Decision: Build 10+ actors, let 80/20 rule work.** (Rationale: Apify pays out $1.2M/month. Volume + patience = winners.)
2. **Decision: No factory/brand/pipeline code in any actor.** (Rationale: Zero IP exposure risk.)
3. **Decision: IT department model with tickets for everything.** (Rationale: User directive. Nothing forgotten.)
4. **Decision: Audio/music creative tools as primary blue ocean.** (Rationale: Critically empty on Apify. OWL has methodology.)
5. **Decision: No scraping actors, ever.** (Rationale: Red ocean. OWL's edge is creative analysis.)

### 🚧 Known Issues
- Actors live but NOT yet priced/published to Store (need Apify Console UI)
- actors currently at $0/run (free) — no revenue until priced
- 10 P0/P1/P2 tickets waiting for nightly cron

---

## Template for Future Entries

| Time | Event | Impact |
|------|-------|--------|
| HH:MM | Milestone | Effect |

### Key Decisions
1. **Decision:** (Rationale: reasoning.)

### Known Issues
- Issue description
