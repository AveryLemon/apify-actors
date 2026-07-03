# P1-9: Build Background Removal + Enhancement Actor

## Goal
Build an Apify actor that removes backgrounds from images and optionally enhances the result (composite, shadow, lighting).

## Why
Surprising gap — remove.bg proves massive demand ($500M+ market). No dedicated background removal actor on Apify. E-commerce, real estate, profile photos. $0.10-0.25/run.

## Approach
- Input: image URL
- Process: background removal (RMBG-1.4 or rembg), optional shadow/reflection composite, optional background replacement
- Output: processed image with transparent/composite background
- Batch mode: process gallery of up to 20 images

## Verification
- [ ] Actor builds on push
- [ ] Background removal is clean on hair/fur edges
- [ ] Composite mode adds realistic shadow
- [ ] Batch processing works with 10+ images

## File location
`~/Desktop/Apify-Actors/templates/bg-remover/`
