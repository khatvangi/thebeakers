// DeepSeek-R1 incentivizes reasoning in LLMs through reinforce
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Reasoning Challenge", "Stage 2: LLM Breakthroughs", "Stage 3: Annotation Limitations", "Stage 4: DeepSeek-R1 Design", "Stage 5: Reinforcement Loop"];
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
  text("Engineering | Experiment", width / 2, 48);
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
  const concepts = ["General reasoning remains a critical challenge in AI. Traditional models struggle with complex problem-solving without human guidance.", "LLMs and CoT prompting have shown promise, but their success depends on massive annotated data and still lack robust reasoning capabilities.", "Human annotations are costly and limited, constraining model development for complex tasks. This creates a bottleneck in AI advancement.", "DeepSeek-R1 introduces a reinforcement framework that incentivizes reasoning through dynamic feedback loops and model self-improvement.", "The system combines reward signals with iterative refinement, enabling models to develop reasoning skills autonomously through continuous optimization."];
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
  for (let i=0; i<20; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let angle = map(sin(frameCount * 0.01 + x/10), -1, 1, 0, TWO_PI);
    line(x, y, x + cos(angle)*10, y + sin(angle)*10);
  }
  fill(text);
  textSize(14);
  text('General reasoning remains a critical challenge in AI. Traditional models struggle with complex problem-solving without human guidance.', 20, 30);
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i=0; i<30; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let angle = map(sin(frameCount * 0.01 + x/10), -1, 1, 0, TWO_PI);
    line(x, y, x + cos(angle)*10, y + sin(angle)*10);
  }
  fill(text);
  textSize(14);
  text('LLMs and CoT prompting have shown promise, but their success depends on massive annotated data and still lack robust reasoning capabilities.', 20, 30);
}

function drawStage2() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i=0; i<40; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let angle = map(sin(frameCount * 0.01 + x/10), -1, 1, 0, TWO_PI);
    line(x, y, x + cos(angle)*10, y + sin(angle)*10);
  }
  fill(text);
  textSize(14);
  text('Human annotations are costly and limited, constraining model development for complex tasks. This creates a bottleneck in AI advancement.', 20, 30);
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i=0; i<50; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let angle = map(sin(frameCount * 0.01 + x/10), -1, 1, 0, TWO_PI);
    line(x, y, x + cos(angle)*10, y + sin(angle)*10);
  }
  fill(text);
  textSize(14);
  text('DeepSeek-R1 introduces a reinforcement framework that incentivizes reasoning through dynamic feedback loops and model self-improvement.', 20, 30);
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i=0; i<60; i++) {
    let x = random(100, 750);
    let y = random(100, 440);
    let angle = map(sin(frameCount * 0.01 + x/10), -1, 1, 0, TWO_PI);
    line(x, y, x + cos(angle)*10, y + sin(angle)*10);
  }
  fill(text);
  textSize(14);
  text('The system combines reward signals with iterative refinement, enabling models to develop reasoning skills autonomously through continuous optimization.', 20, 30);
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
