/**
 * Example 3: Skeleton Drawing
 *
 * Draws skeleton connections between keypoints.
 * Uses bodyPose.getSkeleton() for connection pairs.
 *
 * To use: Replace sketch.js with this file
 */

let video;
let bodyPose;
let poses = [];

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

    // Draw skeleton first (behind keypoints)
    drawSkeleton(pose);

    // Draw keypoints
    drawKeypoints(pose);
  }

  // Info
  fill(255);
  noStroke();
  textSize(14);
  text(`Poses: ${poses.length}`, 10, 25);
}

function drawSkeleton(pose) {
  // Get array of connection pairs: [[0,1], [1,3], ...]
  let connections = bodyPose.getSkeleton();

  stroke(0, 255, 255); // Cyan
  strokeWeight(2);

  for (let connection of connections) {
    let indexA = connection[0];
    let indexB = connection[1];

    let pointA = pose.keypoints[indexA];
    let pointB = pose.keypoints[indexB];

    // Only draw if both points are confident
    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      line(pointA.x, pointA.y, pointB.x, pointB.y);
    }
  }
}

function drawKeypoints(pose) {
  fill(255, 0, 255); // Magenta
  noStroke();

  for (let keypoint of pose.keypoints) {
    if (keypoint.confidence > 0.3) {
      circle(keypoint.x, keypoint.y, 10);
    }
  }
}
