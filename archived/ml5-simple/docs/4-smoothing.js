/**
 * Example 4: Smoothing with Lerp
 *
 * Uses linear interpolation to smooth jittery movements.
 * Creates smoother, more natural tracking.
 *
 * To use: Replace sketch.js with this file
 */

let video;
let bodyPose;
let poses = [];

// Smoothed keypoints storage
let smoothedKeypoints = [];
const LERP_AMOUNT = 0.3; // 0 = no smoothing, 1 = no delay

function preload() {
  bodyPose = ml5.bodyPose("MoveNet");
}

function setup() {
  let canvas = createCanvas(640, 480);
  canvas.parent("canvas-container");

  video = createCapture(VIDEO);
  video.size(640, 480);
  video.hide();

  // Initialize smoothed keypoints array (17 keypoints)
  for (let i = 0; i < 17; i++) {
    smoothedKeypoints.push({ x: 0, y: 0 });
  }

  bodyPose.detectStart(video, gotPoses);
}

function gotPoses(results) {
  poses = results;
}

function draw() {
  image(video, 0, 0);

  if (poses.length > 0) {
    let pose = poses[0];

    // Update smoothed positions
    for (let i = 0; i < pose.keypoints.length; i++) {
      let keypoint = pose.keypoints[i];
      if (keypoint.confidence > 0.3) {
        // Lerp towards new position
        smoothedKeypoints[i].x = lerp(smoothedKeypoints[i].x, keypoint.x, LERP_AMOUNT);
        smoothedKeypoints[i].y = lerp(smoothedKeypoints[i].y, keypoint.y, LERP_AMOUNT);
      }
    }

    // Draw with smoothed positions
    drawSmoothedSkeleton(pose);
    drawSmoothedKeypoints(pose);
  }

  // Info
  fill(255);
  noStroke();
  textSize(14);
  text(`Lerp amount: ${LERP_AMOUNT}`, 10, 25);
  text(`Lower = smoother but delayed`, 10, 45);
}

function drawSmoothedSkeleton(pose) {
  let connections = bodyPose.getSkeleton();

  stroke(0, 255, 255);
  strokeWeight(2);

  for (let connection of connections) {
    let indexA = connection[0];
    let indexB = connection[1];

    let pointA = pose.keypoints[indexA];
    let pointB = pose.keypoints[indexB];

    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      // Use smoothed positions
      line(
        smoothedKeypoints[indexA].x,
        smoothedKeypoints[indexA].y,
        smoothedKeypoints[indexB].x,
        smoothedKeypoints[indexB].y
      );
    }
  }
}

function drawSmoothedKeypoints(pose) {
  fill(255, 0, 255);
  noStroke();

  for (let i = 0; i < pose.keypoints.length; i++) {
    if (pose.keypoints[i].confidence > 0.3) {
      circle(smoothedKeypoints[i].x, smoothedKeypoints[i].y, 10);
    }
  }
}
