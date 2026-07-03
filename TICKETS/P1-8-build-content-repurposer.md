# P1-8: Build Content Repurposing Pipeline Actor

## Goal
Build an Apify actor that takes a long video or blog post URL and automatically generates: short clips, social media posts, audiograms, and quote cards.

## Why
#1 creator economy need. Zero Apify actors. Every YouTuber/podcaster repurposes content manually. $1.00-2.00/run.

## Approach
- Input: YouTube/video URL or blog post URL
- Process: fetch transcript/title, identify key moments, generate short clips, extract quotes, create social posts
- Output: downloadable clips, social post text, quote images, audiogram
- Uses: Whisper for transcription, open-source models for clip identification

## Verification
- [ ] Actor builds on push
- [ ] Produces at least 3 useful short clips from a 10-min video
- [ ] Quote cards are visually appealing
- [ ] Social posts are platform-specific (Twitter, Instagram, LinkedIn)

## File location
`~/Desktop/Apify-Actors/templates/content-repurposer/`
