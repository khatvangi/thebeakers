// Development Education
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Foundation of Sponsorship", "Stage 2: Cultivation of Knowledge", "Stage 3: Community Engagement", "Stage 4: Sustainable Practices", "Stage 5: Future Generations"];
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
  background(#0f172a);
  if (currentStage === 0) { drawStage0(); } 
  else if (currentStage === 1) { drawStage1(); }
  else if (currentStage === 2) { drawStage2(); }
  else if (currentStage === 3) { drawStage3(); }
  else if (currentStage === 4) { drawStage4(); }
}

function keyPressed() {
  currentStage = (currentStage + 1) % num_stages;
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
  const concepts = ["Sponsorship establishes the foundation for agricultural education, creating opportunities for knowledge transfer.", "Knowledge is cultivated through structured learning, connecting theory with practical farming techniques.", "Community involvement ensures education reaches all stakeholders, fostering collaborative development.", "Sustainable practices integrate ecological awareness, ensuring long-term agricultural viability.", "Future generations inherit both challenges and opportunities, requiring adaptive educational strategies."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  noStroke();
  fill(#10b981);
  ellipse(100 + sin(frameCount * 0.005) * 10, 100 + sin(frameCount * 0.005) * 10, 20, 20);
  fill(#e2e8f0);
  text('Seedling', 80, 110);
  
  stroke(#10b981);
  strokeWeight(2);
  bezier(120, 120, 130, 80, 150, 100, 160, 120);
}

function drawStage1() {
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 10; i++) {
    let x = 200 + i * 30 + sin(frameCount * 0.005 + i * 0.1) * 5;
    let y = 150 + sin(frameCount * 0.005 + i * 0.2) * 5;
    ellipse(x, y, 12, 12);
  }
  
  fill(#e2e8f0);
  text('Knowledge Growth', 180, 180);
  
  stroke(#10b981);
  strokeWeight(2);
  bezier(220, 160, 230, 120, 250, 140, 260, 160);
}

function drawStage2() {
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 8; i++) {
    let x = 350 + i * 40 + sin(frameCount * 0.005 + i * 0.1) * 5;
    let y = 200 + sin(frameCount * 0.005 + i * 0.2) * 5;
    ellipse(x, y, 16, 16);
  }
  
  fill(#e2e8f0);
  text('Community Roots', 330, 230);
  
  stroke(#10b981);
  strokeWeight(2);
  bezier(370, 200, 380, 160, 400, 180, 410, 200);
}

function drawStage3() {
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 12; i++) {
    let x = 500 + i * 25 + sin(frameCount * 0.005 + i * 0.1) * 5;
    let y = 250 + sin(frameCount * 0.005 + i * 0.2) * 5;
    ellipse(x, y, 10, 10);
  }
  
  fill(#e2e8f0);
  text('Sustainable Practices', 480, 280);
  
  stroke(#10b981);
  strokeWeight(2);
  bezier(520, 250, 530, 210, 550, 230, 560, 250);
}

function drawStage4() {
  noStroke();
  fill(#10b981);
  for (let i = 0; i < 15; i++) {
    let x = 650 + i * 20 + sin(frameCount * 0.005 + i * 0.1) * 5;
    let y = 300 + sin(frameCount * 0.005 + i * 0.2) * 5;
    ellipse(x, y, 8, 8);
  }
  
  fill(#e2e8f0);
  text('Future Harvest', 630, 330);
  
  stroke(#10b981);
  strokeWeight(2);
  bezier(670, 300, 680, 260, 700, 280, 710, 300);
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
