"""
GMP Floor Inspection Co-Pilot
==============================
Meta Ray-Ban Wayfarer Gen 2 + Claude API Integration

How it works:
1. Capture photo with Meta Ray-Ban glasses (saves to phone gallery via Meta View app)
2. Run this app on your phone/laptop
3. Select the photo or point to the glasses export folder
4. Claude analyzes it against GMP/EHS/GDP inspection criteria
5. Get a structured observation report with severity classifications

Setup:
    pip install anthropic flask pillow
    set ANTHROPIC_API_KEY=your_key
    python gmp_inspector.py

Then open http://localhost:5000 in your browser.
"""

import anthropic
import base64
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = Path(__file__).parent / "inspection_reports"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# GMP INSPECTION SYSTEM PROMPT (3-Skill Suite)
# ============================================================

SYSTEM_PROMPT = """You are a GMP floor inspection co-pilot for pharmaceutical and biotech manufacturing environments. You analyze photos taken during floor walks, facility walkthroughs, EHS audits, and QA inspections. You identify compliance observations, potential deviations, and good practices based on what you see in the image.

You are NOT making disposition decisions. You are surfacing observations for the human inspector to evaluate.

## Auto-Detect Mode
Analyze the image and automatically determine which inspection domains are relevant:

### Domain 1: Area Status and Labeling
- Status tags (CLEAN, IN USE, QUARANTINE, OUT OF SERVICE, MAINTENANCE)
- Status tag matches apparent condition
- Room classification signage, pressure differential indicators
- Access restriction signage, gowning requirement signage

### Domain 2: Equipment and Instrumentation
- Calibration stickers with current dates
- Equipment ID labels visible and legible
- "Do Not Use" / "Out of Service" tags
- Proper storage, clean equipment covered, no visible damage/corrosion

### Domain 3: Good Documentation Practice (GDP)
- Logbook present and current at station
- Entries appear contemporaneous
- Corrections: single-line strikethrough with initials and date
- SOPs accessible at point of use, controlled document stamps

### Domain 4: Gowning and Personnel
- Proper gowning for area classification
- Gowning sequence signage posted
- Clean/soiled garment separation, sticky mats not saturated
- No food, drink, gum, or personal items in controlled areas

### Domain 5: Material Control and Storage
- Materials labeled with lot number, expiry, status
- No expired materials visible
- Quarantine materials physically segregated
- FIFO organization, approved containers only

### Domain 6: Environmental and Housekeeping
- Floors clean, walls/ceilings undamaged
- Waste bins not overflowing, properly labeled
- No standing water, adequate lighting
- Air returns and vents free of contamination

### Domain 7: EHS and Safety
- Emergency eyewash/shower stations accessible
- Fire extinguishers visible with current tags
- SDS accessible, spill kits present
- Exit signs illuminated, paths clear, PPE appropriate

### Domain 8: Line Clearance
- No materials from previous batch visible
- Labels from previous product removed
- Equipment surfaces visually clean
- Current batch documentation displayed

## Output Format

For each photo, generate:

```
INSPECTION OBSERVATION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skill Applied: [QA Floor Operations / EHS Safety / GDP Check / Auto-Detect]
Photo: [description of what you see]
Location: [inferred from image context — or "Not determinable"]
Domains assessed: [which domains are relevant]

FINDINGS:

[1] [SEVERITY: Critical/Major/Minor/Informational/Good Practice]
    Domain: [which domain]
    Observation: [what you observed]
    Regulatory Reference: [21 CFR section, EU GMP Annex, ICH, OSHA]
    Recommended Action: [what the inspector should verify or do]

[2] ...

NOT ASSESSABLE FROM THIS IMAGE:
- [items that cannot be determined from the photo]

INSPECTOR ACTION REQUIRED:
- Review each finding above
- Confirm or dismiss based on direct observation
- Document confirmed findings per site deviation/observation SOP
- This report is a pre-screening aid, not a GxP record
```

## Severity Definitions
- Critical: Direct risk to product quality, patient safety, or personnel safety. Immediate action.
- Major: Significant deviation from GMP/EHS requirements. Investigation required.
- Minor: Deviation from best practice, low immediate risk. Correct at next opportunity.
- Informational: Worth noting but not a deviation.
- Good Practice: Positive observation. Acknowledge what is done well.

## Rules
1. Report only what you can see. If you cannot read a label, say so.
2. No fabrication. If uncertain, say so explicitly.
3. Be specific. Describe residue, discoloration, particulate — not just "potential issue."
4. Reference regulations for each finding.
5. Err on the side of reporting. The inspector makes the final call.
6. Never identify the specific company, site, or product.
7. Photos are not GxP records. This is a pre-screening aid."""


# ============================================================
# CORE INSPECTION FUNCTION
# ============================================================

def inspect_image(image_path: str, skill: str = "auto") -> dict:
    """
    Send an image to Claude API for GMP inspection analysis.
    
    Args:
        image_path: Path to the image file (JPEG/PNG)
        skill: "auto", "qa", "ehs", or "gdp"
    
    Returns:
        dict with report text, metadata, and findings
    """
    if not API_KEY:
        return {"error": "ANTHROPIC_API_KEY not set. Run: set ANTHROPIC_API_KEY=your_key"}
    
    client = anthropic.Anthropic(api_key=API_KEY)
    
    # Read and encode image
    image_path = Path(image_path)
    if not image_path.exists():
        return {"error": f"Image not found: {image_path}"}
    
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    # Determine media type
    suffix = image_path.suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    media_type = media_types.get(suffix, "image/jpeg")
    
    # Build skill-specific prompt
    skill_prompts = {
        "auto": "Analyze this photo from a pharmaceutical environment. Auto-detect which inspection domains are relevant and provide a complete observation report.",
        "qa": "Analyze this photo as a QA Floor Operations inspection. Focus on area status, equipment, material control, document control, and line clearance.",
        "ehs": "Analyze this photo for EHS and Safety compliance. Focus on emergency equipment, exits, chemical safety, PPE, and physical hazards.",
        "gdp": "Analyze this photo for Good Documentation Practice (GDP) compliance. Focus on ALCOA+ principles, correction practices, ink standards, and logbook specifics.",
    }
    
    user_prompt = skill_prompts.get(skill, skill_prompts["auto"])
    
    # Call Claude API with vision
    print(f"  Sending image to Claude API ({MODEL})...")
    start_time = datetime.now()
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }]
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    report_text = response.content[0].text
    
    # Build result
    result = {
        "image": str(image_path),
        "skill": skill,
        "model": MODEL,
        "timestamp": datetime.now().isoformat(),
        "response_time_seconds": round(elapsed, 1),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "report": report_text,
    }
    
    # Save report
    report_name = f"report_{image_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save as text
    txt_path = OUTPUT_DIR / f"{report_name}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"GMP INSPECTION REPORT\n")
        f.write(f"Generated: {result['timestamp']}\n")
        f.write(f"Image: {image_path.name}\n")
        f.write(f"Skill: {skill}\n")
        f.write(f"Model: {MODEL}\n")
        f.write(f"Response time: {elapsed:.1f}s\n")
        f.write(f"Tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out\n")
        f.write(f"{'='*60}\n\n")
        f.write(report_text)
    
    # Save as JSON
    json_path = OUTPUT_DIR / f"{report_name}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"  Analysis complete in {elapsed:.1f}s")
    print(f"  Report saved: {txt_path}")
    
    return result


# ============================================================
# BATCH PROCESSING (for experiment)
# ============================================================

def batch_inspect(image_folder: str, skill: str = "auto"):
    """Process all images in a folder."""
    folder = Path(image_folder)
    images = sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.jpeg")) + sorted(folder.glob("*.png"))
    
    if not images:
        print(f"No images found in {folder}")
        return
    
    print(f"\nBatch inspection: {len(images)} images")
    print(f"Skill: {skill}")
    print(f"Output: {OUTPUT_DIR}\n")
    
    results = []
    for i, img in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] {img.name}")
        result = inspect_image(str(img), skill)
        results.append(result)
        print(f"  Tokens used: {result.get('input_tokens', 0)} + {result.get('output_tokens', 0)}")
    
    # Save batch summary
    summary_path = OUTPUT_DIR / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w") as f:
        json.dump({
            "batch_size": len(images),
            "skill": skill,
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in results),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in results),
            "results": results,
        }, f, indent=2)
    
    print(f"\nBatch complete. Summary: {summary_path}")


# ============================================================
# WEB UI (Flask)
# ============================================================

def run_web_ui():
    """Run a simple web interface for the inspector."""
    try:
        from flask import Flask, request, render_template_string, jsonify, send_from_directory
    except ImportError:
        print("Flask not installed. Run: pip install flask")
        print("Falling back to CLI mode.\n")
        return False
    
    app = Flask(__name__)
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GMP Floor Inspection Co-Pilot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
               background: #0a0a0a; color: #e0e0e0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a237e, #0d47a1); padding: 20px; text-align: center; }
        .header h1 { font-size: 1.4em; color: white; }
        .header p { color: #90caf9; font-size: 0.85em; margin-top: 5px; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-zone { border: 2px dashed #444; border-radius: 12px; padding: 40px; text-align: center;
                       margin: 20px 0; cursor: pointer; transition: all 0.3s; }
        .upload-zone:hover { border-color: #2196f3; background: #111; }
        .upload-zone.dragover { border-color: #4caf50; background: #1a1a1a; }
        .upload-zone input { display: none; }
        .upload-zone label { cursor: pointer; }
        .upload-zone .icon { font-size: 3em; margin-bottom: 10px; }
        .skill-select { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
        .skill-btn { padding: 10px 20px; border: 1px solid #333; border-radius: 8px; background: #1a1a1a;
                     color: #e0e0e0; cursor: pointer; transition: all 0.2s; flex: 1; min-width: 120px; text-align: center; }
        .skill-btn:hover { border-color: #2196f3; }
        .skill-btn.active { background: #1a237e; border-color: #2196f3; color: white; }
        .analyze-btn { width: 100%; padding: 15px; background: #2196f3; color: white; border: none; 
                       border-radius: 8px; font-size: 1.1em; cursor: pointer; margin: 20px 0; }
        .analyze-btn:hover { background: #1976d2; }
        .analyze-btn:disabled { background: #333; cursor: not-allowed; }
        .preview { max-width: 100%; border-radius: 8px; margin: 15px 0; }
        .report { background: #111; border: 1px solid #333; border-radius: 8px; padding: 20px; 
                  margin: 20px 0; white-space: pre-wrap; font-family: 'Consolas', monospace; 
                  font-size: 0.9em; line-height: 1.6; }
        .report .critical { color: #f44336; font-weight: bold; }
        .report .major { color: #ff9800; font-weight: bold; }
        .report .minor { color: #ffc107; }
        .report .good { color: #4caf50; }
        .loading { text-align: center; padding: 40px; }
        .loading .spinner { border: 4px solid #333; border-top: 4px solid #2196f3; 
                           border-radius: 50%; width: 40px; height: 40px; margin: 0 auto 15px;
                           animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .meta { color: #888; font-size: 0.8em; margin-top: 10px; }
        .stats { display: flex; gap: 15px; margin: 15px 0; }
        .stat { background: #1a1a1a; border-radius: 8px; padding: 10px 15px; flex: 1; text-align: center; }
        .stat .value { font-size: 1.3em; color: #2196f3; font-weight: bold; }
        .stat .label { font-size: 0.75em; color: #888; }
    </style>
</head>
<body>
    <div class="header">
        <h1>GMP Floor Inspection Co-Pilot</h1>
        <p>Meta Ray-Ban + Claude AI | Real-time GMP Compliance Analysis</p>
    </div>
    <div class="container">
        <div class="skill-select">
            <div class="skill-btn active" data-skill="auto" onclick="selectSkill(this)">Auto-Detect</div>
            <div class="skill-btn" data-skill="qa" onclick="selectSkill(this)">QA Floor Ops</div>
            <div class="skill-btn" data-skill="ehs" onclick="selectSkill(this)">EHS Safety</div>
            <div class="skill-btn" data-skill="gdp" onclick="selectSkill(this)">GDP Check</div>
        </div>
        
        <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
            <div class="icon">📸</div>
            <p>Drop a photo from your Meta Ray-Ban here<br>or click to browse</p>
            <input type="file" id="fileInput" accept="image/*" onchange="handleFile(this.files[0])">
        </div>
        
        <img id="preview" class="preview" style="display:none">
        
        <button class="analyze-btn" id="analyzeBtn" onclick="analyze()" disabled>
            Analyze for GMP Compliance
        </button>
        
        <div id="loading" style="display:none" class="loading">
            <div class="spinner"></div>
            <p>Claude is analyzing the image across 8 inspection domains...</p>
        </div>
        
        <div id="stats" style="display:none" class="stats">
            <div class="stat"><div class="value" id="statTime">-</div><div class="label">Response Time</div></div>
            <div class="stat"><div class="value" id="statFindings">-</div><div class="label">Findings</div></div>
            <div class="stat"><div class="value" id="statTokens">-</div><div class="label">Tokens Used</div></div>
        </div>
        
        <div id="report" class="report" style="display:none"></div>
    </div>
    
    <script>
        let selectedSkill = 'auto';
        let selectedFile = null;
        
        function selectSkill(el) {
            document.querySelectorAll('.skill-btn').forEach(b => b.classList.remove('active'));
            el.classList.add('active');
            selectedSkill = el.dataset.skill;
        }
        
        function handleFile(file) {
            if (!file) return;
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = e => {
                document.getElementById('preview').src = e.target.result;
                document.getElementById('preview').style.display = 'block';
                document.getElementById('analyzeBtn').disabled = false;
            };
            reader.readAsDataURL(file);
        }
        
        // Drag and drop
        const dz = document.getElementById('dropZone');
        dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
        dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
        dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('dragover'); handleFile(e.dataTransfer.files[0]); });
        
        async function analyze() {
            if (!selectedFile) return;
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('report').style.display = 'none';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = true;
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            formData.append('skill', selectedSkill);
            
            try {
                const resp = await fetch('/analyze', { method: 'POST', body: formData });
                const data = await resp.json();
                
                if (data.error) {
                    document.getElementById('report').textContent = 'Error: ' + data.error;
                } else {
                    let html = data.report
                        .replace(/Critical/g, '<span class="critical">Critical</span>')
                        .replace(/Major/g, '<span class="major">Major</span>')
                        .replace(/Minor/g, '<span class="minor">Minor</span>')
                        .replace(/Good Practice/g, '<span class="good">Good Practice</span>');
                    document.getElementById('report').innerHTML = html;
                    
                    document.getElementById('statTime').textContent = data.response_time_seconds + 's';
                    document.getElementById('statFindings').textContent = (data.report.match(/\\[\\d+\\]/g) || []).length;
                    document.getElementById('statTokens').textContent = (data.input_tokens + data.output_tokens).toLocaleString();
                    document.getElementById('stats').style.display = 'flex';
                }
                
                document.getElementById('report').style.display = 'block';
            } catch (e) {
                document.getElementById('report').textContent = 'Connection error: ' + e.message;
                document.getElementById('report').style.display = 'block';
            }
            
            document.getElementById('loading').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = false;
        }
    </script>
</body>
</html>
    """
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"})
        
        file = request.files['image']
        skill = request.form.get('skill', 'auto')
        
        # Save uploaded file temporarily
        temp_path = OUTPUT_DIR / f"temp_{file.filename}"
        file.save(str(temp_path))
        
        try:
            result = inspect_image(str(temp_path), skill)
            return jsonify(result)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    @app.route('/reports')
    def list_reports():
        reports = sorted(OUTPUT_DIR.glob("*.json"), reverse=True)
        return jsonify([{"name": r.name, "size": r.stat().st_size} for r in reports[:20]])
    
    print("\n" + "=" * 60)
    print("  GMP Floor Inspection Co-Pilot")
    print("  Meta Ray-Ban + Claude AI")
    print("=" * 60)
    print(f"\n  Open in browser: http://localhost:5000")
    print(f"  Reports saved to: {OUTPUT_DIR}")
    print(f"\n  Press Ctrl+C to stop.\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
    return True


# ============================================================
# CLI MODE
# ============================================================

def cli_mode():
    """Simple CLI for single image inspection."""
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python gmp_inspector.py                    # Start web UI")
        print("  python gmp_inspector.py image.jpg          # Inspect single image")
        print("  python gmp_inspector.py image.jpg qa       # Inspect with QA skill")
        print("  python gmp_inspector.py --batch folder/    # Batch process folder")
        print("\nSkills: auto, qa, ehs, gdp")
        return
    
    if sys.argv[1] == "--batch":
        folder = sys.argv[2] if len(sys.argv) > 2 else "."
        skill = sys.argv[3] if len(sys.argv) > 3 else "auto"
        batch_inspect(folder, skill)
    else:
        image = sys.argv[1]
        skill = sys.argv[2] if len(sys.argv) > 2 else "auto"
        result = inspect_image(image, skill)
        if "error" in result:
            print(f"\nError: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(result["report"])
            print(f"\n{'='*60}")
            print(f"Response time: {result['response_time_seconds']}s")
            print(f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_mode()
    else:
        if not run_web_ui():
            cli_mode()
