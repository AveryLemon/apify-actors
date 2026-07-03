# P0-5: Build Aesthetic / Style Analysis Actor

## Goal
Build an Apify actor that analyzes images for aesthetic quality, composition rules, visual style classification, and brand consistency scoring.

## Why
No competitor on Apify does aesthetic analysis. akash9078 analyzes objects/colors/emotions but NOT beauty, composition, or style. OWL's visual creation methodology is directly applicable. $0.35-0.50/run.

## Approach
- Input: image URL
- Output: aesthetic score (0-10), composition analysis (rule of thirds, symmetry, leading lines), style classification (minimalist, grunge, vintage, clean, dark, nature, etc.), color harmony score, lighting quality, top 3 improvements

## Verification
- [ ] Actor builds on push
- [ ] Returns meaningful aesthetic score for a test image
- [ ] Style classification matches human judgment
- [ ] Color harmony analysis is accurate

## File location
`~/Desktop/Apify-Actors/templates/aesthetic-style-analyzer/`
