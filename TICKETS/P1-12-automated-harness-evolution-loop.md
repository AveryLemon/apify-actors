# P1-12: Automated Harness Evolution Loop

**Priority:** P1
**Source:** Siphoned from Hugging Face (Joel Niklaus) + tweet by @akshay_pachaar
**Date:** July 4, 2026
**Est. Revenue:** Indirect — cost optimization (7x cheaper per task than Sonnet 4.6, can run on local hardware)
**Status:** 🔲 Not Started

---

## What It Is

Hugging Face published a paper/space showing: **take a frozen open model scoring 0% on a hard legal agent benchmark, leave its weights alone, and let an automated loop rewrite only the code around it** (the harness/scaffold). The loop lifted it from 0% → 5.0% all-pass, and 63.4% → 80.1% criterion pass, matching Sonnet 4.6 at **7x lower cost**.

The key finding: **The benchmark score measures the model AND its harness together. Until the harness is fixed, you can't know which one failed.**

## Why It Matters for OWL

1. **Our album factory pipelines are harnesses** — the same model with a better harness (tool schema, file handling, context shaping) dramatically outperforms the same model with a bad one
2. **7x cost savings** without changing a single weight — this is pure infrastructure optimization
3. **Code fixes transfer across models; prompt playbooks do not** — fixing the harness once benefits all models
4. **"The harness matters more than anything else"** — 5 different harnesses on the same model scored 3.5% to 80.1%

## Key Findings Siphoned

| Finding | Implication for OWL |
|---------|-------------------|
| Biggest single gain: file handling (landing the deliverable exactly where the judge expects it) | Our actor output schemas must be bulletproof — auto-validate output location/format |
| Code fixes transferred across models (+14 points); prompt playbooks hurt different models | Build model-agnostic harnesses; keep prompts model-specific |
| 5 harnesses → 3.5% to 80.1% on same model | Our factory pipeline's orchestration layer IS the harness — optimize it |
| A Claude proposer adds one mechanism per iteration; outer loop keeps it only if it beats current best | This is exactly how our factory should evolve — atomic, measurable, compounding |
| Gains flatten — at some point the wrapper runs out of tricks | Know the ceiling; don't over-engineer the harness |

## Implementation Plan

### Phase 1: Audit OWL's Current Harnesses (2 hours)
1. Map every factory/actor pipeline's orchestration layer (the code that feeds context, runs tools, decides when a run ends)
2. For each pipeline, measure: what % of failures are harness failures vs model failures?
3. Create harness quality score for each pipeline

### Phase 2: Build Automated Harness Optimizer (4 hours)
1. Create `harness_optimizer.py` — an automated loop that:
   - Freezes the current model weights
   - Tests the current harness on a held-out set of tasks
   - Has a Claude proposer suggest one mechanism change per iteration
   - Tests the new harness — keeps it ONLY if it beats the current best
   - Compounds accepted mechanisms
2. Run on album factory pipeline first (highest ROI)

### Phase 3: Model-Agnostic Harness Library (6 hours)
1. Extract the winning harness patterns into a reusable library
2. Each harness must be testable on 3+ different models to verify transfer
3. Document: which harness mechanisms transfer, which are model-specific

### Phase 4: Integration with Apify Actors (4 hours)
1. Apply harness optimization to our 3 live actors
2. Measure: does a better harness for the same model increase pass rates?
3. If yes: this is a competitive moat — our actors use better infrastructure

## Acceptance Criteria
- [ ] Harness audit completed for album factory + 3 Apify actors
- [ ] Automated harness optimizer script created
- [ ] At least one pipeline shows measurable improvement from harness tuning alone
- [ ] Model-agnostic harness library documented
- [ ] Harness improvement transferred to at least 1 Apify actor

## ERRC Analysis (Applied to OWL's Infrastructure)

| ELIMINATE | RAISE |
|-----------|-------|
| Duplicate harness logic across factories/actors — each pipeline reinvents the same scaffolding | Output file handling — auto-validate deliverables land exactly where the judge/user expects |
| Model-specific prompt tuning that doesn't transfer (waste of tokens) | Harness quality as a first-class metric — benchmark the infrastructure, not just the model |

| REDUCE | CREATE |
|--------|--------|
| Manual harness tuning per pipeline (should be automated like the HF loop) | Automated Harness Optimizer — a Claude proposer that evolves the code around fixed models |
| Time spent wondering "is it the model or the harness?" | Model-agnostic harness library that transfers across all pipelines |

## Revenue Model
- **Direct:** None — this is infrastructure/cost optimization
- **Indirect:** 7x cost reduction on agent tasks, faster iteration on new pipelines, competitive moat for Apify actors (better harness = better output = more runs)
- **ROI estimate:** If our current agent costs are ~$50-100/month in API credits, this could save $40-85/month. More importantly: better harnesses mean faster iteration on revenue-generating actors.
