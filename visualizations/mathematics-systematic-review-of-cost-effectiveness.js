// Systematic review of cost effectiveness and budget impact of
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: AI in Healthcare", "Stage 2: Cost Reduction", "Stage 3: Cost-Effectiveness", "Stage 4: Budget Impact", "Stage 5: Summary"];
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
  if (currentStage === 0) { drawStage0(); } else if (currentStage === 1) { drawStage1(); } else if (currentStage === 2) { drawStage2(); } else if (currentStage === 3) { drawStage3(); } else { drawStage4(); }
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
  text("Systematic review of cost effectiveness ", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Mathematics | General", width / 2, 48);
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
  const concepts = ["AI interventions are transforming healthcare through mathematical optimization of diagnostic processes and resource allocation.", "Cost reductions emerge from probabilistic modeling of clinical pathways and predictive analytics.", "Cost-effectiveness analysis quantifies health outcomes using mathematical models of quality-adjusted life years (QALYs).", "Budget impact analysis tracks financial implications through dynamic resource allocation algorithms.", "Mathematical frameworks enable rigorous evaluation of AI's economic and clinical value across healthcare domains."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  bezierOrder(2);
  
  // Animated sine wave pattern
  let y = map(sin(frameCount * 0.005), -1, 1, 20, height - 20);
  bezier(0, y, 50, y, 150, height - y, 200, height - y);
  
  // Animated text
  fill(text);
  textSize(16);
  text('AI transforms healthcare through mathematical optimization', 20, 30);
  text('of diagnostic processes and resource allocation', 20, 50);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(1.5);
  
  // Animated data points
  for (let i = 0; i < 10; i++) {
    let x = map(sin(i + frameCount * 0.01), -1, 1, 50, width - 50);
    let y = map(cos(i + frameCount * 0.02), -1, 1, 50, height - 50);
    point(x, y);
  }
  
  // Animated cost reduction line
  strokeWeight(2);
  line(50, height - 50, width - 50, 50);
  
  fill(text);
  textSize(16);
  text('Cost reductions from probabilistic modeling', 20, 30);
}

function drawStage2() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Animated cost-effectiveness graph
  beginShape();
  for (let i = 0; i < width; i++) {
    let y = map(sin(i/width * PI * 2 + frameCount * 0.005), -1, 1, 50, height - 50);
    vertex(i, y);
  }
  endShape();
  
  // Animated QALYs markers
  for (let i = 0; i < 5; i++) {
    let x = map(i, 0, 5, 50, width - 50);
    let y = height - 50 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, 10, 10);
  }
  
  fill(text);
  textSize(16);
  text('Cost-effectiveness quantifies health outcomes', 20, 30);
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Animated budget impact curve
  beginShape();
  for (let i = 0; i < width; i++) {
    let y = map(cos(i/width * PI * 2 + frameCount * 0.005), -1, 1, 50, height - 50);
    vertex(i, y);
  }
  endShape();
  
  // Animated resource allocation markers
  for (let i = 0; i < 4; i++) {
    let x = map(i, 0, 4, 50, width - 50);
    let y = height - 50 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, 12, 12);
  }
  
  fill(text);
  textSize(16);
  text('Budget impact tracks financial implications', 20, 30);
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Animated comparison graph
  beginShape();
  for (let i = 0; i < width; i++) {
    let y = map(sin(i/width * PI * 2 + frameCount * 0.005), -1, 1, 50, height - 50);
    vertex(i, y);
  }
  endShape();
  
  // Animated mathematical framework markers
  for (let i = 0; i < 6; i++) {
    let x = map(i, 0, 6, 50, width - 50);
    let y = height - 50 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, 14, 14);
  }
  
  fill(text);
  textSize(16);
  text('Mathematical frameworks enable rigorous evaluation', 20, 30);
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
