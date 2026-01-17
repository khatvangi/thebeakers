// The Student Nitric Oxide Explorer
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Spacecraft Overview", "Stage 2: Solar Radiation", "Stage 3: Magnetosphere Interactions", "Stage 4: Data Collection", "Stage 5: Scientific Analysis"];
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
  // p5.js draw code that switches on currentStage
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
  text("The Student Nitric Oxide Explorer", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Physics | Experiment", width / 2, 48);
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
  const concepts = ["The SNOE spacecraft is launched to study nitric oxide in the thermosphere. It carries instruments to measure density and energy inputs from solar and magnetospheric sources.", "Energetic EUV/X-ray photons from the sun ionize atmospheric gases, creating nitric oxide through complex photochemical reactions.", "The magnetosphere channels charged particles that collide with atmospheric molecules, influencing nitric oxide density patterns.", "SNOE's sensors detect plasma density variations, correlating them with solar activity and magnetic field fluctuations.", "Data analysis reveals how solar and magnetospheric energy inputs drive nitric oxide abundance in the lower thermosphere."];
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
  ellipse(400, 250, 120 + sin(frameCount * 0.01) * 20, 80 + sin(frameCount * 0.01) * 10);
  fill(text);
  textSize(16);
  text('SNOE Spacecraft', 300, 350);
  stroke(accent);
  strokeWeight(2);
  line(300, 300, 500, 300);
  line(300, 320, 500, 320);
  line(300, 340, 500, 340);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 200; i++) {
    let x = random(850);
    let y = random(540);
    let r = 2 + sin(frameCount * 0.005 + i * 0.1) * 2;
    ellipse(x, y, r, r);
  }
  fill(text);
  textSize(16);
  text('Solar EUV/X-ray photons', 50, 50);
}

function drawStage2() {
  background(bg);
  stroke(accent);
  strokeWeight(1);
  for (let i = 0; i < 100; i++) {
    let x = random(850);
    let y = random(540);
    let angle = random(TAU);
    let length = 20 + sin(frameCount * 0.005 + i * 0.1) * 10;
    line(x, y, x + cos(angle)*length, y + sin(angle)*length);
  }
  fill(text);
  textSize(16);
  text('Magnetic Field Lines', 50, 50);
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 150; i++) {
    let x = random(850);
    let y = random(540);
    let r = 4 + sin(frameCount * 0.005 + i * 0.1) * 2;
    ellipse(x, y, r, r);
  }
  fill(text);
  textSize(16);
  text('Plasma Density Variations', 50, 50);
}

function drawStage4() {
  background(bg);
  noStroke();
  fill(accent);
  let waveHeight = 10 + sin(frameCount * 0.002) * 5;
  for (let i = 0; i < 20; i++) {
    let x = i * 40;
    let y = 270 + sin(frameCount * 0.002 + i * 0.2) * waveHeight;
    ellipse(x, y, 12, 12);
  }
  fill(text);
  textSize(16);
  text('Energy Input Correlation', 50, 50);
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
