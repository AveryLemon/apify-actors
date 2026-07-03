# OWL Apify Actor Factory — Active Ticket Queue

> **Updated:** July 4, 2026 | **Total tickets:** 3 completed, 15 active | **Priority:** P0 first, then P1, then P2

---

## COMPLETED ✅

### P0-0: Initial Actor Scaffolding — COMPLETED ✅
- Built 3 actor templates (aesthetic-music-tagger, album-art-analyzer, playlist-optimizer)
- Installed Apify CLI (1.7.0) and Python SDK (3.4.1)
- Created ~/Desktop/Apify-Actors/ structure
- Logged into Apify as peaceful_campanile
- Created dedicated apify-actor-builder skill
- Created nightly cron job for Apify Actor Factory (5AM daily)

### P0-0b: Competitive Siphoning + Ticketing Infrastructure — COMPLETED ✅
- Loaded owl-blue-ocean-siphon framework
- Created TICKETS/ directory
- Wrote this TICKET.md queue

### P0-1: Siphon Top 5 Apify Actors by Category — COMPLETED ✅
- Siphoned full AI category (6,337 actors mapped)
- Siphoned top 10 by runs (all scrapers)
- Siphoned audio/music actors (6 total — critically empty)
- Siphoned image analysis actors (9 total — no aesthetic analysis)
- Built feature matrices for audio + image
- Built ERRC grid with 4 quadrants
- Identified 15 gaps (5 P0, 5 P1, 5 P2)
- Wrote living competitive intelligence doc at references/apify-competitive-intelligence.md

---

## ACTIVE TICKETS

### 🔴 P0 — Do This Week (Critical)

| # | Ticket | Est. Price | Status |
|---|--------|-----------|--------|
| P0-2 | Push Aesthetic Music Tagger | $0.50/run | ✅ LIVE at console.apify.com/actors/h0wFrE8woQSA8aNgd |
| P0-3 | Build Stem Separation Actor | $0.50-1.00/run | 🔲 Ready to code (nightly cron will build) |
| P0-4 | Build Audio Mood/Emotion Analysis Actor | $0.50/run | 🔲 Ready to code (nightly cron will build) |
| P0-5 | Build Aesthetic / Style Analysis Actor | $0.35-0.50/run | 🔲 Ready to code (nightly cron will build) |

**Why these are P0:** Direct revenue opportunities with ZERO competitors. OWL has existing methodology for audio/image aesthetic analysis. The competitive moat is widest here.

### 🟡 P1 — This Month (High Value)

| # | Ticket | Est. Price | Status |
|---|--------|-----------|--------|
| P1-4 | Push Album Art Analyzer | $0.25/run | ✅ LIVE at console.apify.com/actors/ZtUxIZxXufElQRqgy |
| P1-5 | Push Playlist Optimizer | $0.50/run | ✅ LIVE at console.apify.com/actors/vlMskrGqaZxQWG8bA |
| P1-6 | Build TTS / Voiceover Actor | $0.25-0.50/run | 🔲 Ready to code |
| P1-7 | Build Thumbnail CTR Analyzer + Generator | $0.35-0.75/run | 🔲 Ready to code |
| P1-8 | Build Content Repurposing Pipeline | $1.00-2.00/run | 🔲 Ready to code |
| P1-9 | Build Background Removal + Enhancement | $0.10-0.25/run | 🔲 Ready to code |
| P1-10 | Build Music Generation with Brand Voice | $1.00-2.00/run | 🔲 Ready to code |

**Why these are P1:** High-value opportunities but either have partial competition or more complex implementation. Build after P0 actors are live.

### 🟢 P2 — This Quarter (Growth)

| # | Ticket | Est. Price | Status |
|---|--------|-----------|--------|
| P2-1 | Set up pricing + publish all 3 initial actors | — | 🔲 Do after pushes succeed |
| P2-2 | Create 3 more actor ideas from siphon gaps | — | 🔲 Covered by gap analysis |
| P2-3 | Build Voice Cloning Actor | $1.00-3.00/run | 🔲 Ready to code |
| P2-4 | Build Cross-Modal Brand Analysis Actor | $0.75-1.50/run | 🔲 Ready to code |
| P2-5 | Reviews + iteration on first 30 days of data | — | 🔲 After actors are live |

**Why these are P2:** Frontier tech (voice cloning), complex multi-modal (brand analysis), or post-launch (reviews/iteration).

---

## Strategy: What to Build First

1. **P0-2: Push Aesthetic Music Tagger** — Already coded, just needs one successful push
2. **P0-3: Stem Separation** — Highest demand gap, zero competition, $0.50-1.00/run
3. **P0-4: Audio Mood Analyzer** — Direct OWL methodology port, $0.50/run
4. **P0-5: Aesthetic Style Analyzer** — Unique value prop, $0.35-0.50/run
5. After 4 P0 actors live → P1-4, P1-5 (push remaining initial actors)
6. Then P1-6 through P1-10 (TTS, thumbnail, repurposing, bg removal, brand music)
7. Then P2-3, P2-4 (frontier: voice cloning, cross-modal)

**Revenue projection at full deployment (15 actors):**
- Conservative: 5 runs/day average × $0.50 × 15 actors = $37.50/day = $1,125/month
- Moderate: 15 runs/day avg × $0.50 × 8 winners = $60/day = $1,800/month
- Optimistic: 30 runs/day avg × $0.50 × 5 winners = $75/day = $2,250/month

**All figures net of Apify's 20% commission + platform costs.**

---

## DETAILED TICKETS

### P0-2: Push Aesthetic Music Tagger

**Goal:** Complete the push of the first actor to Apify's production build system.

**Why:** We need at least one actor live to learn from real data (run counts, user feedback, earnings). The code is ready, .actor/actor.json is fixed.

**Files to modify:**
- `~/Desktop/Apify-Actors/templates/aesthetic-music-tagger/.actor/actor.json`

**Verification:**
- [ ] `apify push --wait-for-finish=300` returns SUCCEEDED
- [ ] Actor visible at https://console.apify.com/actors/h0wFrE8woQSA8aNgd
- [ ] Build number shows version 1.0.X with green checkmark

### P1-4: Album Art Analyzer — actor.json + push

**Goal:** Create .actor/actor.json for the Album Art Analyzer and push to Apify.

**Files to create:**
- `~/Desktop/Apify-Actors/templates/album-art-analyzer/.actor/actor.json`

**Verify:**
- [ ] `apify push --wait-for-finish=300` succeeds
- [ ] Actor visible in Apify Console

### P1-5: Playlist Optimizer — actor.json + push

**Goal:** Create .actor/actor.json for the Playlist Optimizer and push to Apify.

**Files to create:**
- `~/Desktop/Apify-Actors/templates/playlist-optimizer/.actor/actor.json`

**Verify:**
- [ ] `apify push --wait-for-finish=300` succeeds
- [ ] Actor visible in Apify Console
