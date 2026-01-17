// International Journal of Scientific Research
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Cellular Stress", "Stage 2: DNA Damage", "Stage 3: Neural Overload", "Stage 4: Recovery Pathways", "Stage 5: Healthy Environment"];
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
  text("International Journal of Scientific Rese", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Biology | General", width / 2, 48);
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
  const concepts = ["Microscopic stress signals disrupt cellular balance", "DNA damage accumulates with chronic stress exposure", "Neural pathways become overstimulated in burnout states", "Recovery requires targeted physiological interventions", "Optimal work environments promote cellular resilience"];
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
  noStroke();
  fill(accent);
  for (let i = 0; i < 100; i++) {
    let x = random(width);
    let y = height/2 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, 4, 4);
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Cellular Stress', width/2, height/2);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  bezierOrder(2);
  for (let i = 0; i < 20; i++) {
    let x = i * 20;
    let y = height/2 + sin(frameCount * 0.005 + i) * 5;
    splineVertex(x, y, x + 10, y + 10, x + 20, y);
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('DNA Damage', width/2, height/2);
}

function drawStage2() {
  background(bg);
  noStroke();
  fill(accent);
  for (let i = 0; i < 50; i++) {
    let x = random(width);
    let y = height/2 + sin(frameCount * 0.01 + i) * 15;
    ellipse(x, y, 6, 6);
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Neural Overload', width/2, height/2);
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 15; i++) {
    let x = i * 30;
    let y = height/2 + sin(frameCount * 0.005 + i) * 8;
    line(x, y, x + 10, y + 10);
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Recovery Pathways', width/2, height/2);
}

function drawStage4() {
  background(bg);
  noStroke();
  fill(accent);
  for (let i = 0; i < 80; i++) {
    let x = random(width);
    let y = height/2 + sin(frameCount * 0.01 + i) * 8;
    ellipse(x, y, 5, 5);
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Healthy Environment', width/2, height/2);
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
