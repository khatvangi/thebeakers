#!/usr/bin/env python3
"""
batch_salvador.py - generate p5.js visualizations for education papers

uses Qwen + Gemma counsel to generate p5.js 2.x code
follows Salvador skill guidelines:
- progressive stages with stepper
- continuous motion
- data cards with domain notation
- color-coded element tracking

usage:
    python scripts/batch_salvador.py --input data/education_papers/education_papers_20260117.json
    python scripts/batch_salvador.py --input data/education_papers/education_papers_20260117.json --limit 5
"""

import argparse
import json
import os
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# paths
BASE_DIR = Path(__file__).parent.parent
SALVADOR_DIR = BASE_DIR / "salvador"
OUTPUT_DIR = BASE_DIR / "visualizations"

# ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_QWEN = "qwen3:latest"
MODEL_GEMMA = "gemma2:9b"

# p5.js 2.x template
P5_TEMPLATE = '''// {title}
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = {num_stages};
let stageLabels = {stage_labels};
let transitioning = false;
let transitionProgress = 0;

// colors
const colors = {{
  bg: "#0f172a",
  card: "#1e293b",
  accent: "#10b981",
  text: "#e2e8f0",
  secondary: "#94a3b8",
}};

function setup() {{
  createCanvas(850, 540);
  textFont("system-ui");
}}

function draw() {{
  background(colors.bg);

  // header
  drawHeader();

  // stage indicator
  drawStageIndicator();

  // main visualization area
  push();
  translate(width / 2, height / 2 - 30);
  {draw_stages}
  pop();

  // data card
  drawDataCard();

  // controls hint
  drawControls();

  // handle transitions
  if (transitioning) {{
    transitionProgress += 0.05;
    if (transitionProgress >= 1) {{
      transitioning = false;
      transitionProgress = 0;
    }}
  }}
}}

function drawHeader() {{
  fill(colors.text);
  textSize(20);
  textAlign(CENTER, TOP);
  text("{title_short}", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("{subtitle}", width / 2, 48);
}}

function drawStageIndicator() {{
  let y = 75;
  let dotSize = 12;
  let spacing = 30;
  let startX = width / 2 - ((totalStages - 1) * spacing) / 2;

  for (let i = 0; i < totalStages; i++) {{
    let x = startX + i * spacing;
    if (i === currentStage) {{
      fill(colors.accent);
      ellipse(x, y, dotSize + 4);
    }} else if (i < currentStage) {{
      fill(colors.accent);
      ellipse(x, y, dotSize);
    }} else {{
      noFill();
      stroke(colors.secondary);
      strokeWeight(2);
      ellipse(x, y, dotSize);
      noStroke();
    }}
  }}

  fill(colors.text);
  textSize(14);
  textAlign(CENTER, TOP);
  text(stageLabels[currentStage], width / 2, y + 15);
}}

function drawDataCard() {{
  let cardX = 20;
  let cardY = height - 120;
  let cardW = 250;
  let cardH = 100;

  fill(colors.card);
  rect(cardX, cardY, cardW, cardH, 8);

  fill(colors.accent);
  textSize(12);
  textAlign(LEFT, TOP);
  text("📊 Key Concept", cardX + 15, cardY + 12);

  fill(colors.text);
  textSize(11);
  let conceptText = getConceptForStage(currentStage);
  text(conceptText, cardX + 15, cardY + 35, cardW - 30, cardH - 50);
}}

function getConceptForStage(stage) {{
  const concepts = {concepts};
  return concepts[stage] || "";
}}

function drawControls() {{
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}}

{stage_functions}

function keyPressed() {{
  if (keyCode === RIGHT_ARROW && currentStage < totalStages - 1) {{
    currentStage++;
    transitioning = true;
    transitionProgress = 0;
  }} else if (keyCode === LEFT_ARROW && currentStage > 0) {{
    currentStage--;
    transitioning = true;
    transitionProgress = 0;
  }} else if (key === "r" || key === "R") {{
    currentStage = 0;
  }} else if (key === "g" || key === "G") {{
    saveGif("visualization.gif", 5);
  }}
}}

// micro-movement for continuous animation
function microMove(baseX, baseY, amplitude = 2) {{
  return {{
    x: baseX + sin(frameCount * 0.02) * amplitude,
    y: baseY + cos(frameCount * 0.03) * amplitude
  }};
}}
'''


def query_ollama(model: str, prompt: str, timeout: int = 180) -> str:
    """query ollama model"""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 4000}
            },
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"  Ollama error ({model}): {e}")
        return ""


def generate_p5_code(paper: Dict) -> Optional[str]:
    """generate p5.js visualization code using counsel approach"""

    title = paper.get("paper_title", "")[:60]
    concept = paper.get("concept_summary", "")
    discipline = paper.get("discipline", "")
    edu_type = paper.get("education_type", "")

    prompt = f"""You are generating p5.js 2.x code for an educational visualization.

CONCEPT TO VISUALIZE:
Title: {title}
Discipline: {discipline}
Education type: {edu_type}
Summary: {concept}

REQUIREMENTS:
1. Create 4-6 stages that progressively reveal the concept
2. Each stage should have continuous micro-movement (nothing static)
3. Use these colors: bg="#0f172a", accent="#10b981", text="#e2e8f0"
4. Canvas size: 850x540
5. Include visual elements appropriate for {discipline}

IMPORTANT p5.js 2.x CHANGES:
- NO preload() function - use async setup() if loading assets
- Use splineVertex() instead of curveVertex()
- Use bezierOrder(2) for quadratic beziers

Return a JSON object with these fields:
{{
    "num_stages": 5,
    "stage_labels": ["Stage 1 Title", "Stage 2 Title", ...],
    "concepts": ["Concept text for stage 1", "Concept text for stage 2", ...],
    "draw_stages": "// p5.js draw code that switches on currentStage\\nif (currentStage === 0) {{ drawStage0(); }} else if ...",
    "stage_functions": "function drawStage0() {{ ... }}\\nfunction drawStage1() {{ ... }}"
}}

The draw_stages should be p5.js code that:
- Uses currentStage variable to show appropriate stage
- Calls stage-specific draw functions
- Adds micro-movement using sin/cos with frameCount

The stage_functions should define drawStage0(), drawStage1(), etc. with actual p5.js drawing code.

Return ONLY valid JSON, no markdown."""

    print(f"    Querying {MODEL_QWEN}...")
    qwen_response = query_ollama(MODEL_QWEN, prompt)

    print(f"    Querying {MODEL_GEMMA}...")
    gemma_response = query_ollama(MODEL_GEMMA, prompt)

    # parse responses
    def extract_json(text: str) -> Optional[Dict]:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return json.loads(text)
        except:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        return None

    qwen_data = extract_json(qwen_response)
    gemma_data = extract_json(gemma_response)

    # counsel merge
    data = qwen_data or gemma_data
    if not data:
        return None

    # build final p5.js code
    code = P5_TEMPLATE.format(
        title=title,
        title_short=title[:40],
        subtitle=f"{discipline.title()} | {edu_type.replace('_', ' ').title()}",
        num_stages=data.get("num_stages", 5),
        stage_labels=json.dumps(data.get("stage_labels", ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5"])),
        concepts=json.dumps(data.get("concepts", ["", "", "", "", ""])),
        draw_stages=data.get("draw_stages", "// placeholder\ndrawStage0();"),
        stage_functions=data.get("stage_functions", "function drawStage0() { fill(colors.accent); ellipse(0, 0, 100); }")
    )

    return code


def slugify(text: str) -> str:
    """convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:40].strip('-')


def main():
    parser = argparse.ArgumentParser(description="batch generate Salvador visualizations")
    parser.add_argument("--input", required=True, help="input JSON file with education papers")
    parser.add_argument("--limit", type=int, default=10, help="max papers to process")
    parser.add_argument("--dry-run", action="store_true", help="don't generate, just show plan")

    args = parser.parse_args()

    # load papers
    with open(args.input) as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} papers")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []

    for i, paper in enumerate(papers[:args.limit]):
        title = paper.get("paper_title", "")[:50]
        discipline = paper.get("discipline", "")

        print(f"\n[{i+1}/{min(len(papers), args.limit)}] {title}...")

        if args.dry_run:
            generated.append(f"{discipline}-{slugify(title)}.js")
            continue

        # generate p5.js code
        code = generate_p5_code(paper)

        if not code:
            print(f"    Failed to generate code")
            continue

        # save
        filename = f"{discipline}-{slugify(title)}.js"
        filepath = OUTPUT_DIR / filename

        with open(filepath, 'w') as f:
            f.write(code)

        print(f"    Saved: {filename}")
        generated.append(filename)

        # also create HTML wrapper
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — The Beakers Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/p5@2.1.2/lib/p5.min.js"></script>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #0f172a; }}
        main {{ box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
    </style>
</head>
<body>
    <main></main>
    <script src="{filename}"></script>
</body>
</html>'''

        html_path = OUTPUT_DIR / f"{discipline}-{slugify(title)}.html"
        with open(html_path, 'w') as f:
            f.write(html)

        time.sleep(1)  # rate limit

    print(f"\n{'='*50}")
    print(f"Generated {len(generated)} visualizations")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
