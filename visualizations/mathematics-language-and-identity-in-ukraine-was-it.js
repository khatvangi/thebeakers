// Language and Identity in Ukraine: Was it Really Nation-Build
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Historical Foundations", "Language as a Vector", "Fractal Identity", "Dynamic Equilibrium", "Synthesis of Forces"];
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
  // p5.js draw code that switches on currentStage
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
  text("Language and Identity in Ukraine: Was it", width / 2, 20);

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
  const concepts = ["The collapse of socialist federations created new spaces for nation-building. Ukraine's post-1991 identity formation began with redefining its historical narrative.", "Language policies became a tool for nation-building. Ukrainian was repositioned as a unifying force against Russian influence, creating symbolic vectors of national identity.", "Fractal patterns represent the recursive nature of identity formation. Each level of the fractal mirrors Ukraine's layered history and cultural complexity.", "Centrifugal forces (regional identities) and centripetal forces (national unity) are visualized as dynamic equilibrium systems. Mathematical models show how these forces interact.", "Mathematical synthesis of language, history, and policy reveals Ukraine's nation-building as a complex system with emergent properties."];
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
  ellipse(width/2, height/2, 100 + sin(frameCount * 0.01) * 20, 100 + sin(frameCount * 0.01) * 20);
  fill(text);
  textAlign(CENTER, CENTER);
  text('Historical Foundations', width/2, height/2 - 30);
  text('1991: New Space for Nation-Building', width/2, height/2 + 30);
}

function drawStage1() {
  background(bg);
  stroke(accent);
  strokeWeight(2);
  noFill();
  beginShape();
  for (let i = 0; i < 360; i += 10) {
    let r = 100 + sin(frameCount * 0.005 + i * 0.1) * 5;
    let x = width/2 + r * cos(radians(i));
    let y = height/2 + r * sin(radians(i));
    vertex(x, y);
  }
  endShape();
  fill(text);
  textAlign(LEFT, TOP);
  text('Language as a Vector', 20, 20);
  text('Ukrainian repositioned as unifying force', 20, 60);
}

function drawStage2() {
  background(bg);
  stroke(accent);
  strokeWeight(1);
  noFill();
  beginShape();
  for (let i = 0; i < 200; i += 1) {
    let x = 400 + sin(frameCount * 0.002 + i * 0.05) * 10;
    let y = 270 + cos(frameCount * 0.002 + i * 0.05) * 10;
    curveVertex(x, y);
  }
  endShape();
  fill(accent);
  ellipse(400, 270, 20, 20);
  fill(text);
  textAlign(CENTER, CENTER);
  text('Fractal Identity', width/2, height/2);
  text('Recursive patterns of history', width/2, height/2 + 30);
}

function drawStage3() {
  background(bg);
  stroke(accent);
  strokeWeight(2);
  noFill();
  beginShape();
  for (let i = 0; i < 180; i += 2) {
    let x = 400 + sin(frameCount * 0.003 + i * 0.05) * 15;
    let y = 270 + cos(frameCount * 0.003 + i * 0.05) * 15;
    bezierVertex(x, y, x + 10, y - 10, x + 20, y);
  }
  endShape();
  fill(text);
  textAlign(CENTER, CENTER);
  text('Dynamic Equilibrium', width/2, height/2);
  text('Centrifugal vs Centripetal Forces', width/2, height/2 + 30);
}

function drawStage4() {
  background(bg);
  stroke(accent);
  strokeWeight(1);
  noFill();
  beginShape();
  for (let i = 0; i < 100; i += 1) {
    let angle = radians(i);
    let x = 400 + 100 * cos(angle) + sin(frameCount * 0.002 + angle) * 5;
    let y = 270 + 100 * sin(angle) + cos(frameCount * 0.002 + angle) * 5;
    curveVertex(x, y);
  }
  endShape();
  fill(accent);
  ellipse(400, 270, 15, 15);
  fill(text);
  textAlign(CENTER, CENTER);
  text('Synthesis of Forces', width/2, height/2);
  text('Emergent properties of nation-building', width/2, height/2 + 30);
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
