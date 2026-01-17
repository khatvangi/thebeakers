// DeepSeek-R1 incentivizes reasoning in LLMs through reinforce
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Reasoning Challenge", "Stage 2: LLM Foundations", "Stage 3: Human Limitations", "Stage 4: Reinforcement Breakthrough", "Stage 5: Chemistry Impact"];
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
  text("DeepSeek-R1 incentivizes reasoning in LL", width / 2, 20);

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
  const concepts = ["AI struggles with complex reasoning tasks requiring deep understanding of chemical systems and molecular interactions.", "Large language models (LLMs) and chain-of-thought prompting show promise but face limitations in complex chemical reasoning.", "Human-annotated demonstrations are insufficient for teaching LLMs to handle intricate chemical reasoning tasks.", "DeepSeek-R1 uses reinforcement learning to train models through iterative feedback, enabling better reasoning in chemistry.", "This approach improves performance on complex chemical problems like reaction prediction and molecular synthesis."];
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
  text('AI struggles with complex reasoning tasks requiring deep understanding of chemical systems and molecular interactions.', 20, 30);
  
  // Moving atoms
  for (let i = 0; i < 10; i++) {
    let x = 100 + i * 50 + sin(frameCount * 0.01 + i) * 5;
    let y = 200 + sin(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 10, 10);
  }
}

function drawStage1() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textSize(14);
  text('Large language models (LLMs) and chain-of-thought prompting show promise but face limitations in complex chemical reasoning.', 20, 30);
  
  // Neural network nodes
  stroke(#10b981);
  strokeWeight(2);
  for (let i = 0; i < 8; i++) {
    let x = 300 + sin(frameCount * 0.01 + i) * 5;
    let y = 200 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 12, 12);
  }
  
  // Flowing particles
  fill(#10b981);
  for (let i = 0; i < 12; i++) {
    let x = 300 + sin(frameCount * 0.01 + i) * 5;
    let y = 200 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 4, 4);
  }
}

function drawStage2() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textSize(14);
  text('Human-annotated demonstrations are insufficient for teaching LLMs to handle intricate chemical reasoning tasks.', 20, 30);
  
  // Wall representation
  fill(#10b981);
  rect(400, 250, 200, 20);
  
  // Particles approaching wall
  fill(#e2e8f0);
  for (let i = 0; i < 15; i++) {
    let x = 300 + sin(frameCount * 0.01 + i) * 5;
    let y = 200 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 6, 6);
  }
  
  // Bouncing back particles
  fill(#10b981);
  for (let i = 0; i < 10; i++) {
    let x = 500 + sin(frameCount * 0.01 + i) * 5;
    let y = 250 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 4, 4);
  }
}

function drawStage3() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textSize(14);
  text('DeepSeek-R1 uses reinforcement learning to train models through iterative feedback, enabling better reasoning in chemistry.', 20, 30);
  
  // Reward target
  fill(#10b981);
  ellipse(600, 300, 16, 16);
  
  // Orbiting particles
  fill(#e2e8f0);
  for (let i = 0; i < 12; i++) {
    let angle = frameCount * 0.01 + i;
    let x = 550 + sin(angle) * 20;
    let y = 300 + cos(angle) * 20;
    ellipse(x, y, 6, 6);
  }
  
  // Feedback arrows
  stroke(#10b981);
  strokeWeight(1);
  for (let i = 0; i < 8; i++) {
    let x = 550 + sin(frameCount * 0.01 + i) * 10;
    let y = 300 + cos(frameCount * 0.01 + i * 2) * 10;
    line(x, y, x + 15, y);
  }
}

function drawStage4() {
  background(#0f172a);
  noStroke();
  fill(#e2e8f0);
  textSize(14);
  text('This approach improves performance on complex chemical problems like reaction prediction and molecular synthesis.', 20, 30);
  
  // Molecule formation
  fill(#10b981);
  ellipse(200, 400, 12, 12);
  ellipse(300, 400, 12, 12);
  ellipse(400, 400, 12, 12);
  
  // Bonds
  stroke(#10b981);
  strokeWeight(2);
  line(200, 400, 300, 400);
  line(300, 400, 400, 400);
  
  // Reaction arrow
  stroke(#10b981);
  strokeWeight(2);
  line(400, 400, 500, 450);
  
  // Product molecule
  fill(#10b981);
  ellipse(550, 450, 12, 12);
  ellipse(650, 450, 12, 12);
  ellipse(750, 450, 12, 12);
  
  // Moving reaction elements
  fill(#e2e8f0);
  for (let i = 0; i < 6; i++) {
    let x = 200 + sin(frameCount * 0.01 + i) * 5;
    let y = 400 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 6, 6);
  }
  
  // Product movement
  fill(#e2e8f0);
  for (let i = 0; i < 6; i++) {
    let x = 550 + sin(frameCount * 0.01 + i) * 5;
    let y = 450 + cos(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, 6, 6);
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
