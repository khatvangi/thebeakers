// Family Background and School Choice in Cities of Russia and 
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Family Background Dynamics", "Stage 2: Regional Educational Systems", "Stage 3: School Level Influence", "Stage 4: Policy Moderation Effects", "Stage 5: Cross-National Comparison"];
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
  text("Family Background and School Choice in C", width / 2, 20);

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
  const concepts = ["Particles represent family socioeconomic status with gravity and repulsion forces", "Regions are visualized with heat gradients showing access disparities", "School levels (primary/secondary) are layered with motion vectors", "Policy indicators show varying degrees of student mobility", "Dynamic comparison between Russia and Estonia with physics-based interactions"];
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
  strokeWeight(1);
  for (let i = 0; i < 100; i++) {
    let x = random(width);
    let y = random(height);
    let angle = map(sin(frameCount * 0.01 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 2;
    let dy = sin(angle) * 2;
    line(x, y, x + dx, y + dy);
  }
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  let regions = [250, 350, 450, 550];
  for (let i = 0; i < regions.length; i++) {
    let x = regions[i];
    let y = height/2;
    let angle = map(sin(frameCount * 0.005 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 5;
    let dy = sin(angle) * 5;
    line(x, y, x + dx, y + dy);
    ellipse(x, y, 20, 20);
  }
}

function drawStage2() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(1);
  let schoolLevels = [150, 250, 350];
  for (let i = 0; i < schoolLevels.length; i++) {
    let x = schoolLevels[i];
    let y = height/2;
    let angle = map(sin(frameCount * 0.003 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 3;
    let dy = sin(angle) * 3;
    line(x, y, x + dx, y + dy);
    ellipse(x, y, 15, 15);
  }
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(1);
  let policies = [100, 200, 300];
  for (let i = 0; i < policies.length; i++) {
    let x = policies[i];
    let y = height/2;
    let angle = map(sin(frameCount * 0.002 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 4;
    let dy = sin(angle) * 4;
    line(x, y, x + dx, y + dy);
    ellipse(x, y, 12, 12);
  }
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(1);
  let russiaX = 300;
  let estoniaX = 500;
  let y = height/2;
  let angleR = map(sin(frameCount * 0.001), -1, 1, 0, TWO_PI);
  let angleE = map(sin(frameCount * 0.001 + 1), -1, 1, 0, TWO_PI);
  line(russiaX, y, russiaX + cos(angleR) * 50, y + sin(angleR) * 50);
  line(estoniaX, y, estoniaX + cos(angleE) * 50, y + sin(angleE) * 50);
  ellipse(russiaX, y, 25, 25);
  ellipse(estoniaX, y, 25, 25);
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
