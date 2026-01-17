// DeepSeek-R1 incentivizes reasoning in LLMs through reinforce
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Reasoning Foundations", "Stage 2: Force Dynamics", "Stage 3: Chain-of-Thought", "Stage 4: Reinforcement Loop", "Stage 5: Convergent Insight"];
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
  text("Physics | Experiment", width / 2, 48);
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
  const concepts = ["Reasoning requires structured problem-solving. Particles represent basic cognitive units moving through potential energy fields.", "Forces guide reasoning paths. Green vectors show reinforcement signals that shape particle trajectories.", "Connected particles form thought chains. Their motion demonstrates sequential reasoning through physical interactions.", "Energy bars visualize reward signals. Higher energy indicates successful reasoning steps in the learning process.", "Convergent patterns emerge as particles stabilize. This represents optimized reasoning through reinforcement learning."];
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
  fill(#10b981);
  for (let i = 0; i < 20; i++) {
    let x = 400 + 200 * sin(frameCount * 0.01 + i * 0.1);
    let y = 270 + 150 * cos(frameCount * 0.01 + i * 0.1);
    ellipse(x, y, 10, 10);
  }
}

function drawStage1() {
  background(#0f172a);
  stroke(#10b981);
  strokeWeight(2);
  noFill();
  for (let i = 0; i < 15; i++) {
    let x = 400 + 180 * sin(frameCount * 0.01 + i * 0.2);
    let y = 270 + 120 * cos(frameCount * 0.01 + i * 0.2);
    bezier(x, y, x+30, y-20, x+60, y+10, x+90, y);
  }
}

function drawStage2() {
  background(#0f172a);
  stroke(#10b981);
  strokeWeight(1.5);
  noFill();
  for (let i = 0; i < 12; i++) {
    let x = 400 + 150 * sin(frameCount * 0.01 + i * 0.25);
    let y = 270 + 100 * cos(frameCount * 0.01 + i * 0.25);
    bezier(x, y, x+40, y-30, x+80, y+20, x+120, y);
  }
}

function drawStage3() {
  background(#0f172a);
  stroke(#10b981);
  strokeWeight(2);
  noFill();
  for (let i = 0; i < 10; i++) {
    let x = 400 + 120 * sin(frameCount * 0.01 + i * 0.3);
    let y = 270 + 80 * cos(frameCount * 0.01 + i * 0.3);
    bezier(x, y, x+50, y-40, x+100, y+30, x+150, y);
  }
  fill(#e2e8f0);
  rect(50, 20, 10, 10);
  rect(150, 20, 10, 10);
  rect(250, 20, 10, 10);
}

function drawStage4() {
  background(#0f172a);
  stroke(#10b981);
  strokeWeight(2);
  noFill();
  for (let i = 0; i < 8; i++) {
    let x = 400 + 90 * sin(frameCount * 0.01 + i * 0.35);
    let y = 270 + 60 * cos(frameCount * 0.01 + i * 0.35);
    bezier(x, y, x+60, y-50, x+120, y+40, x+180, y);
  }
  fill(#e2e8f0);
  rect(50, 20, 10, 10);
  rect(150, 20, 10, 10);
  rect(250, 20, 10, 10);
  rect(350, 20, 10, 10);
  rect(450, 20, 10, 10);
  fill(#10b981);
  rect(50, 50, 10, 10);
  rect(150, 50, 10, 10);
  rect(250, 50, 10, 10);
  rect(350, 50, 10, 10);
  rect(450, 50, 10, 10);
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
