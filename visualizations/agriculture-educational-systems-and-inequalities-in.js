// Educational Systems and Inequalities in Educational Attainme
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Foundations of Agricultural Education", "Stage 2: Pathways to Higher Learning", "Stage 3: Inequality in Access", "Stage 4: Systematic Patterns", "Stage 5: Future Directions"];
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
  fill(bg);
  noStroke();

  if (currentStage === 0) {
    drawStage0();
  } else if (currentStage === 1) {
    drawStage1();
  } else if (currentStage === 2) {
    drawStage2();
  } else if (currentStage === 3) {
    drawStage3();
  } else if (currentStage === 4) {
    drawStage4();
  }

  // Micro-movement for all stages
  for (let i = 0; i < 10; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/10);
    let y = 540/2 + sin(angle) * 10;
    fill(accent);
    ellipse(x, y, 8, 8);
  }
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
  text("Educational Systems and Inequalities in ", width / 2, 20);

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
  const concepts = ["Agricultural education systems in CEE countries show distinct patterns of vocational training and higher education access. This visualization explores how these systems shape educational outcomes.", "Secondary education in these regions often splits into vocational and academic tracks. This stage shows the divergence in educational pathways and their implications for future opportunities.", "Students from disadvantaged backgrounds face systemic barriers in accessing higher education. This stage illustrates how socioeconomic factors influence educational attainment.", "National data reveals patterns of selectivity in higher education. This stage connects secondary education tracks to university admission rates across CEE countries.", "The visualization concludes with projections of educational reforms and their potential impact on reducing inequalities in agricultural education systems."];
  return concepts[stage] || "";
}

function drawControls() {
  fill(colors.secondary);
  textSize(11);
  textAlign(RIGHT, BOTTOM);
  text("← → Navigate stages | R Reset", width - 20, height - 15);
}

function drawStage0() {
  // Base grid with agricultural symbols
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < 850; x += 100) {
    for (let y = 0; y < 540; y += 100) {
      line(x, y, x+100, y+100);
      line(x, y+100, x+100, y);
    }
  }

  // Animated particles
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 20; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/20);
    let y = 540/2 + sin(angle) * 10;
    ellipse(x, y, 12, 12);
  }
}

function drawStage1() {
  // Grid with educational pathways
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < 85, x += 150) {
    for (let y = 0; y < 540; y += 150) {
      line(x, y, x+150, y+150);
      line(x, y+150, x+150, y);
    }
  }

  // Animated tractors
  noFill();
  stroke(accent);
  strokeWeight(3);
  for (let i = 0; i < 15; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/15);
    let y = 540/2 + sin(angle) * 12;
    ellipse(x, y, 20, 10);
  }
}

function drawStage2() {
  // Grid with inequality indicators
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < 850; x += 120) {
    for (let y = 0; y < 540; y += 120) {
      line(x, y, x+120, y+120);
      line(x, y+120, x+120, y);
    }
  }

  // Animated soil particles
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 25; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/25);
    let y = 540/2 + sin(angle) * 10;
    ellipse(x, y, 8, 8);
  }
}

function drawStage3() {
  // Grid with data patterns
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < 850; x += 140) {
    for (let y = 0; y < 540; y += 140) {
      line(x, y, x+140, y+140);
      line(x, y+140, x+140, y);
    }
  }

  // Animated bar charts
  noFill();
  stroke(accent);
  strokeWeight(3);
  for (let i = 0; i < 10; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/10);
    let y = 540/2 + sin(angle) * 12;
    line(x, y, x+10, y);
  }
}

function drawStage4() {
  // Grid with future projections
  stroke(accent);
  strokeWeight(1);
  for (let x = 0; x < 850; x += 160) {
    for (let y = 0; y < 540; y += 160) {
      line(x, y, x+160, y+160);
      line(x, y+160, x+160, y);
    }
  }

  // Animated growth patterns
  noFill();
  stroke(accent);
  strokeWeight(2);
  for (let i = 0; i < 30; i++) {
    let angle = (frameCount * 0.01 + i * 0.2) % (TWO_PI);
    let x = 850 * (i/30);
    let y = 540/2 + sin(angle) * 10;
    ellipse(x, y, 10, 10);
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
