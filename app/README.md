# GMP Floor Inspection Co-Pilot
## Meta Ray-Ban Wayfarer Gen 2 + Claude API

### Quick Start (3 steps)

**1. Install dependencies:**
```
pip install anthropic flask pillow
```

**2. Set your API key:**
```
set ANTHROPIC_API_KEY=your_key_here
```

**3. Run the app:**
```
cd "C:\Users\gaura\OneDrive\Desktop\Claude Cowork\Smart Glasses GMP Inspection\app"
python gmp_inspector.py
```

Open **http://localhost:5000** in your browser.

### How to Use

1. **Capture** — Take a photo with your Meta Ray-Ban glasses (tap the temple or say "Hey Meta, take a photo")
2. **Transfer** — Photos sync to your phone via the Meta View app, then to your PC
3. **Analyze** — Drop the photo into the web interface or use CLI:
   ```
   python gmp_inspector.py photo.jpg        # Auto-detect mode
   python gmp_inspector.py photo.jpg qa     # QA Floor Ops mode
   python gmp_inspector.py photo.jpg ehs    # EHS Safety mode
   python gmp_inspector.py photo.jpg gdp    # GDP Documentation mode
   python gmp_inspector.py --batch folder/  # Batch process entire folder
   ```

### Features

- **4 inspection modes**: Auto-Detect, QA Floor Ops, EHS Safety, GDP Check
- **8 inspection domains**: Area status, equipment, documentation, gowning, materials, environment, safety, line clearance
- **Severity classification**: Critical, Major, Minor, Informational, Good Practice
- **Regulatory references**: 21 CFR, EU GMP Annex, ICH, OSHA citations
- **Audit-ready reports**: Saved as .txt and .json in `inspection_reports/`
- **Web UI**: Drag-and-drop interface with real-time analysis
- **CLI mode**: For scripting and batch processing
- **~$0.01-0.02 per inspection** via Claude API

### For the Experiment (Phase 1)

To run the 10-image synthetic test:
```
python gmp_inspector.py --batch ../test_images/ auto
```

Results are saved to `inspection_reports/` with a batch summary JSON.
