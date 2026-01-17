// Language and Identity in Ukraine: Was it Really Nation-Build
// Generated visualization for The Beakers

let currentStage = 0;
const totalStages = 5;
let stageLabels = ["Stage 1: Nation-Building Foundations", "Stage 2: Language as Identity Marker", "Stage 3: Historical Policy Shifts", "Stage 4: Modern Language Policies", "Stage 5: Balancing Centrifugal Forces"];
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
  text("Language and Identity in Ukraine: Was it", width / 2, 20);

  fill(colors.secondary);
  textSize(12);
  text("Engineering | General", width / 2, 48);
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
  const concepts = ["The collapse of socialist federations reignited debates on nation-building, with Ukraine seeking to balance state unity and national identity through language policies.", "Language became a critical tool for constructing Ukrainian identity, with policies promoting Ukrainian as the dominant language while managing regional linguistic diversity.", "Historical policies oscillated between centralizing Ukrainian and accommodating regional languages, reflecting tensions between state control and cultural pluralism.", "Modern policies emphasize linguistic equality, with initiatives to standardize Ukrainian across education, media, and public life while respecting minority languages.", "Ukraine's nation-building project navigates between strengthening national unity and mitigating centrifugal forces through dynamic language policy adjustments."];
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
  beginShape();
  for (let i = 0; i < 360; i += 10) {
    let x = 425 + 150 * cos(radians(i));
    let y = 270 + 150 * sin(radians(i));
    vertex(x, y);
  }
  endShape(CLOSE);
  fill(text);
  noStroke();
  textAlign(CENTER, CENTER);
  textSize(14);
  text("Ukraine's Nation-Building Project", 425, 270);
}

function drawStage1() {
  background(bg);
  noStroke();
  fill(accent);
  for (let i = 0; i < 100; i++) {
    let x = random(50, 800);
    let y = random(50, 500);
    let r = 5 + sin(frameCount * 0.01 + i) * 3;
    ellipse(x, y, r, r);
  }
  fill(text);
  noStroke();
  textAlign(LEFT, TOP);
  textSize(14);
  text("Language policies became central to constructing Ukrainian identity, with Ukrainian as the primary medium for statehood.", 50, 50);
}

function drawStage2() {
  background(bg);
  stroke(accent);
  strokeWeight(1);
  for (let i = 0; i < 100; i++) {
    let x = 425 + 200 * sin(radians(i * 3.6));
    let y = 270 + 200 * cos(radians(i * 3.6));
    line(x, y, x + 10 * cos(radians(i * 3.6 + 90)), y + 10 * sin(radians(i * 3.6 + 90)));
  }
  fill(text);
  noStroke();
  textAlign(LEFT, TOP);
  textSize(14);
  text("Historical policies oscillated between centralizing Ukrainian and accommodating regional languages, reflecting tensions between state control and cultural pluralism.", 50, 50);
}

function drawStage3() {
  background(bg);
  noStroke();
  fill(accent);
  for (let i = 0; i < 50; i++) {
    let x = 425 + 150 * sin(radians(i * 7.2));
    let y = 270 + 150 * cos(radians(i * 7.2));
    let r = 10 + sin(frameCount * 0.01 + i * 2) * 5;
    ellipse(x, y, r, r);
  }
  fill(text);
  noStroke();
  textAlign(LEFT, TOP);
  textSize(14);
  text("Modern policies emphasize linguistic equality, with initiatives to standardize Ukrainian across education, media, and public life while respecting minority languages.", 50, 50);
}

function drawStage4() {
  background(bg);
  noFill();
  stroke(accent);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < 360; i += 10) {
    let x = 425 + 150 * cos(radians(i));
    let y = 270 + 150 * sin(radians(i));
    let offset = sin(frameCount * 0.01 + i) * 5;
    vertex(x + offset, y + offset);
  }
  endShape(CLOSE);
  fill(text);
  noStroke();
  textAlign(CENTER, CENTER);
  textSize(14);
  text("Ukraine's nation-building project navigates between strengthening national unity and mitigating centrifugal forces through dynamic language policy adjustments.", 425, 270);
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
