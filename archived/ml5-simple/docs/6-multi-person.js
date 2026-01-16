/**
 * Example 6: Multi-Person Tracking
 *
 * Detects and tracks multiple people simultaneously.
 * Each person gets a unique color.
 *
 * To use: Replace sketch.js with this file
 */

let video;
let bodyPose;
let poses = [];

// Colors for different people
const PERSON_COLORS = [
  [0, 255, 255],   // Cyan
  [255, 255, 0],   // Yellow
  [0, 255, 0],     // Green
  [255, 100, 0],   // Orange
  [255, 0, 255],   // Magenta
  [100, 100, 255]  // Light Blue
];

function preload() {
  // Use MULTIPOSE model for multiple people
  bodyPose = ml5.bodyPose("MoveNet", {
    modelType: "MULTIPOSE_LIGHTNING"
  });
}

function setup() {
  let canvas = createCanvas(640, 480);
  canvas.parent("canvas-container");

  video = createCapture(VIDEO);
  video.size(640, 480);
  video.hide();

  bodyPose.detectStart(video, gotPoses);
}

function gotPoses(results) {
  poses = results;
}

function draw() {
  image(video, 0, 0);

  // Draw each detected person with unique color
  for (let i = 0; i < poses.length; i++) {
    let pose = poses[i];
    let color = PERSON_COLORS[i % PERSON_COLORS.length];

    drawSkeleton(pose, color);
    drawKeypoints(pose, color);
    drawPersonLabel(pose, i + 1, color);
  }

  // Info panel
  drawInfoPanel();
}

function drawSkeleton(pose, color) {
  let connections = bodyPose.getSkeleton();

  stroke(color[0], color[1], color[2]);
  strokeWeight(3);

  for (let connection of connections) {
    let pointA = pose.keypoints[connection[0]];
    let pointB = pose.keypoints[connection[1]];

    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      line(pointA.x, pointA.y, pointB.x, pointB.y);
    }
  }
}

function drawKeypoints(pose, color) {
  fill(color[0], color[1], color[2]);
  noStroke();

  for (let keypoint of pose.keypoints) {
    if (keypoint.confidence > 0.3) {
      circle(keypoint.x, keypoint.y, 12);
    }
  }
}

function drawPersonLabel(pose, personNumber, color) {
  // Find the nose or highest confident keypoint for label position
  let nose = pose.keypoints[0];

  if (nose.confidence > 0.3) {
    // Background pill
    fill(color[0], color[1], color[2]);
    noStroke();
    rectMode(CENTER);
    rect(nose.x, nose.y - 40, 80, 25, 12);

    // Text
    fill(0);
    textSize(14);
    textAlign(CENTER, CENTER);
    textStyle(BOLD);
    text(`Person ${personNumber}`, nose.x, nose.y - 40);

    // Reset
    textStyle(NORMAL);
    textAlign(LEFT, BASELINE);
    rectMode(CORNER);
  }
}

function drawInfoPanel() {
  // Background
  fill(0, 0, 0, 180);
  noStroke();
  rect(10, 10, 200, 80, 10);

  // Text
  fill(255);
  textSize(16);
  text(`People detected: ${poses.length}`, 20, 35);
  text(`Max supported: 6`, 20, 55);
  text(`Model: MULTIPOSE`, 20, 75);
}
