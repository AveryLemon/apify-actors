# OWL Apify Actor Factory — AGENTS.md

> **If I am ever wiped:** Read TICKET.md → TIMELINE.md → HANDOFF.md in order. Then pick the highest priority 🔲 ticket from TICKET.md.

## Project Structure

```
~/Desktop/Apify-Actors/
├── templates/          # Ready-to-build actor source code
│   ├── aesthetic-music-tagger/   # Audio → mood/energy tags ✅ LIVE
│   ├── album-art-analyzer/       # Image → color harmony ✅ LIVE
│   └── playlist-optimizer/       # Tracks → optimized order ✅ LIVE
├── deployed/           # Symlinks or notes for deployed actors
├── ideas/              # Brainstormed actor concepts
├── references/         # Competitive intelligence, strategy docs
│   ├── apify-competitive-intelligence.md   # Living siphoning document
│   └── apify-actor-monetization.md         # Revenue/payout reference
├── TICKETS/            # Active tickets (follow TICKET.md queue)
├── TICKET.md           # Master queue — read this first
├── TIMELINE.md         # Chronological decision log
├── HANDOFF.md          # Session handoff state — resume here
├── AGENTS.md           # This file
└── README.md           # Project overview
```

## How to Work Here (Every Session)

1. **Read TICKET.md** — Check what's pending, in progress, completed
2. **Read TIMELINE.md** — Understand what happened and why
3. **Read HANDOFF.md** — Get current state, next actions
4. **Pick highest priority 🔲 ticket** (P0 before P1 before P2)
5. **Read the ticket file** in TICKETS/
6. **Execute** — build, push, document
7. **Run tests** — `python3 test_*.py` from the actor's directory. ALL must pass before marking complete.
8. **Mark complete** in TICKET.md
9. **Update TIMELINE.md** — Add entry with time + event + impact
10. **Update HANDOFF.md** — Reflect new current state
11. **Commit** if code changes
12. **Re-push** if code changed (the push updates the live actor)

## Key Commands

```bash
apify push --wait-for-finish=300   # Build + deploy in current directory
apify actors                        # List your actors
apify logs <actor-id>               # View run logs
```

## Competitive Siphoning Protocol

Every work session should also check the competitive intel:
1. Read references/apify-competitive-intelligence.md
2. Check if any gaps have been filled by competitors
3. Update the ERRC grid
4. Create tickets for new gaps

## Security Rules (NON-NEGOTIABLE)

- **NO factory code** in any actor
- **NO pipeline code** in any actor
- **NO brand strategy** in any actor
- **NO calls to OWL private APIs**
- Actors call only public APIs or do local processing

## Known Issues

- Actors are live but NOT YET PRICED — need to set monetization in Apify Console
- First 10 P0/P1/P2 tickets waiting for nightly cron or manual work
- Apify CLI version: 1.7.0

## Cron Schedule

| Time | Job | What It Does |
|------|-----|-------------|
| :00 every hour | OWL Hourly Guardian | Health check → if healthy, work tickets for < 1hr |
| 05:00 daily | Apify Actor Factory | BUILD → SIPHON → TICKET cycle |
| 07:00 daily | Evolution Engine | Skill research + Apify intelligence |
| 11:00 daily | Timeline + Sync | Update TIMELINE.md + HANDOFF.md + git push |

## Resources

- Apify Console: https://console.apify.com
- Actor ID: h0wFrE8woQSA8aNgd
- Apify login: peaceful_campanile (token in OS keyring)
- Docs: https://docs.apify.com
