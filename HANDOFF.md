# OWL Apify Actor Factory — HANDOFF.md

> **If I am ever wiped or this session ends:** Read this file. It contains everything needed to resume work immediately.

---

## Current State (July 4, 2026 — 22:50 UTC)

### 🟢 System Status: ALL SYSTEMS GO

| Metric | Value | Status |
|--------|-------|--------|
| Actors deployed | 3 ✅ LIVE | Ready for revenue |
| CI document | Full feature matrix + ERRC + 15 gaps | Strategic asset |
| Active tickets | 10 (2 P0, 6 P1, 2 P2) | Ready queue |
| Nightly cron | BUILD→SIPHON→TICKET at 5AM | Automated |
| Evolution cron | Apify siphoning at 7AM | Cross-pollination |
| RAM on MacBook | ~89% free | Healthy |

### 🎯 Next Priority Ticket: P0-3 (Stem Separation Actor)
Build an Apify actor that takes audio URL → separated stems (vocals/drums/bass/other).
- Est. price: $0.50-1.00/run
- Competition: ZERO (no Apify actor does this)
- Method: open-source Demucs/MVSEP/spleeter
- File: `~/Desktop/Apify-Actors/templates/stem-separator/`

---

## How to Resume Work

### Step 1: Quick Health Check
```bash
memory_pressure | grep "System-wide memory free percentage"
df -h / | tail -1
```

### Step 2: Load Context
```bash
# Read these files in order:
1. ~/Desktop/Apify-Actors/AGENTS.md
2. ~/Desktop/Apify-Actors/TICKET.md
3. ~/Desktop/Apify-Actors/TIMELINE.md
4. ~/Desktop/Apify-Actors/references/apify-competitive-intelligence.md
```

### Step 3: Pick Next Ticket
- P0 first, then P1, then P2
- Read the full ticket file at `~/Desktop/Apify-Actors/TICKETS/P{id}.md`
- Execute the build
- Mark ✅ in TICKET.md
- Update TIMELINE.md + HANDOFF.md

### Step 4: Document Everything
After each ticket completed, update:
1. TICKET.md (mark ✅, move to COMPLETED)
2. TIMELINE.md (add entry with time + event + impact)
3. HANDOFF.md (update Current State section)

---

## Live Actors

| Actor | ID | Price | Build | URL |
|-------|----|-------|-------|-----|
| Aesthetic Music Tagger | h0wFrE8woQSA8aNgd | $0.50/run (not yet set) | 1.0.4 | console.apify.com/actors/h0wFrE8woQSA8aNgd |
| Album Art Analyzer | ZtUxIZxXufElQRqgy | $0.25/run (not yet set) | 1.0.1 | console.apify.com/actors/ZtUxIZxXufElQRqgy |
| Playlist Optimizer | vlMskrGqaZxQWG8bA | $0.50/run (not yet set) | 1.0.1 | console.apify.com/actors/vlMskrGqaZxQWG8bA |

**⚠️ All 3 need pricing set in Apify Console → Publication tab → Monetization**

---

## Ticket Queue (as of handoff)

### 🔴 P0 — Critical
- P0-3: Stem Separation Actor 🔲 (next build target)
- P0-4: Audio Mood/Emotion Analysis Actor 🔲
- P0-5: Aesthetic / Style Analysis Actor 🔲

### 🟡 P1 — This Month
- P1-6: TTS Voiceover Actor 🔲
- P1-7: Thumbnail CTR Analyzer + Generator 🔲
- P1-8: Content Repurposing Pipeline 🔲
- P1-9: Background Removal + Enhancement 🔲
- P1-10: Music Generation with Brand Voice 🔲

### 🟢 P2 — This Quarter
- P2-3: Voice Cloning Actor 🔲
- P2-4: Cross-Modal Brand Analysis Actor 🔲

---

## Key Files & Commands

| What | Path/Command |
|------|-------------|
| Project root | ~/Desktop/Apify-Actors/ |
| Ticket queue | TICKET.md |
| Detailed tickets | TICKETS/P{priority}-{seq}-{slug}.md |
| Competitive intel | references/apify-competitive-intelligence.md |
| AGENTS.md | AGENTS.md (always read first) |
| TIMELINE.md | TIMELINE.md |
| This file | HANDOFF.md |
| Actor templates | templates/{actor-name}/ |
| Push actor | `cd templates/{actor-name} && apify push --wait-for-finish=300` |
| Apify console | https://console.apify.com |
| Apify login | peaceful_campanile (token in OS keyring) |
