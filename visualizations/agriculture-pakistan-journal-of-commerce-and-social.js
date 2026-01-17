// Pakistan Journal of Commerce and Social Sciences
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Journal Foundation", "Stage 2: Agricultural Roots", "Stage 3: Water Flow", "Stage 4: Soil Dynamics", "Stage 5: Integrated System"];
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
  if (currentStage === 0) {
    drawStage0();
  } else if (currentStage === 1) {
    drawStage1();
  } else if (currentStage === 2) {
    drawStage2();
  } else if (currentStage === 3) {
    drawStage3();
  } else if (currentStage === 4) {
    drawStage4();
  }
}

function drawStage0() {
  // Micro-movement for title text
  fill(text);
  textSize(24);
  text('Pakistan Journal of Commerce & Social Sciences', 20, 50);
  
  // Animated soil texture
  noFill();
  stroke(accent, 50);
  beginShape();
  for (let x = 0; x < width; x += 30) {
    let y = height - 50 + sin(frameCount * 0.01 + x * 0.1) * 5;
    curveVertex(x, y);
  }
  endShape();
}

function drawStage1() {
  // Growing crops animation
  noStroke();
  fill(accent);
  for (let i = 0; i < 20; i++) {
    let x = 100 + i * 40;
    let y = height - 100 + sin(frameCount * 0.01 + x * 0.05) * 10;
    ellipse(x, y, 20, 40);
    
    // Micro-movement for crop leaves
    fill(text);
    noStroke();
    ellipse(x, y - 30, 10, 20);
  }
}

function drawStage2() {
  // Water flow animation
  noFill();
  stroke(accent, 100);
  beginShape();
  for (let x = 0; x < width; x += 20) {
    let y = height/2 + sin(frameCount * 0.02 + x * 0.1) * 5;
    splineVertex(x, y, x+10, y-10, x+20, y);
  }
  endShape();
}

function drawStage3() {
  // Soil particle movement
  noStroke();
  fill(accent, 50);
  for (let i = 0; i < 100; i++) {
    let x = random(0, width);
    let y = height - 50 + sin(frameCount * 0.01 + x * 0.05) * 3;
    ellipse(x, y, 4, 8);
  }
}

function drawStage4() {
  // Integrated system animation
  noStroke();
  fill(accent);
  for (let i = 0; i < 15; i++) {
    let x = 100 + i * 50;
    let y = height - 120 + sin(frameCount * 0.01 + x * 0.05) * 8;
    ellipse(x, y, 15, 30);
    
    // Animated water droplets
    fill(text);
    noStroke();
    ellipse(x, y - 20, 5, 10);
  }
  
  // Animated journal logo
  fill(text);
  textSize(20);
  text('PJ-CSS', 650, 40);
  text('Agriculture Edition', 650, 60);
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
  text("Pakistan Journal of Commerce and Social ", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Agriculture | General", width / 2, 48);
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
  const concepts = ["Introducing the Pakistan Journal of Commerce and Social Sciences with agricultural focus", "Exploring foundational agricultural elements like crops and soil", "Visualizing water movement as a critical agricultural resource", "Demonstrating soil particle interactions and nutrient flow", "Showcasing integrated systems of agriculture, commerce, and social science"];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Micro-movement for title text
  fill(text);
  textSize(24);
  text('Pakistan Journal of Commerce & Social Sciences', 20, 50);
  
  // Animated soil texture
  noFill();
  stroke(accent, 50);
  beginShape();
  for (let x = 0; x < width; x += 30) {
    let y = height - 50 + sin(frameCount * 0.01 + x * 0.1) * 5;
    curveVertex(x, y);
  }
  endShape();
}

function drawStage1() {
  // Growing crops animation
  noStroke();
  fill(accent);
  for (let i = 0; i < 20; i++) {
    let x = 100 + i * 40;
    let y = height - 100 + sin(frameCount * 0.01 + x * 0.05) * 10;
    ellipse(x, y, 20, 40);
    
    // Micro-movement for crop leaves
    fill(text);
    noStroke();
    ellipse(x, y - 30, 10, 20);
  }
}

function drawStage2() {
  // Water flow animation
  noFill();
  stroke(accent, 100);
  beginShape();
  for (let x = 0; x < width; x += 20) {
    let y = height/2 + sin(frameCount * 0.02 + x * 0.1) * 5;
    splineVertex(x, y, x+10, y-10, x+20, y);
  }
  endShape();
}

function drawStage3() {
  // Soil particle movement
  noStroke();
  fill(accent, 50);
  for (let i = 0; i < 100; i++) {
    let x = random(0, width);
    let y = height - 50 + sin(frameCount * 0.01 + x * 0.05) * 3;
    ellipse(x, y, 4, 8);
  }
}

function drawStage4() {
  // Integrated system animation
  noStroke();
  fill(accent);
  for (let i = 0; i < 15; i++) {
    let x = 100 + i * 50;
    let y = height - 120 + sin(frameCount * 0.01 + x * 0.05) * 8;
    ellipse(x, y, 15, 30);
    
    // Animated water droplets
    fill(text);
    noStroke();
    ellipse(x, y - 20, 5, 10);
  }
  
  // Animated journal logo
  fill(text);
  textSize(20);
  text('PJ-CSS', 650, 40);
  text('Agriculture Edition', 650, 60);
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
