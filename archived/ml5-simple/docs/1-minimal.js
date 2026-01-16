/**
 * Example 1: Minimal Pose Detection
 *
 * The simplest possible ml5 pose detection.
 * Just tracks the nose position.
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

  // Draw circle at nose position
  if (poses.length > 0) {
    let nose = poses[0].keypoints[0];
    if (nose.confidence > 0.3) {
      fill(255, 0, 255);
      noStroke();
      circle(nose.x, nose.y, 30);
    }
  }
}
