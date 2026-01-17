// Report on Alternative Devices to Pyrotechnics on Spacecraft
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Pyrotechnics in Spacecraft", "Stage 2: Limitations of Pyrotechnics", "Stage 3: Emerging Alternatives", "Stage 4: Safety & Cost Analysis", "Stage 5: Future of Space Systems"];
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

if (currentStage === 0) { drawStage0(); } 
else if (currentStage === 1) { drawStage1(); } 
else if (currentStage === 2) { drawStage2(); } 
else if (currentStage === 3) { drawStage3(); } 
else { drawStage4(); }
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
  text("Report on Alternative Devices to Pyrotec", width / 2, 20);

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
  const concepts = ["Pyrotechnics provide reliable, compact solutions for spacecraft operations. They enable rapid, high-energy actions with minimal power requirements.", "However, pyrotechnics introduce risks: mechanical shock, potential failure, and high development costs. Their use is being re-evaluated for modern missions.", "Alternatives like electric actuators, shape-memory alloys, and laser systems offer safer, more predictable operation with comparable performance.", "Comparative analysis shows alternatives reduce risk profiles and long-term costs, though initial implementation challenges persist.", "NASA is prioritizing research into hybrid systems that combine reliability with innovation to ensure mission safety and efficiency."];
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
  fill(#e2e8f0);
  noStroke();
  textAlign(CENTER, CENTER);
  text('Pyrotechnics in Spacecraft', width/2, 100);
  
  // Rotating gear animation
  push();
  translate(width/2, height/2);
  rotate(sin(frameCount * 0.005));
  fill(#10b981);
  ellipse(0, 0, 100, 100);
  fill(#e2e8f0);
  text('Reliable, Compact', 0, -60);
  pop();
}

function drawStage1() {
  background(#0f172a);
  fill(#10b981);
  noStroke();
  textAlign(LEFT, TOP);
  text('Limitations of Pyrotechnics', 20, 30);
  
  // Pulsing bar graph
  for (let i = 0; i < 5; i++) {
    let y = 100 + i * 60;
    let value = sin(frameCount * 0.01 + i) * 20 + 50;
    rect(20, y, value, 20);
    fill(#e2e8f0);
    text(['Shock Risk', 'Failure Risk', 'Cost', 'Safety', 'Reliability'][i], 30, y + 10);
  }
}

function drawStage2() {
  background(#0f172a);
  fill(#10b981);
  noStroke();
  textAlign(CENTER, CENTER);
  text('Emerging Alternatives', width/2, 100);
  
  // Animated tech icons
  push();
  translate(width/2, height/2);
  for (let i = 0; i < 3; i++) {
    let angle = TWO_PI * i / 3;
    let x = cos(angle) * 150;
    let y = sin(angle) * 150;
    fill(#e2e8f0);
    text(['\u{1F525}', '\u{1F5A5}', '\u{1F526}'][i], x + width/2, y + height/2);
    ellipse(x + width/2, y + height/2, 40 + sin(frameCount * 0.01 + i) * 10, 40 + sin(frameCount * 0.01 + i) * 10);
  }
  pop();
}

function drawStage3() {
  background(#0f172a);
  fill(#10b981);
  noStroke();
  textAlign(CENTER, CENTER);
  text('Safety & Cost Analysis', width/2, 100);
  
  // Split-screen comparison
  push();
  translate(0, 200);
  fill(#e2e8f0);
  text('Pyrotechnics', 20, 30);
  rect(20, 60, 100, 200);
  for (let i = 0; i < 5; i++) {
    let y = 80 + i * 40;
    let value = sin(frameCount * 0.01 + i) * 15 + 50;
    fill(#10b981);
    rect(20, y, value, 20);
    text(['Shock', 'Failure', 'Cost', 'Safety', 'Reliability'][i], 30, y + 10);
  }
  
  translate(width - 200, 200);
  fill(#e2e8f0);
  text('Alternatives', 20, 30);
  rect(20, 60, 100, 200);
  for (let i = 0; i < 5; i++) {
    let y = 80 + i * 40;
    let value = sin(frameCount * 0.01 + i + 3) * 15 + 80;
    fill(#10b981);
    rect(20, y, value, 20);
    text(['Shock', 'Failure', 'Cost', 'Safety', 'Reliability'][i], 30, y + 10);
  }
  pop();
}

function drawStage4() {
  background(#0f172a);
  fill(#10b981);
  noStroke();
  textAlign(CENTER, CENTER);
  text('Future of Space Systems', width/2, 100);
  
  // Rising graph visualization
  push();
  translate(0, height - 200);
  fill(#e2e8f0);
  text('Research Priorities', width/2, 30);
  
  let x = 100;
  let y = height - 150;
  let angle = frameCount * 0.005;
  fill(#10b981);
  ellipse(x, y, 60, 60);
  
  // Animated data points
  for (let i = 0; i < 4; i++) {
    let angle = TWO_PI * i / 4 + frameCount * 0.01;
    let radius = 80 + sin(frameCount * 0.02 + i) * 10;
    let dx = cos(angle) * radius;
    let dy = sin(angle) * radius;
    fill(#e2e8f0);
    text(['\u{1F4E6}', '\u{1F525}', '\u{1F4E7}', '\u{1F5A5}'][i], x + dx, y + dy);
  }
  pop();
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
