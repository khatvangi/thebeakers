// Development Education
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Foundation", "Circuit Integration", "Structural Framework", "Network Expansion", "Sustainable Systems"];
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

function draw() {
  background(bg);
  noStroke();
  fill(bg);
  rect(0, 0, width, height);
  
  if (currentStage === 0) {
    drawStage0();
  } else if (currentStage === 1) {
    drawStage1();
  } else if (currentStage === 2) {
    drawStage2();
  } else if (currentStage === 3) {
    drawStage3();
  } else if (currentStage === 4) {
    drawStage4();
  }

  // Micro-movement for all stages
  fill(accent);
  textSize(14);
  text(`Stage ${currentStage + 1}`, 10, 20);
}

function mousePressed() {
  currentStage = (currentStage + 1) % num_stages;
}
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
  text("Development Education", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Engineering | General", width / 2, 48);
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
  const concepts = ["Basic engineering principles form the foundation of development education.", "Circuits and systems demonstrate how knowledge flows through educational networks.", "Structural elements represent the framework supporting educational infrastructure.", "Expanding connections show how collaboration enhances educational impact.", "Sustainable systems emphasize long-term development and eco-friendly practices."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Rotating gear base
  push();
  translate(width/2, height/2);
  rotate(sin(frameCount * 0.002) * 0.1);
  fill(accent);
  stroke(accent);
  strokeWeight(2);
  ellipse(0, 0, 100, 100);
  // Pulsing text
  fill(text);
  noStroke();
  textSize(16);
  text('Engineering Foundations', -100, 50);
  pop();
}

function drawStage1() {
  // Animated circuit nodes
  push();
  translate(100, 100);
  for (let i = 0; i < 5; i++) {
    let x = 50 + i * 60;
    let y = 50;
    let size = 20 + sin(frameCount * 0.01 + i * 0.3) * 5;
    fill(accent);
    ellipse(x, y, size, size);
    // Connecting lines
    stroke(accent);
    strokeWeight(1);
    line(x, y, x + 30, y);
  }
  pop();
  // Text overlay
  fill(text);
  noStroke();
  textSize(16);
  text('Knowledge Flow', 20, 150);
}

function drawStage2() {
  // Structural framework with animated beams
  push();
  translate(width/2, height/2);
  // Pulsing beams
  for (let i = 0; i < 4; i++) {
    let angle = map(i, 0, 4, 0, TWO_PI);
    let x = cos(angle) * 150;
    let y = sin(angle) * 150;
    let length = 100 + sin(frameCount * 0.005 + i * 0.5) * 10;
    stroke(accent);
    strokeWeight(3);
    line(x, y, x + cos(angle) * length, y + sin(angle) * length);
  }
  pop();
  fill(text);
  textSize(16);
  text('Educational Infrastructure', 20, 150);
}

function drawStage3() {
  // Network expansion with growing nodes
  push();
  translate(width/2, height/2);
  for (let i = 0; i < 8; i++) {
    let angle = map(i, 0, 8, 0, TWO_PI);
    let radius = 80 + sin(frameCount * 0.003 + i * 0.4) * 15;
    let x = cos(angle) * radius;
    let y = sin(angle) * radius;
    fill(accent);
    noStroke();
    ellipse(x, y, 20, 20);
    // Connecting lines
    stroke(accent);
    strokeWeight(1);
    line(x, y, x + cos(angle) * 40, y + sin(angle) * 40);
  }
  pop();
  fill(text);
  textSize(16);
  text('Collaborative Networks', 20, 150);
}

function drawStage4() {
  // Sustainable systems with rotating eco-circle
  push();
  translate(width/2, height/2);
  rotate(sin(frameCount * 0.002) * 0.1);
  // Eco-circle
  fill(accent);
  stroke(accent);
  strokeWeight(2);
  ellipse(0, 0, 120, 120);
  // Text overlay
  fill(text);
  noStroke();
  textSize(16);
  text('Sustainable Development', -100, 50);
  pop();
  fill(text);
  textSize(14);
  text('Eco-friendly practices', 20, 150);
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
