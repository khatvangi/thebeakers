// Development Education
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Cell Division", "DNA Replication", "Cell Differentiation", "Organ Systems", "Ecological Development"];
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
  noFill();
  stroke(text);
  strokeWeight(1);
  
  if (currentStage === 0) {
    drawStage0();
  } else if (currentStage === 1) {
    drawStage1();
  } else if (currentStage === 2) {
    drawStage2();
  } else if (currentStage === 3) {
    drawStage3();
  } else {
    drawStage4();
  }

  // Micro-movement
  for (let i = 0; i < 5; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let r = sin(frameCount * 0.01 + i) * 2 + 5;
    ellipse(x, y, r, r);
  }
}

function drawStage0() {
  stroke(accent);
  strokeWeight(2);
  
  // Animated cell division
  let angle = map(sin(frameCount * 0.005), -1, 1, 0, TWO_PI);
  line(425, 270, 425 + cos(angle)*100, 270 + sin(angle)*100);
  line(425, 270, 425 + cos(angle + PI)*100, 27,0 + sin(angle + PI)*100);
  
  // Cell shapes
  fill(accent);
  ellipse(425, 270, 60, 60);
  ellipse(425 + cos(angle)*100, 270 + sin(angle)*100, 30, 30);
  ellipse(425 + cos(angle + PI)*100, 270 + sin(angle + PI)*100, 30, 30);
}

function drawStage1() {
  stroke(accent);
  strokeWeight(1.5);
  
  // DNA strands
  for (let i = 0; i < 8; i++) {
    let y = 270 + i * 20;
    bezier(100, y, 120, y - 10, 120, y + 10, 140, y);
    bezier(700, y, 680, y - 10, 680, y + 10, 660, y);
  }
  
  // Base pairs
  fill(accent);
  for (let i = 0; i < 6; i++) {
    let x = 200 + i * 80;
    let y = 270;
    ellipse(x, y, 8, 8);
    ellipse(x + 40, y, 8, 8);
    line(x, y, x + 40, y);
  }
}

function drawStage2() {
  stroke(accent);
  strokeWeight(2);
  
  // Differentiated cells
  for (let i = 0; i < 5; i++) {
    let x = 200 + i * 100;
    let y = 270;
    let r = 30 + sin(frameCount * 0.01 + i) * 5;
    ellipse(x, y, r, r);
    fill(text);
    textSize(12);
    text(['Neuron', 'Muscle', 'Skin', 'Blood', 'Nerve'][i], x - 10, y + 10);
  }
}

function drawStage3() {
  stroke(accent);
  strokeWeight(1.5);
  
  // Organ system connections
  for (let i = 0; i < 4; i++) {
    let x = 200 + i * 150;
    let y = 270;
    ellipse(x, y, 60, 60);
    bezier(200, 270, 220, 250, 220, 290, 240, 310);
  }
  
  // System labels
  fill(text);
  textSize(14);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][0], 180, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][1], 300, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][2], 420, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][3], 540, 250);
}

function drawStage4() {
  stroke(accent);
  strokeWeight(2);
  
  // Ecosystem growth
  for (let i = 0; i < 5; i++) {
    let x = 200 + i * 100;
    let y = 270;
    let size = 20 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, size, size);
    
    // Tree branches
    bezier(x, y, x + 20, y - 15, x + 40, y, x + 60, y + 15);
    bezier(x, y, x - 20, y - 15, x - 40, y, x - 60, y + 15);
  }
  
  // Ecosystem labels
  fill(text);
  textSize(12);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][0], 180, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][1], 300, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][2], 420, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][3], 540, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][4], 660, 250);
}

function setup() {
  createCanvas(850, 540);
  bezierOrder(2);
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
  const concepts = ["Stage 1: Cells divide through mitosis, creating identical daughter cells. This process is fundamental to growth and tissue repair.", "Stage 2: DNA replication ensures genetic continuity. Base pairs (A-T, C-G) form complementary strands during cell division.", "Stage 3: Stem cells differentiate into specialized cell types, forming tissues and organs through controlled gene expression.", "Stage 4: Organ systems (e.g., digestive, circulatory) function through coordinated interactions between specialized structures.", "Stage 5: Ecological development shows how ecosystems evolve through species interactions and environmental adaptations."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  stroke(accent);
  strokeWeight(2);
  
  // Animated cell division
  let angle = map(sin(frameCount * 0.005), -1, 1, 0, TWO_PI);
  line(425, 270, 425 + cos(angle)*100, 270 + sin(angle)*100);
  line(425, 270, 425 + cos(angle + PI)*100, 270 + sin(angle + PI)*100);
  
  // Cell shapes
  fill(accent);
  ellipse(425, 270, 60, 60);
  ellipse(425 + cos(angle)*100, 270 + sin(angle)*100, 30, 30);
  ellipse(425 + cos(angle + PI)*100, 270 + sin(angle + PI)*100, 30, 30);
}

function drawStage1() {
  stroke(accent);
  strokeWeight(1.5);
  
  // DNA strands
  for (let i = 0; i < 8; i++) {
    let y = 270 + i * 20;
    bezier(100, y, 120, y - 10, 120, y + 10, 140, y);
    bezier(700, y, 680, y - 10, 680, y + 10, 660, y);
  }
  
  // Base pairs
  fill(accent);
  for (let i = 0; i < 6; i++) {
    let x = 200 + i * 80;
    let y = 270;
    ellipse(x, y, 8, 8);
    ellipse(x + 40, y, 8, 8);
    line(x, y, x + 40, y);
  }
}

function drawStage2() {
  stroke(accent);
  strokeWeight(2);
  
  // Differentiated cells
  for (let i = 0; i < 5; i++) {
    let x = 200 + i * 100;
    let y = 270;
    let r = 30 + sin(frameCount * 0.01 + i) * 5;
    ellipse(x, y, r, r);
    fill(text);
    textSize(12);
    text(['Neuron', 'Muscle', 'Skin', 'Blood', 'Nerve'][i], x - 10, y + 10);
  }
}

function drawStage3() {
  stroke(accent);
  strokeWeight(1.5);
  
  // Organ system connections
  for (let i = 0; i < 4; i++) {
    let x = 200 + i * 150;
    let y = 270;
    ellipse(x, y, 60, 60);
    bezier(200, 270, 220, 250, 220, 290, 240, 310);
  }
  
  // System labels
  fill(text);
  textSize(14);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][0], 180, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][1], 300, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][2], 420, 250);
  text(['Heart', 'Lungs', 'Liver', 'Kidneys'][3], 540, 250);
}

function drawStage4() {
  stroke(accent);
  strokeWeight(2);
  
  // Ecosystem growth
  for (let i = 0; i < 5; i++) {
    let x = 200 + i * 100;
    let y = 270;
    let size = 20 + sin(frameCount * 0.01 + i) * 10;
    ellipse(x, y, size, size);
    
    // Tree branches
    bezier(x, y, x + 20, y - 15, x + 40, y, x + 60, y + 15);
    bezier(x, y, x - 20, y - 15, x - 40, y, x - 60, y + 15);
  }
  
  // Ecosystem labels
  fill(text);
  textSize(12);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][0], 180, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][1], 300, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][2], 420, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][3], 540, 250);
  text(['Tree', 'Bird', 'Fish', 'Mammal', 'Insect'][4], 660, 250);
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
