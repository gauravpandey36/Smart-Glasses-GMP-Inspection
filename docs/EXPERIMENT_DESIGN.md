# AI-Augmented GMP Floor Inspection: Feasibility Experiment

## Research Gap

As of May 2026, no published study has evaluated AI vision systems for observational GMP floor walks, QA inspections, or facility walkthroughs in pharmaceutical environments. Fixed-camera AI inspection of products (vials, tablets, line clearance) is commercially deployed. But the specific use case — a human inspector wearing camera-enabled glasses or using a phone camera while the AI provides real-time compliance observations — has no published evidence.

This experiment fills that gap.

## Hypothesis

An AI vision system, given a structured GMP inspection skill and a photo from a pharmaceutical environment, can identify compliance-relevant observations across 8 inspection domains with sufficient accuracy to serve as a useful pre-screening co-pilot for qualified human inspectors.

## Experiment Design

### Phase 1: Synthetic Image Test (what we build now — $0)

Create 10 synthetic pharmaceutical environment images using AI image generation or stock photos. Each image has deliberately planted compliance issues and good practices.

**Test Image Set:**

| # | Scene | Planted Findings | Expected Severity |
|---|---|---|---|
| 1 | Clean equipment staging area | Missing status tag on one vessel, correct tags on others | Major + Good Practice |
| 2 | Gowning area entry | Proper signage, but sticky mat is saturated, garments disorganized | Minor x2 |
| 3 | Open logbook at workstation | Visible correction without initials, entries appear current | Major + Good Practice |
| 4 | Chemical storage shelf | One expired container visible, others properly labeled, SDS binder present | Critical + Good Practice |
| 5 | Production line (idle) | Previous batch label still attached to hopper, otherwise clean | Major (line clearance) |
| 6 | Corridor outside cleanroom | Emergency eyewash blocked by cart, exit sign illuminated | Critical + Good Practice |
| 7 | Equipment with calibration stickers | One sticker shows expired date, two are current, one missing | Major + Minor |
| 8 | Material staging area | Quarantine material mixed with released material, no segregation | Critical |
| 9 | Cleanroom interior (in operation) | Operator properly gowned, but uncovered coffee cup on bench | Critical (food in controlled area) |
| 10 | Maintenance workshop | Tools organized, but no "Out of Service" tag on disassembled pump | Major |

**Scoring rubric:**
- True Positive: AI correctly identifies a planted finding
- False Negative: AI misses a planted finding
- False Positive: AI identifies a finding that was not planted (may still be valid)
- Severity Accuracy: AI assigns correct severity level

**Success criteria:**
- Detection rate ≥ 70% of planted findings (10 images, ~20 planted findings total)
- Critical findings detection rate ≥ 90%
- False positive rate: document but do not penalize (the AI should err on the side of reporting)

### Phase 2: Real Environment Test (next step — phone camera, $0)

Take 10 real photos in a non-proprietary environment (training lab, Yogesh's facility, generic lab setup):
- Re-run the same skill
- Compare AI observations with manual expert observations
- Document concordance rate

### Phase 3: Smart Glasses Integration (future — $100-200 hardware)

Options within budget:
- **$30-60:** Amazon camera glasses (1080p, records video, exports to phone)
- **$50-100:** Raspberry Pi + camera module in a 3D-printed glasses frame (DIY maker approach)
- **$99:** Insta360 GO 3S (tiny clip-on camera, good image quality)
- **$0:** Phone on lanyard (simplest viable option)

The integration is simple: glasses capture image → transfer to phone → phone sends to Claude API → structured observation returned → displayed on phone screen or read via text-to-speech.

### Phase 4: Publication

Write up results as: "AI-Augmented Observational Inspection for GMP Floor Walks: A Feasibility Study Using Multimodal Vision Models and Commodity Camera Hardware"

Target: ISPE Pharmaceutical Engineering or PDA JPST

## Hardware Comparison for Budget Deployment

| Option | Cost | Image Quality | Hands-Free | GMP Compatible | Best For |
|---|---|---|---|---|---|
| Phone on lanyard | $0 | Excellent | No | Yes | Fastest PoC |
| Amazon camera glasses | $30-60 | Good (1080p) | Yes | TBD (material) | Budget wearable PoC |
| Insta360 GO 3S | $99 | Very good (4K) | Yes (clip-on) | Possibly | Best image quality per $ |
| Raspberry Pi + cam | $50-100 | Good | Yes (DIY mount) | No (not cleanroom) | Maker/research credibility |
| Vuzix M400 | $1,500+ | Excellent | Yes | Yes (ISO Class 2) | Production deployment |

## API Cost Estimate

Claude API (claude-sonnet) with vision:
- Input: ~1,500 tokens per image + ~500 tokens skill prompt = ~2,000 tokens
- Output: ~500 tokens per observation report
- Cost per image: ~$0.01-0.02
- 100 test images: ~$1-2
- 1,000 test images: ~$10-20

Well within $200 budget. Even at scale, this is negligible.

## File Structure

```
Smart Glasses GMP Inspection/
├── SKILL_gmp_floor_inspector.md          ← The Claude inspection skill
├── EXPERIMENT_DESIGN.md                  ← This document
├── test_images/                          ← Synthetic test images (Phase 1)
│   ├── 01_equipment_staging.png
│   ├── 02_gowning_area.png
│   ├── ...
│   └── ground_truth.json                 ← What each image should find
├── results/                              ← AI observation reports per image
│   ├── 01_observation_report.md
│   ├── ...
│   └── summary_metrics.json
├── api_inspector.py                      ← Script to batch-process images via Claude API
└── README.md                             ← GitHub repo readme
```

## Regulatory Positioning

This is a decision-support tool. The AI surfaces observations; the qualified inspector makes the judgment. Aligns with:
- FDA CSA (2025): risk-based assurance, critical thinking
- ISPE GAMP AI Guide (2025): HITL mandatory for GxP-impacting outputs
- EU GMP Annex 22 (draft): human oversight of AI in regulated environments
- ICH Q9(R1): risk-proportionate application of technology

## What Makes This Novel

1. First published feasibility study of AI vision for observational GMP floor inspection
2. Uses commodity hardware ($0-100) rather than enterprise platforms ($1,500+)
3. Structured 8-domain inspection taxonomy mapped to regulatory references
4. Open-source skill and experiment — reproducible by any organization
5. Bridges the gap between fixed-camera product inspection (mature) and wearable observational inspection (unexplored)
