// Topological Weyl altermagnetism in CrSb
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Crystal Lattice", "Stage 2: Spin-Splitting Bands", "Stage 3: Magnetic Order", "Stage 4: Topological Surface States", "Stage 5: Weyl Cones"];
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
  if (currentStage === 0) { drawStage0(); } 
  else if (currentStage === 1) { drawStage1(); }
  else if (currentStage === 2) { drawStage2(); }
  else if (currentStage === 3) { drawStage3(); }
  else if (currentStage === 4) { drawStage4(); }
}

function drawStage0() {
  // Crystal lattice
  noFill();
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < width; x += 40) {
    for (let y = 0; y < height; y += 40) {
      ellipse(x + 20*sin(frameCount*0.01), y + 20*cos(frameCount*0.01), 10, 10);
      ellipse(x + 30*sin(frameCount*0.01), y + 30*cos(frameCount*0.01), 10, 10);
    }
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('CrSb Crystal Lattice', width/2, 30);
}

function drawStage1() {
  // Spin-splitting bands
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let y = 0; y < height; y += 30) {
    bezier(
      50, y, 50, y, 
      100 + 20*sin(frameCount*0.01), y + 10*cos(frameCount*0.01), 
      200, y + 20*sin(frameCount*0.01)
    );
    bezier(
      50, y + 20, 50, y + 20, 
      100 + 20*cos(frameCount*0.01), y + 10*sin(frameCount*0.01), 
      200, y + 20*cos(frameCount*0.01)
    );
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Spin-Splitting Bands', width/2, 30);
}

function drawStage2() {
  // Magnetic order
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let x = 0; x < width; x += 40) {
    for (let y = 0; y < height; y += 40) {
      line(x + 10, y + 10, x + 10 + 15*cos(frameCount*0.01), y + 10 + 15*sin(frameCount*0.01));
      line(x + 30, y + 30, x + 30 + 15*cos(frameCount*0.01), y + 30 + 15*sin(frameCount*0.01));
    }
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Magnetic Order', width/2, 30);
}

function drawStage3() {
  // Topological surface states
  noFill();
  stroke(accent);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < 100; i++) {
    let angle = map(sin(frameCount*0.01 + i), -1, 1, 0, TWO_PI);
    let r = 50 + 20*sin(i*0.1 + frameCount*0.005);
    vertex(r*cos(angle), r*sin(angle));
  }
  endShape();
  fill(text);
  textAlign(CENTER, CENTER);
  text('Topological Surface States', width/2, 30);
}

function drawStage4() {
  // Weyl cones
  noFill();
  stroke(accent);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < 100; i++) {
    let angle = map(cos(frameCount*0.01 + i), -1, 1, 0, TWO_PI);
    let r = 50 + 10*sin(i*0.1 + frameCount*0.005);
    vertex(r*cos(angle), r*sin(angle));
  }
  endShape();
  fill(text);
  textAlign(CENTER, CENTER);
  text('Weyl Cones', width/2, 30);
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
  text("Topological Weyl altermagnetism in CrSb", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Physics | General", width / 2, 48);
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
  const concepts = ["CrSb's hexagonal crystal structure forms the basis for its unique magnetic properties. Atoms arrange in a layered lattice with chromium and antimony atoms alternating.", "Exchange interactions create spin-splitting of electronic bands, similar to ferromagnets, but without net magnetization. This splitting is crucial for altermagnetism.", "Antiferromagnetic ordering results in cancellation of net magnetization, yet spin splitting persists. This duality defines altermagnets.", "Topological surface states emerge at material boundaries, enabling unique electron behavior. These states are protected by symmetry and topology.", "Weyl cones represent the band structure of topological materials. Their linear dispersion relations and chirality define Weyl fermions, linking magnetism and topology."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Crystal lattice
  noFill();
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < width; x += 40) {
    for (let y = 0; y < height; y += 40) {
      ellipse(x + 20*sin(frameCount*0.01), y + 20*cos(frameCount*0.01), 10, 10);
      ellipse(x + 30*sin(frameCount*0.01), y + 30*cos(frameCount*0.01), 10, 10);
    }
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('CrSb Crystal Lattice', width/2, 30);
}

function drawStage1() {
  // Spin-splitting bands
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let y = 0; y < height; y += 30) {
    bezier(
      50, y, 50, y, 
      100 + 20*sin(frameCount*0.01), y + 10*cos(frameCount*0.01), 
      200, y + 20*sin(frameCount*0.01)
    );
    bezier(
      50, y + 20, 50, y + 20, 
      100 + 20*cos(frameCount*0.01), y + 10*sin(frameCount*0.01), 
      200, y + 20*cos(frameCount*0.01)
    );
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Spin-Splitting Bands', width/2, 30);
}

function drawStage2() {
  // Magnetic order
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let x = 0; x < width; x += 40) {
    for (let y = 0; y < height; y += 40) {
      line(x + 10, y + 10, x + 10 + 15*cos(frameCount*0.01), y + 10 + 15*sin(frameCount*0.01));
      line(x + 30, y + 30, x + 30 + 15*cos(frameCount*0.01), y + 30 + 15*sin(frameCount*0.01));
    }
  }
  fill(text);
  textAlign(CENTER, CENTER);
  text('Magnetic Order', width/2, 30);
}

function drawStage3() {
  // Topological surface states
  noFill();
  stroke(accent);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < 100; i++) {
    let angle = map(sin(frameCount*0.01 + i), -1, 1, 0, TWO_PI);
    let r = 50 + 20*sin(i*0.1 + frameCount*0.005);
    vertex(r*cos(angle), r*sin(angle));
  }
  endShape();
  fill(text);
  textAlign(CENTER, CENTER);
  text('Topological Surface States', width/2, 30);
}

function drawStage4() {
  // Weyl cones
  noFill();
  stroke(accent);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < 100; i++) {
    let angle = map(cos(frameCount*0.01 + i), -1, 1, 0, TWO_PI);
    let r = 50 + 10*sin(i*0.1 + frameCount*0.005);
    vertex(r*cos(angle), r*sin(angle));
  }
  endShape();
  fill(text);
  textAlign(CENTER, CENTER);
  text('Weyl Cones', width/2, 30);
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
