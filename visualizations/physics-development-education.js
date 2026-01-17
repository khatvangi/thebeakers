// Development Education
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Particles in Motion", "Stage 2: Force Vectors", "Stage 3: Energy Transfer", "Stage 4: System Dynamics", "Stage 5: Educational Impact"];
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
  background(#0f172a);
  noFill();
  stroke(#e2e8f0);
  strokeWeight(1);
  
  if (currentStage === 0) { drawStage0(); } 
  else if (currentStage === 1) { drawStage1(); }
  else if (currentStage === 2) { drawStage2(); }
  else if (currentStage === 3) { drawStage3(); }
  else if (currentStage === 4) { drawStage4(); }
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
  text("Physics | General", width / 2, 48);
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
  const concepts = ["Fundamental particles exhibit continuous motion patterns", "Forces act as vectors influencing particle trajectories", "Energy transfer occurs through dynamic interactions", "System behavior emerges from interconnected components", "Educational impact grows through iterative development"];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Particle motion with sine waves
  for (let i = 0; i < 12; i++) {
    let x = 100 + i * 60;
    let y = 200 + sin(frameCount * 0.01 + i) * 20;
    ellipse(x, y, 12, 12);
    line(x, y, x + 10, y - 5);
  }
}

function drawStage1() {
  // Force vectors with rotation
  for (let i = 0; i < 8; i++) {
    let angle = map(i, 0, 8, 0, TWO_PI);
    let x = 400 + cos(angle + sin(frameCount * 0.01)) * 50;
    let y = 300 + sin(angle + cos(frameCount * 0.01)) * 30;
    push();
    translate(x, y);
    rotate(angle);
    line(0, 0, 20, 0);
    fill(#10b981);
    ellipse(20, 0, 8, 8);
    pop();
  }
}

function drawStage2() {
  // Energy transfer visualization
  for (let i = 0; i < 6; i++) {
    let x = 300 + i * 100;
    let y = 250 + sin(frameCount * 0.01 + i * 1.5) * 15;
    let size = 16 + sin(frameCount * 0.02 + i) * 8;
    ellipse(x, y, size, size);
    strokeWeight(2);
    line(x, y, x + 40, y);
  }
}

function drawStage3() {
  // System dynamics with orbits
  bezierOrder(2);
  for (let i = 0; i < 4; i++) {
    let angle = map(i, 0, 4, 0, TWO_PI);
    let x = 600 + cos(angle + sin(frameCount * 0.01)) * 40;
    let y = 350 + sin(angle + cos(frameCount * 0.01)) * 30;
    let radius = 20 + sin(frameCount * 0.02 + i) * 10;
    ellipse(x, y, 12, 12);
    splineVertex(x, y, x + cos(angle) * radius, y + sin(angle) * radius);
  }
}

function drawStage4() {
  // Educational impact visualization
  for (let i = 0; i < 5; i++) {
    let x = 700 + i * 120;
    let y = 400 + sin(frameCount * 0.01 + i * 1.2) * 20;
    let size = 16 + sin(frameCount * 0.02 + i) * 8;
    ellipse(x, y, size, size);
    strokeWeight(2);
    line(x, y, x + 30, y);
    fill(#10b981);
    ellipse(x + 25, y, 6, 6);
  }
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
