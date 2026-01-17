// DeepSeek-R1 incentivizes reasoning in LLMs through reinforce
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["The Reasoning Challenge", "LLMs and Chain-of-Thought Prompting", "Limitations of Human Demonstrations", "DeepSeek-R1 Reinforcement Framework", "Reasoning Success through Reinforcement"];
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
  text("Mathematics | Experiment", width / 2, 48);
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
  const concepts = ["General reasoning remains a core challenge in AI. Traditional models struggle with complex mathematical problems requiring sequential logical steps.", "Large language models (LLMs) and chain-of-thought (CoT) prompting have shown promise, but rely on human-annotated examples for training.", "Human demonstrations are labor-intensive and limited in scope, constraining model capabilities for complex mathematical reasoning.", "DeepSeek-R1 introduces reinforcement learning to incentivize reasoning, creating a self-improving system through reward-based training.", "This approach enables models to develop robust reasoning abilities without human intervention, achieving success on complex mathematical tasks."];
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
  stroke(text);
  strokeWeight(2);
  
  // Pulsing central node
  let radius = 40 + 15 * sin(frameCount * 0.01);
  ellipse(width/2, height/2, radius*2, radius*2);
  
  // Radiating lines
  for (let i=0; i<360; i+=45) {
    let ang = radians(i);
    let x = width/2 + 100 * cos(ang);
    let y = height/2 + 100 * sin(ang);
    line(width/2, height/2, x, y);
    stroke(accent);
    line(width/2, height/2, x, y);
    stroke(text);
  }
}

function drawStage1() {
  background(bg);
  noFill();
  stroke(text);
  strokeWeight(2);
  
  // Chain-of-thought visualization
  let spacing = 120;
  let y = height/2;
  for (let i=0; i<5; i++) {
    let x = 100 + i*spacing;
    let size = 20 + 10 * sin(frameCount * 0.01 + i);
    ellipse(x, y, size, size);
    
    // Connecting lines
    stroke(accent);
    line(x, y, x + spacing, y);
    stroke(text);
    line(x, y, x + spacing, y);
  }
}

function drawStage2() {
  background(bg);
  noFill();
  stroke(text);
  strokeWeight(2);
  
  // Broken chain visualization
  let spacing = 120;
  let y = height/2;
  for (let i=0; i<5; i++) {
    let x = 100 + i*spacing;
    let size = 20 + 10 * sin(frameCount * 0.01 + i);
    ellipse(x, y, size, size);
    
    // Connecting lines with fading
    let opacity = 100 * (1 - abs(sin(frameCount * 0.01 + i * 2)));
    stroke(accent, opacity);
    line(x, y, x + spacing, y);
    stroke(text, opacity);
    line(x, y, x + spacing, y);
  }
}

function drawStage3() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(3);
  
  // Reinforcement loop visualization
  let centerX = width/2;
  let centerY = height/2;
  let radius = 100;
  
  // Outer circle
  beginShape();
  for (let i=0; i<360; i+=10) {
    let ang = radians(i);
    let x = centerX + radius * cos(ang);
    let y = centerY + radius * sin(ang);
    curveVertex(x, y);
  }
  endShape();
  
  // Inner circle
  beginShape();
  for (let i=0; i<360; i+=10) {
    let ang = radians(i);
    let x = centerX + (radius - 40) * cos(ang);
    let y = centerY + (radius - 40) * sin(ang);
    curveVertex(x, y);
  }
  endShape();
  
  // Arrows for reinforcement
  for (let i=0; i<4; i++) {
    let ang = radians(90 - i*90);
    let x = centerX + 120 * cos(ang);
    let y = centerY + 120 * sin(ang);
    
    // Arrowhead
    push();
    translate(x, y);
    rotate(ang);
    stroke(text);
    line(0, 0, 20, 0);
    stroke(accent);
    line(0, 0, 18, -5);
    line(0, 0, 18, 5);
    pop();
  }
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(text);
  strokeWeight(2);
  
  // Successful reasoning chain
  let spacing = 120;
  let y = height/2;
  for (let i=0; i<5; i++) {
    let x = 100 + i*spacing;
    let size = 20 + 10 * sin(frameCount * 0.01 + i);
    ellipse(x, y, size, size);
    
    // Connecting lines
    stroke(accent);
    line(x, y, x + spacing, y);
    stroke(text);
    line(x, y, x + spacing, y);
  }
  
  // Glowing effect
  noStroke();
  fill(accent, 150);
  ellipse(width/2, height/2, 80 + 20 * sin(frameCount * 0.01), 80 + 20 * sin(frameCount * 0.01));
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
