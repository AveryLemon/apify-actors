# P1-13: Fable 5 Reasoning Distillation — Student Can Surpass Teacher

**Priority:** P1
**Source:** Siphoned from @waterloo_intern (ali/Baseten) tweet
**Date:** July 4, 2026
**Est. Revenue:** Indirect — local model capability upgrade for factory pipelines
**Status:** 🔲 Not Started

---

## What It Is

Baseten (ali/@waterloo_intern) distilled **2.3M Claude Fable 5 reasoning traces** into Qwen3-4B. Results:

- **100% self-consistency** @ 512 samples
- **0.00 bits output entropy**
- **Zero hallucination variance**
- **"The student is not bounded by the teacher"** — the distilled 4B model converged on a universal truth the teacher didn't find

They open-sourced the model weights.

A parallel project by Dhamodharan2006 on GitHub distilled **4,659 real agentic sessions** with Claude Fable-5's cleartext thinking traces into Qwen3-4B for coding/debugging/architecture tasks.

And Qwen + Fable shipped a **35B agentic coder with 3B active parameters** (MoE), combining Qwen3 weights with Claude Fable-5 tool-use behavior.

## Why It Matters for OWL

1. **Local inference breakthrough** — a 4B model with Fable-5 reasoning quality can run on our MacBook (24GB) at real-time speeds with ZERO API cost
2. **Zero hallucination variance** — this is the holy grail for production pipelines where output consistency matters
3. **Student > Teacher** — distilled models can generalize beyond the teacher's distribution. This breaks the assumption that bigger = better
4. **35B/3B MoE coder** — the sweet spot for local agentic coding. 3B active params = runs on consumer hardware, 35B total = deep knowledge

## Key Findings Siphoned

| Finding | Implication for OWL |
|---------|-------------------|
| 2.3M Fable 5 reasoning traces distilled into 4B model | We could do this with our OWN pipelines — distill our factory agents into tiny local models |
| 100% self-consistency @ 512 samples | Production-grade reliability from a 4B model — no more praying the API returns a good answer |
| Student not bounded by teacher | Distillation isn't compression — it's transformation. The student discovers things the teacher misses |
| Open-sourced model weights | We can download and run this TODAY on our MacBook |
| 35B/3B MoE agentic coder | Local coding agent that rivals cloud APIs — 3B active params per forward pass |

## Implementation Plan

### Phase 1: Download & Evaluate (1 hour)
1. Download the distilled Qwen3-4B model from Hugging Face
2. Run on Ollama or llama.cpp on MacBook
3. Evaluate on: coding tasks, factory pipeline decisions, creative writing
4. Compare: latency, output quality, consistency vs current API models

### Phase 2: Factory Pipeline Integration (4 hours)
1. Identify 3 places in the album factory where a local reasoning model could replace an API call
2. Implement as drop-in replacement with fallback to API
3. Measure: cost savings, latency improvement, quality delta
4. Documents: which tasks the distilled model handles, which still need the full teacher

### Phase 3: OWL's Own Distillation Pipeline (8 hours — P2)
1. Collect reasoning traces from OWL's factory pipelines (album decisions, taste evaluations, creative choices)
2. Format as thinking traces (cleartext reasoning chains)
3. Distill into a small local model (Qwen3-1.7B or similar)
4. This creates an OWL-specific model that embodies our taste without needing API access

### Phase 4: Agentic Coder (35B/3B) Evaluation (2 hours)
1. Download the Qwen+Fable 35B/3B MoE coder
2. Test on our Apify actor codebase (can it write actors without the factory context?)
3. If good: integrate with agy CLI as alternative backend for coding tasks

## Acceptance Criteria
- [ ] Distilled Qwen3-4B running locally on MacBook
- [ ] Evaluation report: quality, latency, cost comparison vs current API models
- [ ] At least 1 factory pipeline stage replaced with local model (with API fallback)
- [ ] Documented: token cost savings per week
- [ ] (P2) OWL-specific distillation pipeline designed

## ERRC Analysis (Applied to OWL's Infrastructure)

| ELIMINATE | RAISE |
|-----------|-------|
| API calls for simple reasoning tasks that a local 4B can handle | Local model capability — run production-quality reasoning at zero marginal cost |
| Waiting on API latency for creative decisions | Pipeline throughput — local models return in milliseconds, not seconds |

| REDUCE | CREATE |
|--------|--------|
| Token spend on routine evaluations (taste checks, quality gates) | OWL-specific distilled model — our taste, our pipelines, our brand, running locally |
| Dependency on a single API provider for reasoning | Local model as default, API as fallback — never blocked by API outages |

## Revenue Model
- **Direct:** Zero — this is cost optimization
- **Indirect:** If we replace 50% of API calls with local inference, we save ~$25-50/month in DeepSeek/Claude credits. More importantly: local models run 24/7 with zero rate limits, enabling continuous factory operation.
- **Strategic:** An OWL-specific distilled model is a moat — no one else has our taste in a 4B package that can run on any device.
