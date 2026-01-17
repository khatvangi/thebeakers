// DeepSeek-R1 incentivizes reasoning in LLMs through reinforce
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Neural Foundations", "Stage 2: Chain-of-Thought", "Stage 3: Data Limitations", "Stage 4: Reinforcement Loop", "Stage 5: DeepSeek-R1"];
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
  text("Biology | Experiment", width / 2, 48);
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
  const concepts = ["Artificial intelligence struggles with general reasoning. Biological systems like neural networks show complex decision-making patterns.", "Large language models (LLMs) use chain-of-thought prompting to simulate step-by-step reasoning, mimicking human problem-solving processes.", "Human-annotated data is insufficient for complex tasks. Models often fail to generalize beyond training examples.", "Reinforcement learning incentivizes reasoning through reward signals, creating a feedback loop for iterative improvement.", "DeepSeek-R1 advances reasoning capabilities by integrating reinforcement learning, enabling models to tackle complex biological problems."];
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
  noStroke();
  fill(accent);
  const angle = sin(frameCount * 0.005) * 10;
  const radius = 100 + sin(frameCount * 0.01) * 10;
  ellipse(width/2, height/2, radius*2, radius*2);
  
  fill(text);
  textSize(16);
  text('Neural networks mimic biological decision-making', 50, 50);
  text('with complex, dynamic patterns', 50, 70);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  const x = 100 + sin(frameCount * 0.005) * 10;
  const y = 100 + sin(frameCount * 0.005) * 10;
  ellipse(x, y, 40, 40);
  
  const x2 = 400 + sin(frameCount * 0.005) * 10;
  const y2 = 200 + sin(frameCount * 0.005) * 10;
  ellipse(x2, y2, 40, 40);
  
  strokeWeight(1);
  line(x, y, x2, y2);
  
  fill(text);
  textSize(16);
  text('Chain-of-thought prompting simulates', 50, 50);
  text('step-by-step reasoning processes', 50, 70);
}

function drawStage2() {
  background(bg);
  noStroke();
  fill(accent);
  
  for (let i = 0; i < 20; i++) {
    const x = random(50, 750);
    const y = random(50, 450);
    const size = 10 + sin(frameCount * 0.005 + i) * 5;
    ellipse(x, y, size, size);
  }
  
  fill(text);
  textSize(16);
  text('Human-annotated data is insufficient', 50, 50);
  text('for complex biological problems', 50, 70);
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  const centerX = width/2;
  const centerY = height/2;
  
  for (let i = 0; i < 10; i++) {
    const angle = i * 36 - frameCount * 0.1;
    const radius = 50 + sin(frameCount * 0.005 + i) * 10;
    const x = centerX + cos(angle * PI/180) * radius;
    const y = centerY + sin(angle * PI/180) * radius;
    point(x, y);
  }
  
  fill(text);
  textSize(16);
  text('Reinforcement learning creates', 50, 50);
  text('iterative improvement cycles', 50, 70);
}

function drawStage4() {
  background(bg);
  noStroke();
  fill(accent);
  
  const centerX = width/2;
  const centerY = height/2;
  
  for (let i = 0; i < 15; i++) {
    const angle = i * 24 - frameCount * 0.1;
    const radius = 30 + sin(frameCount * 0.005 + i) * 5;
    const x = centerX + cos(angle * PI/180) * radius;
    const y = centerY + sin(angle * PI/180) * radius;
    ellipse(x, y, 5, 5);
  }
  
  fill(text);
  textSize(16);
  text('DeepSeek-R1 integrates', 50, 50);
  text('reinforcement for complex tasks', 50, 70);
}

function drawStage5() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  
  bezierOrder(2);
  
  const centerX = width/2;
  const centerY = height/2;
  
  for (let i = 0; i < 10; i++) {
    const angle = i * 36 - frameCount * 0.1;
    const radius = 80 + sin(frameCount * 0.005 + i) * 10;
    const x = centerX + cos(angle * PI/180) * radius;
    const y = centerY + sin(angle * PI/180) * radius;
    
    splineVertex(x, y);
    
    const endX = x + cos(angle * PI/180) * 10;
    const endY = y + sin(angle * PI/180) * 10;
    
    splineVertex(endX, endY);
  }
  
  fill(accent);
  noStroke();
  ellipse(centerX, centerY, 60, 60);
  
  fill(text);
  textSize(16);
  text('DeepSeek-R1 enables biological', 50, 50);
  text('reasoning through reinforcement', 50, 70);
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
