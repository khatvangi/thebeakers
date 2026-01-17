// Outcasting: Enforcement in Domestic and International Law
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Social Fabric", "Stage 2: Exclusion Dynamics", "Stage 3: Legal Framework", "Stage 4: Global Reach", "Stage 5: Systemic Impact"];
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

if (currentStage === 0) { drawStage0(); } 
else if (currentStage === 1) { drawStage1(); } 
else if (currentStage === 2) { drawStage2(); } 
else if (currentStage === 3) { drawStage3(); } 
else if (currentStage === 4) { drawStage4(); }
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
  text("Outcasting: Enforcement in Domestic and ", width / 2, 20);

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
  const concepts = ["Stage 1 introduces the social fabric as a network of interconnected nodes representing individuals and systems. These nodes pulse gently to show the baseline of cooperation.", "Stage 2 demonstrates how outcasting begins with subtle exclusion. Nodes gradually drift apart, symbolizing the erosion of social bonds through nonviolent separation.", "Stage 3 visualizes legal frameworks as structural beams that oscillate, showing how systems maintain order through symbolic boundaries rather than physical force.", "Stage 4 illustrates international law as a network of rotating nodes, with some elements fading to represent the complexities of global enforcement mechanisms.", "Stage 5 reveals systemic consequences through a dynamic network where nodes pulse in sync with their connectivity status, showing how exclusion propagates through systems."];
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
  fill(#e2e8f0);
  for (let i=0; i<20; i++) {
    for (let j=0; j<20; j++) {
      let x = 40 + i*40;
      let y = 40 + j*40;
      let size = 10 + 5*sin(frameCount/10 + i*2 + j*2);
      ellipse(x, y, size, size);
    }
  }
}

function drawStage1() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  for (let i=0; i<20; i++) {
    for (let j=0; j<20; j++) {
      let x = 40 + i*40;
      let y = 40 + j*4,0;
      let dx = 2*sin(frameCount/15 + i*1.5);
      let dy = 2*sin(frameCount/15 + j*1.5);
      ellipse(x+dx, y+dy, 8, 8);
    }
  }
  fill(#10b981);
  for (let i=0; i<10; i++) {
    ellipse(40 + i*40, 40, 12, 12);
  }
}

function drawStage2() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  for (let i=0; i<15; i++) {
    for (let j=0; j<15; j++) {
      let x = 40 + i*40;
      let y = 40 + j*40;
      let size = 8 + 4*sin(frameCount/12 + i*2 + j*2);
      ellipse(x, y, size, size);
      if (i % 2 === 0 && j % 2 === 0) {
        fill(#10b981);
        ellipse(x, y, size*0.6, size*0.6);
      }
    }
  }
}

function drawStage3() {
  background(#0f172a);
  noFill();
  stroke(#10b981);
  bezierOrder(2);
  for (let i=0; i<10; i++) {
    let x1 = 40 + i*60;
    let y1 = 40;
    let x2 = 40 + i*60;
    let y2 = 320;
    let ctrlX = x1 + 30*sin(frameCount/10 + i);
    let ctrlY = y1 + 30*cos(frameCount/10 + i);
    beginShape();
    splineVertex(x1, y1);
    splineVertex(ctrlX, ctrlY);
    splineVertex(x2, y2);
    endShape();
  }
}

function drawStage4() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  for (let i=0; i<12; i++) {
    let angle = map(i, 0, 12, 0, TWO_PI);
    let x = 420 + 150*cos(angle);
    let y = 270 + 150*sin(angle);
    let size = 8 + 4*sin(frameCount/15 + i);
    ellipse(x, y, size, size);
    if (i % 2 === 0) {
      fill(#10b981);
      ellipse(x, y, size*0.6, size*0.6);
    }
  }
  fill(#10b981);
  ellipse(420, 270, 12, 12);
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
