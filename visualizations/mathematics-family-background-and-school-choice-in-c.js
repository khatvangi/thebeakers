// Family Background and School Choice in Cities of Russia and 
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Countries & Systems", "Stage 2: Family Background Effects", "Stage 3: Urban vs Rural", "Stage 4: Policy Moderation", "Stage 5: Integrated Analysis"];
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
  const concepts = ["Introduce Russia and Estonia with their post-Soviet educational systems, highlighting shared communist-era institutions and divergent welfare states.", "Visualize family background effects using mathematical models showing how socioeconomic factors influence school outcomes.", "Compare urban-rural disparities with dynamic graphs illustrating access to resources and opportunities.", "Demonstrate how school admission policies moderate family effects through interactive policy representation.", "Combine all elements to show complex interactions between family background, policies, and educational outcomes."];
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
  strokeWeight(2);
  
  // Rotating country icons
  push();
  translate(200, 270);
  rotate(sin(frameCount * 0.005) * PI);
  ellipse(0, 0, 60, 60);
  pop();

  push();
  translate(600, 270);
  rotate(cos(frameCount * 0.005) * PI);
  ellipse(0, 0, 60, 60);
  pop();

  // Animated text
  fill(text);
  noStroke();
  textAlign(CENTER, CENTER);
  text('Russia & Estonia', 425, 270);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Data point animation
  for (let i = 0; i < 10; i++) {
    let x = random(100, 750);
    let y = random(50, 500);
    let size = 8 + sin(frameCount * 0.01 + i) * 4;
    ellipse(x, y, size, size);
  }

  // Mathematical equation
  fill(text);
  noStroke();
  textAlign(LEFT, TOP);
  text('Family Background = α + β₁Socio + β₂Policy', 20, 20);
}

function drawStage2() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Urban-rural bar chart animation
  for (let i = 0; i < 4; i++) {
    let x = 100 + i * 200;
    let height = 200 + sin(frameCount * 0.01 + i) * 20;
    rect(x, 300, 50, height);
    fill(text);
    noStroke();
    textAlign(CENTER, TOP);
    text('Urban', x + 25, 25);
    text('Rural', x + 25, 450);
  }

  // Animated line graph
  beginShape();
  for (let i = 0; i < 10; i++) {
    let x = 100 + i * 40;
    let y = 200 + sin(frameCount * 0.01 + i) * 50;
    bezierVertex(x, y, x + 20, y - 30, x + 40, y);
  }
  endShape();
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Policy influence visualization
  for (let i = 0; i < 6; i++) {
    let x = 100 + i * 100;
    let y = 300 + sin(frameCount * 0.01 + i) * 15;
    let radius = 20 + cos(frameCount * 0.005 + i) * 5;
    ellipse(x, y, radius, radius);
    fill(text);
    noStroke();
    textAlign(CENTER, CENTER);
    text('Policy', x, y);
  }

  // Animated interaction effect
  for (let i = 0; i < 5; i++) {
    let x = 200 + i * 150;
    let y = 400 + sin(frameCount * 0.01 + i) * 10;
    let size = 12 + cos(frameCount * 0.005 + i) * 4;
    ellipse(x, y, size, size);
  }
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  // Integrated system visualization
  for (let i = 0; i < 8; i++) {
    let x = 100 + i * 100;
    let y = 200 + sin(frameCount * 0.01 + i) * 10;
    let size = 16 + cos(frameCount * 0.005 + i) * 4;
    ellipse(x, y, size, size);
  }

  // Final mathematical model
  fill(text);
  noStroke();
  textAlign(LEFT, TOP);
  text('Integrated Model: Outcomes = f(Family, Policy, Context)', 20, 20);
  text('with interaction terms', 20, 40);
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
