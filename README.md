# AI-Augmented GMP Floor Inspection with Smart Glasses

**Real-time pharmaceutical compliance inspection using Meta Ray-Ban Wayfarer Gen 2 and Claude AI Vision**

## Overview

This project implements an AI-powered GMP (Good Manufacturing Practice) floor inspection co-pilot that works with commodity camera-enabled smart glasses. An inspector wearing Meta Ray-Ban glasses captures photos during facility walkthroughs, and Claude AI analyzes each image against 8 pharmaceutical compliance domains, generating structured observation reports with severity classifications and regulatory references.

**This is the first published feasibility study of AI vision for observational GMP floor inspection using commodity hardware ($0-300) rather than enterprise platforms ($1,500+).**

## How It Works

```
Meta Ray-Ban Glasses (camera capture)
        ↓
Phone (Meta View app - photo sync)
        ↓
GMP Inspector App (web or mobile)
        ↓
Claude API (multimodal vision analysis)
        ↓
Structured Inspection Report
  • Severity: Critical/Major/Minor/Good Practice
  • Regulatory references (21 CFR, EU GMP, ICH)
  • Recommended inspector actions
```

## 3-Skill Inspection Suite

| Skill | Coverage |
|-------|----------|
| **QA Floor Operations** | Area status tags, equipment calibration, material control, line clearance, gowning, environmental monitoring, in-process controls, labeling |
| **EHS Safety** | Emergency equipment, exits, chemical storage, PPE, ergonomics, LOTO, confined space |
| **GDP Documentation** | ALCOA+ assessment, correction practices, ink standards, logbook specifics, batch record review |

## Quick Start

### Web App (works immediately)
```bash
pip install anthropic flask
export ANTHROPIC_API_KEY=your_key
cd app
python gmp_inspector.py
# Open http://localhost:5000
```

### Mobile Web App (iPhone/Android)
Open `http://your-pc-ip:5000/mobile.html` on your phone's browser.

### CLI Mode
```bash
python app/gmp_inspector.py photo.jpg          # Auto-detect mode
python app/gmp_inspector.py photo.jpg qa       # QA Floor Ops
python app/gmp_inspector.py photo.jpg ehs      # EHS Safety
python app/gmp_inspector.py photo.jpg gdp      # GDP Check
python app/gmp_inspector.py --batch folder/    # Batch process
```

## Project Structure

```
├── app/
│   ├── gmp_inspector.py        # Main application (Flask web + CLI)
│   ├── mobile.html             # Progressive Web App for mobile
│   └── README.md               # App setup guide
├── skills/
│   ├── SKILL_gmp_floor_inspector.md   # Core 8-domain inspection skill
│   └── SKILL_SUITE_complete.md        # Full 3-skill suite (QA + EHS + GDP)
├── test_scenarios/
│   └── gmp_test_scenarios.html        # 8 interactive HTML test scenarios
├── test_results/
│   └── *.json / *.txt                 # Inspection reports from live testing
├── flutter_app/
│   ├── lib/main.dart                  # Flutter/Dart mobile app (iOS/Android)
│   ├── pubspec.yaml                   # Flutter dependencies
│   └── SETUP_GUIDE.md                # Mobile app build guide
└── docs/
    └── EXPERIMENT_DESIGN.md           # Feasibility experiment protocol
```

## Experiment Design

### Phase 1: Synthetic Image Test
8 HTML-rendered GMP scenarios with 15+ planted compliance findings. Score AI detection rate against ground truth.

### Phase 2: Real Environment Test (in progress)
Meta Ray-Ban Wayfarer Gen 2 photos in non-proprietary environments. 4 test inspections completed.

### Phase 3: Smart Glasses Integration (completed)
Full integration with Meta Ray-Ban Wayfarer Gen 2 via Meta View app photo sync.

## Cost

- **Hardware**: Meta Ray-Ban Wayfarer Gen 2 (~$299)
- **API cost**: ~$0.01-0.02 per inspection
- **100 inspections**: ~$1-2
- **No subscription fees**

## Regulatory Positioning

This is a **decision-support tool**. The AI surfaces observations; the qualified inspector makes the judgment. Aligns with:
- FDA CSA (2025): Risk-based assurance, critical thinking
- ISPE GAMP AI Guide (2025): HITL mandatory for GxP-impacting outputs
- EU GMP Annex 22 (draft): Human oversight of AI in regulated environments
- ICH Q9(R1): Risk-proportionate application of technology

## Author

**Gourav Pandey**



## License

MIT License — Open source for the pharmaceutical community.
