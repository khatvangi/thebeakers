// Greener Journal of Agricultural Sciences
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Degraded Soil", "Stage 2: Animal Wastes", "Stage 3: Experimental Setup", "Stage 4: Nutrient Release", "Stage 5: Productivity Results"];
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
  text("Greener Journal of Agricultural Sciences", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Agriculture | Experiment", width / 2, 48);
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
  const concepts = ["Degraded soil lacks essential nutrients, hindering crop growth. This study investigates how animal waste can restore soil fertility.", "Poultry, swine, and cow wastes contain varying nutrient profiles. Each waste type has unique organic matter and mineral content.", "A factorial experiment compares waste application rates and soil treatments. Each plot receives different combinations of waste types and quantities.", "Nutrient availability depends on decomposition processes. Microorganisms break down waste, releasing nitrogen, phosphorus, and potassium.", "Productivity metrics show how different waste types affect plant growth. Results highlight optimal waste application strategies."];
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
  textAlign(CENTER, CENTER);
  text('Degraded Soil', width/2, 50);
  
  // Soil texture
  fill(50, 50, 50);
  for (let i = 0; i < 20; i++) {
    let x = random(width);
    let y = random(height);
    let s = random(5, 15);
    ellipse(x, y, s, s);
  }
  
  // Cracks effect
  fill(100, 100, 100, 50);
  for (let i = 0; i < 10; i++) {
    let x1 = random(width);
    let y1 = random(height);
    let x2 = x1 + random(-50, 50);
    let y2 = y1 + random(-50, 50);
    ellipse(x1, y1, 10, 10);
    ellipse(x2, y2, 10, 10);
    line(x1, y1, x2, y2);
  }
}

function drawStage1() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textAlign(CENTER, CENTER);
  text('Animal Wastes', width/2, 50);
  
  // Waste particles
  fill(#10b981);
  for (let i = 0; i < 30; i++) {
    let x = random(width);
    let y = random(height);
    let s = random(8, 18);
    ellipse(x, y, s, s);
    // Micro-movement
    let angle = map(sin(frameCount * 0.01 + x), -1, 1, 0, TWO_PI);
    translate(x, y);
    rotate(angle);
    ellipse(0, 0, s, s);
    rotate(-angle);
    translate(-x, -y);
  }
  
  // Waste labels
  fill(#e2e8f0);
  text('Poultry', 100, 100);
  text('Swine', 450, 100);
  text('Cow', 750, 100);
}

function drawStage2() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textAlign(CENTER, CENTER);
  text('Experimental Setup', width/2, 50);
  
  // Greenhouse structure
  fill(50, 50, 50);
  rect(0, 100, width, height - 100);
  
  // Plot dividers
  stroke(#10b981);
  strokeWeight(2);
  line(200, 150, 200, height - 100);
  line(600, 150, 600, height - 10, 10);
  
  // Waste symbols
  fill(#10b981);
  for (let i = 0; i < 10; i++) {
    let x = random(200, 600);
    let y = random(150, height - 100);
    ellipse(x, y, 12, 12);
    // Micro-movement
    let angle = map(sin(frameCount * 0.01 + x), -1, 1, 0, TWO_PI);
    translate(x, y);
    rotate(angle);
    ellipse(0, 0, 12, 12);
    rotate(-angle);
    translate(-x, -y);
  }
}

function drawStage3() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textAlign(CENTER, CENTER);
  text('Nutrient Release', width/2, 50);
  
  // Soil base
  fill(50, 50, 50);
  rect(0, 100, width, height - 100);
  
  // Nutrient flow
  fill(#10b981);
  for (let i = 0; i < 15; i++) {
    let x = random(width);
    let y = random(100, height);
    let size = random(4, 8);
    ellipse(x, y, size, size);
    // Micro-movement
    let angle = map(sin(frameCount * 0.01 + x), -1, 1, 0, TWO_PI);
    translate(x, y);
    rotate(angle);
    ellipse(0, 0, size, size);
    rotate(-angle);
    translate(-x, -y);
  }
  
  // Arrows for nutrient movement
  stroke(#10b981);
  strokeWeight(1);
  for (let i = 0; i < 20; i++) {
    let x = random(width);
    let y = random(150, height - 50);
    let dx = random(-10, 10);
    let dy = random(-10, 10);
    line(x, y, x + dx, y + dy);
  }
}

function drawStage4() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textAlign(CENTER, CENTER);
  text('Productivity Results', width/2, 50);
  
  // Soil base
  fill(50, 50, 50);
  rect(0, 100, width, height - 100);
  
  // Plant growth
  fill(#10b981);
  for (let i = 0; i < 30; i++) {
    let x = random(100, width - 100);
    let y = random(150, height - 100);
    let size = random(10, 20);
    ellipse(x, y, size, size);
    // Micro-movement
    let angle = map(sin(frameCount * 0.01 + x), -1, 1, 0, TWO_PI);
    translate(x, y);
    rotate(angle);
    ellipse(0, 0, size, size);
    rotate(-angle);
    translate(-x, -y);
  }
  
  // Data visualization
  fill(#e2e8f0);
  text('Poultry: +45%', 100, 100);
  text('Swine: +32%', 450, 100);
  text('Cow: +28%', 750, 100);
  
  // Graph bars
  stroke(#10b981);
  strokeWeight(2);
  for (let i = 0; i < 3; i++) {
    let x = 100 + i * 300;
    let y = 150;
    let barHeight = map([45, 32, 28][i], 0, 50, 50, 100);
    rect(x, y, 50, barHeight);
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
