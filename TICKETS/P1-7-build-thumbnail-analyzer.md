# P1-7: Build Thumbnail CTR Analysis + Generator

## Goal
Build an Apify actor that analyzes YouTube thumbnails for click-through-rate likelihood and generates optimized alternatives.

## Why
Massive YouTube creator demand. No Apify competitor. Creators pay for TubeBuddy/Canva alternatives. $0.35-0.75/run.

## Approach
- Input: YouTube video URL or thumbnail image URL
- Analysis: CTR score based on composition, contrast, text readability, face presence, color psychology
- Generation: produce 3 optimized thumbnail variants with text overlay
- Uses open-source image gen models + composition heuristics

## Verification
- [ ] Actor builds on push
- [ ] Analysis scores are meaningful and actionable
- [ ] Generated thumbnails are visually compelling
- [ ] Text overlay is readable at small sizes

## File location
`~/Desktop/Apify-Actors/templates/thumbnail-analyzer/`
