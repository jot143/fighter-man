/**
 * ML5 Pose Detection with Action Recognition
 * Simple example with camera input
 */

let video;
let bodyPose;
let poses = [];
let actionRecognizer;
let currentAction = { action: "Waiting...", confidence: 0 };

// Preload the bodyPose model
function preload() {
  bodyPose = ml5.bodyPose("MoveNet");
}

function setup() {
  let canvas = createCanvas(640, 480);
  canvas.parent("canvas-container");

  // Create video capture
  video = createCapture(VIDEO);
  video.size(640, 480);
  video.hide();

  // Initialize action recognizer
  actionRecognizer = new ActionRecognizer();

  // Start pose detection
  bodyPose.detectStart(video, gotPoses);

  // Update status
  document.getElementById("status").textContent = "Model loaded! Stand in front of camera.";
}

// Callback when poses are detected
function gotPoses(results) {
  poses = results;
}

function draw() {
  // Draw the video
  image(video, 0, 0, width, height);

  // Draw all detected poses
  for (let i = 0; i < poses.length; i++) {
    let pose = poses[i];
    drawSkeleton(pose);
    drawKeypoints(pose);

    // Recognize action for first person
    if (i === 0) {
      currentAction = actionRecognizer.recognize(pose);
    }
  }

  // Draw action label
  drawActionLabel();

  // Draw info panel
  drawInfoPanel();
}

// Draw skeleton connections
function drawSkeleton(pose) {
  let connections = bodyPose.getSkeleton();

  for (let i = 0; i < connections.length; i++) {
    let connection = connections[i];
    let pointA = pose.keypoints[connection[0]];
    let pointB = pose.keypoints[connection[1]];

    // Only draw if both points are confident
    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      stroke(0, 255, 255);
      strokeWeight(3);
      line(pointA.x, pointA.y, pointB.x, pointB.y);
    }
  }
}

// Draw keypoints as circles
function drawKeypoints(pose) {
  for (let i = 0; i < pose.keypoints.length; i++) {
    let keypoint = pose.keypoints[i];

    // Only draw confident keypoints
    if (keypoint.confidence > 0.3) {
      fill(255, 0, 255);
      noStroke();
      circle(keypoint.x, keypoint.y, 12);
    }
  }
}

// Draw action label at top of screen
function drawActionLabel() {
  // Background pill
  fill(0, 0, 0, 200);
  noStroke();
  rectMode(CENTER);
  rect(width / 2, 35, 280, 45, 22);

  // Action text
  fill(255);
  textSize(20);
  textAlign(CENTER, CENTER);
  textStyle(BOLD);
  text(currentAction.action, width / 2, 32);

  // Confidence bar
  if (currentAction.confidence > 0) {
    let barWidth = 200;
    let barHeight = 4;
    let barX = width / 2 - barWidth / 2;
    let barY = 52;

    // Background
    fill(60);
    noStroke();
    rectMode(CORNER);
    rect(barX, barY, barWidth, barHeight, 2);

    // Fill
    fill(0, 255, 255);
    rect(barX, barY, barWidth * currentAction.confidence, barHeight, 2);
  }

  // Reset
  textStyle(NORMAL);
  textAlign(LEFT, BASELINE);
  rectMode(CORNER);
}

// Draw info panel
function drawInfoPanel() {
  // Background
  fill(0, 0, 0, 180);
  noStroke();
  rect(10, height - 40, 180, 30, 8);

  // Text
  fill(255);
  textSize(14);
  text(`Poses: ${poses.length}  |  FPS: ${Math.round(frameRate())}`, 20, height - 20);
}
