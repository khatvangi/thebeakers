// Artificial Intelligence in Clinical Medicine: Challenges Acr
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Diagnostic Imaging", "Stage 2: Clinical Decision Support", "Stage 3: Surgical Precision", "Stage 4: Pathological Analysis", "Stage 5: Drug Discovery"];
let transitioning = false;
let transitionProgress = 0;

// colors
const colors = {
  bg: "#0f172a",
  card: "#1e293b",
  accent: "#10b981",
  text: "#e2e8f0",
  secondary: "#94a3b8",
};

function setup() {
  createCanvas(850, 540);
  textFont("system-ui");
}

function draw() {
  background(colors.bg);

  // header
  drawHeader();

  // stage indicator
  drawStageIndicator();

  // main visualization area
  push();
  translate(width / 2, height / 2 - 30);
  let currentStage = 0;

if (currentStage === 0) { drawStage0(); } else if (currentStage === 1) { drawStage1(); } else if (currentStage === 2) { drawStage2(); } else if (currentStage === 3) { drawStage3(); } else if (currentStage === 4) { drawStage4(); }
  pop();

  // data card
  drawDataCard();

  // controls hint
  drawControls();

  // handle transitions
  if (transitioning) {
    transitionProgress += 0.05;
    if (transitionProgress >= 1) {
      transitioning = false;
      transitionProgress = 0;
    }
  }
}

function drawHeader() {
  fill(colors.text);
  textSize(20);
  textAlign(CENTER, TOP);
  text("Artificial Intelligence in Clinical Medi", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Chemistry | Experiment", width / 2, 48);
}

function drawStageIndicator() {
  let y = 75;
  let dotSize = 12;
  let spacing = 30;
  let startX = width / 2 - ((totalStages - 1) * spacing) / 2;

  for (let i = 0; i < totalStages; i++) {
    let x = startX + i * spacing;
    if (i === currentStage) {
      fill(colors.accent);
      ellipse(x, y, dotSize + 4);
    } else if (i < currentStage) {
      fill(colors.accent);
      ellipse(x, y, dotSize);
    } else {
      noFill();
      stroke(colors.secondary);
      strokeWeight(2);
      ellipse(x, y, dotSize);
      noStroke();
    }
  }

  fill(colors.text);
  textSize(14);
  textAlign(CENTER, TOP);
  text(stageLabels[currentStage], width / 2, y + 15);
}

function drawDataCard() {
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
}

function getConceptForStage(stage) {
  const concepts = ["AI in diagnostic imaging enables early detection of diseases through pattern recognition in medical scans, revolutionizing how clinicians interpret complex data.", "Clinical decision support systems leverage AI to analyze patient data, offering real-time recommendations that enhance treatment planning and reduce diagnostic errors.", "AI-powered robotic surgery systems improve precision and reduce human error, enabling complex procedures with sub-millimeter accuracy through machine learning algorithms.", "AI analyzes histopathological slides to identify cancerous patterns, accelerating diagnosis and enabling personalized treatment strategies for patients.", "AI accelerates drug discovery by simulating molecular interactions, predicting drug efficacy, and optimizing chemical compounds for targeted therapeutic effects."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  background(#0f172a);
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 50; i++) {
    let angle = frameCount * 0.01 + i * 0.1;
    let x = 400 + 150 * sin(angle);
    let y = 270 + 150 * cos(angle);
    ellipse(x, y, 10 + sin(angle * 2)*5, 10 + cos(angle * 2)*5);
  }
  fill(#e2e8f0);
  textSize(14);
  text("AI identifies patterns in medical scans for early disease detection", 20, 30);
}

function drawStage1() {
  background(#0f172a);
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 30; i++) {
    let angle = frameCount * 0.02 + i * 0.15;
    let x = 400 + 100 * sin(angle);
    let y = 270 + 100 * cos(angle);
    ellipse(x, y, 8 + sin(angle * 2)*4, 8 + cos(angle * 2)*4);
  }
  fill(#e2e8f0);
  textSize(14);
  text("AI provides real-time clinical recommendations for treatment planning", 20, 30);
}

function drawStage2() {
  background(#0f172a);
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 20; i++) {
    let angle = frameCount * 0.03 + i * 0.2;
    let x = 400 + 80 * sin(angle);
    let y = 270 + 80 * cos(angle);
    ellipse(x, y, 6 + sin(angle * 2)*3, 6 + cos(angle * 2)*3);
  }
  fill(#e2e8f0);
  textSize(14);
  text("AI enables sub-millimeter precision in robotic surgical procedures", 20, 30);
}

function drawStage3() {
  background(#0f172a);
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 40; i++) {
    let angle = frameCount * 0.015 + i * 0.12;
    let x = 400 + 120 * sin(angle);
    let y = 270 + 120 * cos(angle);
    ellipse(x, y, 10 + sin(angle * 2)*5, 10 + cos(angle * 2)*5);
  }
  fill(#e2e8f0);
  textSize(14);
  text("AI detects cancerous patterns in histopathological tissue samples", 20, 30);
}

function drawStage4() {
  background(#0f172a);
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 60; i++) {
    let angle = frameCount * 0.01 + i * 0.1;
    let x = 400 + 100 * sin(angle);
    let y = 270 + 100 * cos(angle);
    ellipse(x, y, 8 + sin(angle * 2)*4, 8 + cos(angle * 2)*4);
  }
  fill(#e2e8f0);
  textSize(14);
  text("AI accelerates drug discovery by simulating molecular interactions", 20, 30);
}

function keyPressed() {
  if (keyCode === RIGHT_ARROW && currentStage < totalStages - 1) {
    currentStage++;
    transitioning = true;
    transitionProgress = 0;
  } else if (keyCode === LEFT_ARROW && currentStage > 0) {
    currentStage--;
    transitioning = true;
    transitionProgress = 0;
  } else if (key === "r" || key === "R") {
    currentStage = 0;
  } else if (key === "g" || key === "G") {
    saveGif("visualization.gif", 5);
  }
}

// micro-movement for continuous animation
function microMove(baseX, baseY, amplitude = 2) {
  return {
    x: baseX + sin(frameCount * 0.02) * amplitude,
    y: baseY + cos(frameCount * 0.03) * amplitude
  };
}
