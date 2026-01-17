// Intellectual Economics
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Closed System", "Internal Processes", "External Interactions", "Diversity Emerges", "Interconnected Ecosystem"];
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
  fill(text);
  noStroke();
  
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
  text("Intellectual Economics", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Biology | Teaching Method", width / 2, 48);
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
  const concepts = ["Stage 1: Neoclassical economics is portrayed as a closed system, like a cell membrane containing internal processes while isolating external influences.", "Stage 2: Internal processes (metabolism, signaling) show repetitive patterns, mimicking algorithmic economic models with limited variability.", "Stage 3: External interactions (trade, information flow) create dynamic boundaries, challenging the closed-system paradigm with biological exchange mechanisms.", "Stage 4: Emergent diversity appears as specialized agents (cells, organisms) with unique behaviors defying monocultural economic models.", "Stage 5: Interconnected ecosystems demonstrate complex, adaptive systems where multiple epistemologies coexist and evolve through interaction."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Closed system base
  let cellRadius = 200 + sin(frameCount * 0.01) * 10;
  ellipse(width/2, height/2, cellRadius*2, cellRadius*2);
  
  // Internal processes
  for (let i=0; i<12; i++) {
    let angle = TWO_PI * i/12;
    let x = width/2 + 80 * cos(angle + sin(frameCount * 0.02)) * 0.5;
    let y = height/2 + 80 * sin(angle + cos(frameCount * 0.03)) * 0.5;
    ellipse(x, y, 6, 6);
  }
}

function drawStage1() {
  // Internal processes with repetition
  for (let i=0; i<24; i++) {
    let angle = TWO_PI * i/24;
    let x = width/2 + 60 * cos(angle + sin(frameCount * 0.01)) * 0.5;
    let y = height/2 + 60 * sin(angle + cos(frameCount * 0.02)) * 0.5;
    ellipse(x, y, 6, 6);
  }
  
  // Boundary oscillation
  let borderOffset = sin(frameCount * 0.015) * 15;
  rect(0, 0, width, height, 10);
}

function drawStage2() {
  // External interactions
  for (let i=0; i<12; i++) {
    let angle = TWO_PI * i/12;
    let x = width/2 + 100 * cos(angle + sin(frameCount * 0.01)) * 0.5;
    let y = height/2 + 100 * sin(angle + cos(frameCount * 0.02)) * 0.5;
    ellipse(x, y, 10, 10);
  }
  
  // Dynamic boundaries
  let borderOffset = sin(frameCount * 0.015) * 20;
  rect(0, 0, width, height, 15);
}

function drawStage3() {
  // Emergent diversity
  for (let i=0; i<24; i++) {
    let angle = TWO_PI * i/24;
    let radius = 80 + sin(frameCount * 0.005 + angle) * 10;
    let x = width/2 + radius * cos(angle);
    let y = height/2 + radius * sin(angle);
    
    // Color variation
    let hue = map(i, 0, 24, 0, 360);
    fill(hue, 200, 200);
    ellipse(x, y, 12, 12);
  }
}

function drawStage4() {
  // Interconnected ecosystem
  for (let i=0; i<36; i++) {
    let angle = TWO_PI * i/36;
    let radius = 100 + sin(frameCount * 0.003 + angle) * 15;
    let x = width/2 + radius * cos(angle);
    let y = height/2 + radius * sin(angle);
    
    // Color variation
    let hue = map(i, 0, 36, 0, 360);
    fill(hue, 200, 200);
    ellipse(x, y, 16, 16);
  }
  
  // Connection lines
  for (let i=0; i<36; i++) {
    let angle = TWO_PI * i/36;
    let x1 = width/2 + 120 * cos(angle);
    let y1 = height/2 + 120 * sin(angle);
    let x2 = width/2 + 150 * cos(angle);
    let y2 = height/2 + 150 * sin(angle);
    
    stroke(accent);
    strokeWeight(1);
    line(x1, y1, x2, y2);
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
