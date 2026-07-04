# OWL Intelligence Brief — July 4, 2026

## Source 1: Harness Evolution (HF/Joel Niklaus)

**Tweet:** @akshay_pachaar — "Don't train the model, evolve the harness"
**Paper:** huggingface.co/spaces/joelniklaus/harness-optimization
**Published:** July 1, 2026

### What We Siphoned

1. **Harness > Model on benchmark scores** — 5 different harnesses on the SAME model scored 3.5% to 80.1%. A benchmark score measures model + harness together, and until the harness is fixed, you can't know which failed.

2. **Automated harness evolution works** — A Claude proposer adds one mechanism per iteration. An outer loop keeps it only if it beats the current best. Accepted mechanisms compound. This is our EXACT factory evolution model.

3. **Biggest gain: file handling** — Landing the deliverable exactly where the judge expects it beat every prompt change, with zero extra model tokens. For Apify actors: output schema and file placement matter more than any prompt tweak.

4. **Code fixes transfer; prompt playbooks do NOT** — Same harness lifted a smaller model by 14 points, but tuned prompts hurt a different model family. Harness improvements are model-agnostic; prompt improvements are model-specific.

5. **Cost: 7x cheaper than Sonnet 4.6** — Open model + optimized harness lands between Sonnet 4.6 and Opus 4.6 on LAB metric at 7x lower cost.

### Tickets Created
- P1-12: Automated Harness Evolution Loop

---

## Source 2: Fable 5 Reasoning Distillation (Baseten)

**Tweet:** @waterloo_intern (ali) — "we distilled 2.3M Claude Fable 5 reasoning traces into Qwen3-4B"
**Published:** July 3, 2026

### What We Siphoned

1. **100% self-consistency @ 512 samples** from a 4B model — production-grade reliability at tiny size. Zero hallucination variance.

2. **Student not bounded by teacher** — Distillation is transformation, not compression. The 4B model converged on a "universal truth" the teacher (Fable 5) didn't find.

3. **Open-sourced weights** — Available now. Can run on our MacBook.

4. **Parallel project:** Dhamodharan2006 distilled 4,659 Fable-5 agentic sessions (cleartext thinking traces) into Qwen3-4B for coding/debugging/architecture.

5. **Qwen+Fable 35B/3B MoE agentic coder** — 35B total, 3B active per forward pass. Sweet spot for local agentic coding.

### Tickets Created
- P1-13: Fable 5 Reasoning Distillation — Student Can Surpass Teacher

---

## What We Deliberately DIDN'T Copy

- Neither approach is ready for direct Apify actor revenue — these are infrastructure/cost-optimization plays
- The harness evolution paper uses a Claude proposer; we don't have the budget to run a Claude loop continuously
- The distilled Fable5 model needs local evaluation before we commit to it

## Security Audit
- ✅ Both are public research — no secrets siphoned
- ✅ No code copied — only patterns and architectures
- ✅ No GitHub repos cloned — analysis done via browser + web search only

## Next Action
Phase 1 of both tickets (audit/evaluate) can be done in 2-3 hours. Should be queued for the next hourly guardian cycle when RAM is healthy.
