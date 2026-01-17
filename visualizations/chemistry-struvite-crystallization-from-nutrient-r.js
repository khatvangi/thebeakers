// Struvite crystallization from nutrient rich wastewater
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Wastewater Inflow", "Nutrient Reaction", "Crystal Nucleation", "Crystal Growth", "Struvite Recovery"];
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
  text("Struvite crystallization from nutrient r", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Chemistry | Experiment", width / 2, 48);
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
  const concepts = ["Nutrient-rich wastewater flows through treatment systems, creating conditions for struvite formation.", "Magnesium, ammonium, and phosphate ions react in solution to form struvite precursors.", "Nucleation sites form the initial crystal structures in supersaturated solutions.", "Crystals grow by adding layers as supersaturation increases, forming hexagonal structures.", "Struvite crystals are harvested and processed into fertilizer, closing the nutrient recovery loop."];
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
  textSize(14);
  text('Nutrient-rich wastewater flows through treatment systems', 20, 30);
  
  // Animated particles
  for (let i = 0; i < 50; i++) {
    let x = random(50, 800);
    let y = random(50, 500);
    let angle = map(sin(frameCount * 0.01 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 1;
    let dy = sin(angle) * 1;
    ellipse(x + dx, y + dy, 4, 4);
  }
}

function drawStage1() {
  background(#0f172a);
  fill(#10b981);
  textSize(16);
  text('Mg²+ + NH4+ + PO4^3- → MgNH4PO4', 20, 30);
  
  // Animated ions
  let ionSize = 8;
  let ionSpacing = 50;
  for (let i = 0; i < 3; i++) {
    let x = 200 + i * ionSpacing;
    let y = 100;
    let angle = map(sin(frameCount * 0.01 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 1;
    let dy = sin(angle) * 1;
    ellipse(x + dx, y + dy, ionSize, ionSize);
  }
  
  // Reaction arrow
  stroke(#10b981);
  strokeWeight(2);
  line(230, 100, 280, 100);
  bezier(280, 100, 290, 80, 300, 100, 310, 120);
}

function drawStage2() {
  background(#0f172a);
  fill(#e2e8f0);
  textSize(16);
  text('Nucleation sites form the first crystal structures', 20, 30);
  
  // Animated crystal nuclei
  for (let i = 0; i < 10; i++) {
    let x = random(50, 750);
    let y = random(50, 450);
    let angle = map(sin(frameCount * 0.01 + i), -1, 1, 0, TWO_PI);
    let dx = cos(angle) * 2;
    let dy = sin(angle) * 2;
    ellipse(x + dx, y + dy, 6, 6);
  }
  
  // Hexagon outline
  stroke(#10b981);
  strokeWeight(1);
  beginShape();
  for (let i = 0; i < 6; i++) {
    let angle = TWO_PI / 6 * i;
    let x = 400 + cos(angle) * 20;
    let y = 300 + sin(angle) * 20;
    vertex(x, y);
  }
  endShape();
}

function drawStage3() {
  background(#0f172a);
  fill(#e2e8f0);
  textSize(16);
  text('Crystals grow by layer addition', 20, 30);
  
  // Growing crystals
  let crystalRadius = 20 + sin(frameCount * 0.005) * 10;
  stroke(#10b981);
  strokeWeight(1);
  beginShape();
  for (let i = 0; i < 6; i++) {
    let angle = TWO_PI / 6 * i;
    let x = 400 + cos(angle) * crystalRadius;
    let y = 300 + sin(angle) * crystalRadius;
    vertex(x, y);
  }
  endShape();
  
  // Growth animation
  for (let i = 0; i < 5; i++) {
    let x = 400 + cos(TWO_PI / 5 * i) * 25;
    let y = 300 + sin(TWO_PI / 5 * i) * 25;
    ellipse(x, y, 4, 4);
  }
}

function drawStage4() {
  background(#0f172a);
  fill(#10b981);
  textSize(18);
  text('Struvite (MgNH4PO4·6H2O)', 20, 30);
  
  // Crystal lattice
  stroke(#10b981);
  strokeWeight(1);
  beginShape();
  for (let i = 0; i < 6; i++) {
    let angle = TWO_PI / 6 * i;
    let x = 400 + cos(angle) * 30;
    let y = 300 + sin(angle) * 30;
    vertex(x, y);
  }
  endShape();
  
  // Formula text
  fill(#e2e8f0);
  textSize(16);
  text('Harvested as fertilizer', 20, 200);
  text('MgNH4PO4·6H2O', 20, 230);
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
