with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    content = f.read()

# Fix the corrupted lines 17-21 by replacing the entire block
old_table_block = """| Pending blocks | **Pricing not set** (needs Apify Console UI) | Blocking revenue |
||| RAM on MacBook | 89% free | 🟢 Healthy baseline — no heavy processes |
||| Disk | 104Gi available | ✅ Healthy |
|| Swap | 1729.56Mi/3072Mi used (56.3%) -- encrypted | Consecutive cycles | **72** (blue ocean uncontested — RAM 🟢 44%, no tickets remain) | RAM at 89% — healthy baseline, no active blockers |

|| Competitive watch | solutionssmart/brand-dna (SingleSurge — website brand DNA, deterministic, NOT creative analysis), syntellect_ai (transcription+entity), calm_necessity/HumbleIgnite/BoldBastion (MultipleWords API-wrap music gen -- fragile), VastHornet (API-key TTS), stanvanrooy6 (OpenAI TTS), lupara90/prompt-builder (prompt gen, not analysis), whoareyouanas/creative-intelligence (ad creative LLM analysis, API-wrapper), umischael/ai-data-enricher (dataset enrichment -- not creative analysis). **All LOW threat -- none in OWL's creative analysis niche.** | Blue ocean uncontested -- 72nd cycle (siphon: primary query timed out, retry succeeded -- no competitors found) """

new_table_block = """| Pending blocks | **Pricing not set** (needs Apify Console UI) | Blocking revenue |
|| RAM on MacBook | 89% free | 🟢 Healthy baseline -- no heavy processes |
|| Disk | 104Gi available | ✅ Healthy |
|| Swap | 1729.56Mi/3072Mi used (56.3%) -- encrypted 🟡 | 🟡 Improved from 92.5% -- swap does NOT drain automatically (requires restart or pressure) |
|| Consecutive cycles | **72** (blue ocean uncontested -- RAM 🟢 89%, no tickets remain) | RAM at 89% -- healthy baseline, no active blockers |

|| Competitive watch | solutionssmart/brand-dna (SingleSurge -- website brand DNA, deterministic, NOT creative analysis), syntellect_ai (transcription+entity), calm_necessity/HumbleIgnite/BoldBastion (MultipleWords API-wrap music gen -- fragile), VastHornet (API-key TTS), stanvanrooy6 (OpenAI TTS), lupara90/prompt-builder (prompt gen, not analysis), whoareyouanas/creative-intelligence (ad creative LLM analysis, API-wrapper), umischael/ai-data-enricher (dataset enrichment -- not creative analysis). **All LOW threat -- none in OWL's creative analysis niche.** | Blue ocean uncontested -- 72nd cycle (siphon: no new competitors found) """

if old_table_block in content:
    content = content.replace(old_table_block, new_table_block)
    print('Replaced successfully')
else:
    print('Could not find exact match. Searching...')
    # Try to find the problematic area
    idx = content.find('Pending blocks')
    if idx >= 0:
        print(f'Found at position {idx}')
        print('Context:', repr(content[idx:idx+500])[:500])

with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md', 'w') as f:
    f.write(content)

# Verify
with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    for i, line in enumerate(f.readlines()):
        if any(x in line for x in ['RAM on MacBook', 'Disk |', 'Swap |', 'Consecutive cycles', 'Competitive watch']):
            print(f'L{i+1}: {line.rstrip()}')
