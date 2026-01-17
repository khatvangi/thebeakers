// Development Education
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Foundation", "Growth Patterns", "Quadratic Paths", "Sponsorship Dynamics", "Educational Synergy"];
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
  function draw() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  if (currentStage === 0) { drawStage0(); }
  else if (currentStage === 1) { drawStage1(); }
  else if (currentStage === 2) { drawStage2(); }
  else if (currentStage === 3) { drawStage3(); }
  else if (currentStage === 4) { drawStage4(); }
}

function drawStage0() {
  let amp = sin(frameCount * 0.01) * 20;
  line(50, height/2 + amp, 750, height/2 + amp);
  ellipse(50, height/2 + amp, 10, 10);
  ellipse(750, height/2 + amp, 10, 10);
}

function drawStage1() {
  for (let i = 0; i < 10; i++) {
    let y = height/2 + sin(frameCount * 0.01 + i * 0.2) * 30;
    ellipse(100 + i*60, y, 12, 12);
    line(100 + i*60, y, 100 + i*60 + 15, y);
  }
}

function drawStage2() {
  bezierOrder(2);
  let cp1x = 300 + sin(frameCount * 0.005) * 30;
  let cp1y = height/2 + sin(frameCount * 0.005) * 20;
  let cp2x = 500 + sin(frameCount * 0.005) * 30;
  let cp2y = height/2 + sin(frameCount * 0.005) * 20;
  
  beginShape();
  splineVertex(200, height/2);
  splineVertex(cp1x, cp1y);
  splineVertex(600, height/2);
  splineVertex(cp2x, cp2y);
  splineVertex(800, height/2);
  endShape();
}

function drawStage3() {
  for (let i = 0; i < 5; i++) {
    let angle = frameCount * 0.02 + i * 0.3;
    let x = 400 + sin(angle) * 40;
    let y = 270 + cos(angle) * 40;
    ellipse(x, y, 10, 10);
    line(x, y, x + 15, y);
  }
  
  for (let i = 0; i < 4; i++) {
    let angle = frameCount * 0.015 + i * 0.4;
    let x = 500 + sin(angle) * 30;
    let y = 270 + cos(angle) * 30;
    ellipse(x, y, 10, 10);
  }
}

function drawStage4() {
  for (let i = 0; i < 8; i++) {
    let angle = frameCount * 0.01 + i * 0.25;
    let x = 400 + sin(angle) * 30;
    let y = 270 + cos(angle) * 30;
    ellipse(x, y, 10, 10);
    line(x, y, x + 15, y);
  }
  
  for (let i = 0; i < 6; i++) {
    let angle = frameCount * 0.015 + i * 0.3;
    let x = 500 + sin(angle) * 25;
    let y = 270 + cos(angle) * 25;
    ellipse(x, y, 10, 10);
  }
  
  bezierOrder(2);
  beginShape();
  splineVertex(200, height/2);
  splineVertex(300 + sin(frameCount * 0.005) * 30, height/2 + sin(frameCount * 0.005) * 20);
  splineVertex(600, height/2);
  splineVertex(700 + sin(frameCount * 0.005) * 30, height/2 + sin(frameCount * 0.005) * 20);
  splineVertex(800, height/2);
  endShape();
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
  const concepts = ["Mathematical foundations of sponsorship growth through geometric patterns", "Sinusoidal movement representing educational progress over time", "Quadratic curves modeling development trajectories with dynamic control points", "Interactive sponsorship visualization with animated node connections", "Integrated mathematical model showing educational impact through evolving patterns"];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  let amp = sin(frameCount * 0.01) * 20;
  line(50, height/2 + amp, 750, height/2 + amp);
  ellipse(50, height/2 + amp, 10, 10);
  ellipse(750, height/2 + amp, 10, 10);
}

function drawStage1() {
  for (let i = 0; i < 10; i++) {
    let y = height/2 + sin(frameCount * 0.01 + i * 0.2) * 30;
    ellipse(100 + i*60, y, 12, 12);
    line(100 + i*60, y, 100 + i*60 + 15, y);
  }
}

function drawStage2() {
  bezierOrder(2);
  let cp1x = 300 + sin(frameCount * 0.005) * 30;
  let cp1y = height/2 + sin(frameCount * 0.005) * 20;
  let cp2x = 500 + sin(frameCount * 0.005) * 30;
  let cp2y = height/2 + sin(frameCount * 0.005) * 20;
  
  beginShape();
  splineVertex(200, height/2);
  splineVertex(cp1x, cp1y);
  splineVertex(600, height/2);
  splineVertex(cp2x, cp2y);
  splineVertex(800, height/2);
  endShape();
}

function drawStage3() {
  for (let i = 0; i < 5; i++) {
    let angle = frameCount * 0.02 + i * 0.3;
    let x = 400 + sin(angle) * 40;
    let y = 270 + cos(angle) * 40;
    ellipse(x, y, 10, 10);
    line(x, y, x + 15, y);
  }
  
  for (let i = 0; i < 4; i++) {
    let angle = frameCount * 0.015 + i * 0.4;
    let x = 500 + sin(angle) * 30;
    let y = 270 + cos(angle) * 30;
    ellipse(x, y, 10, 10);
  }
}

function drawStage4() {
  for (let i = 0; i < 8; i++) {
    let angle = frameCount * 0.01 + i * 0.25;
    let x = 400 + sin(angle) * 30;
    let y = 270 + cos(angle) * 30;
    ellipse(x, y, 10, 10);
    line(x, y, x + 15, y);
  }
  
  for (let i = 0; i < 6; i++) {
    let angle = frameCount * 0.015 + i * 0.3;
    let x = 500 + sin(angle) * 25;
    let y = 270 + cos(angle) * 25;
    ellipse(x, y, 10, 10);
  }
  
  bezierOrder(2);
  beginShape();
  splineVertex(200, height/2);
  splineVertex(300 + sin(frameCount * 0.005) * 30, height/2 + sin(frameCount * 0.005) * 20);
  splineVertex(600, height/2);
  splineVertex(700 + sin(frameCount * 0.005) * 30, height/2 + sin(frameCount * 0.005) * 20);
  splineVertex(800, height/2);
  endShape();
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
