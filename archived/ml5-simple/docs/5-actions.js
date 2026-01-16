/**
 * Example 5: Action Detection
 *
 * Detects simple actions/poses:
 * - Hands raised
 * - T-Pose
 * - Waving
 *
 * To use: Replace sketch.js with this file
 */

let video;
let bodyPose;
let poses = [];
let currentAction = "None";

function preload() {
  bodyPose = ml5.bodyPose("MoveNet");
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

  if (poses.length > 0) {
    let pose = poses[0];

    // Detect action
    currentAction = detectAction(pose);

    // Draw skeleton and keypoints
    drawSkeleton(pose);
    drawKeypoints(pose);
  } else {
    currentAction = "No person detected";
  }

  // Display current action
  drawActionLabel();
}

function detectAction(pose) {
  // Get keypoints
  let nose = pose.keypoints[0];
  let leftShoulder = pose.keypoints[5];
  let rightShoulder = pose.keypoints[6];
  let leftWrist = pose.keypoints[9];
  let rightWrist = pose.keypoints[10];

  // Check confidence
  if (leftWrist.confidence < 0.3 || rightWrist.confidence < 0.3) {
    return "Tracking...";
  }

  // T-Pose: Arms extended horizontally
  if (isTpose(leftShoulder, rightShoulder, leftWrist, rightWrist)) {
    return "T-Pose!";
  }

  // Hands Raised: Both wrists above nose
  if (leftWrist.y < nose.y && rightWrist.y < nose.y) {
    return "Hands Raised!";
  }

  // Right Hand Raised
  if (rightWrist.y < nose.y) {
    return "Right Hand Up";
  }

  // Left Hand Raised
  if (leftWrist.y < nose.y) {
    return "Left Hand Up";
  }

  return "Standing";
}

function isTpose(leftShoulder, rightShoulder, leftWrist, rightWrist) {
  const TOLERANCE = 50; // pixels

  // Wrists at shoulder height
  let leftLevel = Math.abs(leftWrist.y - leftShoulder.y) < TOLERANCE;
  let rightLevel = Math.abs(rightWrist.y - rightShoulder.y) < TOLERANCE;

  // Arms extended outward
  let leftExtended = leftWrist.x < leftShoulder.x - 50;
  let rightExtended = rightWrist.x > rightShoulder.x + 50;

  return leftLevel && rightLevel && leftExtended && rightExtended;
}

function drawActionLabel() {
  // Background box
  fill(0, 0, 0, 180);
  noStroke();
  rectMode(CENTER);
  rect(width / 2, 40, 300, 50, 10);

  // Action text
  fill(255);
  textSize(24);
  textAlign(CENTER, CENTER);
  text(currentAction, width / 2, 40);

  // Reset
  textAlign(LEFT, BASELINE);
  rectMode(CORNER);
}

function drawSkeleton(pose) {
  let connections = bodyPose.getSkeleton();
  stroke(0, 255, 255);
  strokeWeight(2);

  for (let connection of connections) {
    let pointA = pose.keypoints[connection[0]];
    let pointB = pose.keypoints[connection[1]];

    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      line(pointA.x, pointA.y, pointB.x, pointB.y);
    }
  }
}

function drawKeypoints(pose) {
  fill(255, 0, 255);
  noStroke();

  for (let keypoint of pose.keypoints) {
    if (keypoint.confidence > 0.3) {
      circle(keypoint.x, keypoint.y, 10);
    }
  }
}
