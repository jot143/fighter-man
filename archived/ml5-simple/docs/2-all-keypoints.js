/**
 * Example 2: All Keypoints
 *
 * Draws all 17 body keypoints.
 * Shows how to loop through keypoints array.
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

    // Draw all keypoints
    for (let keypoint of pose.keypoints) {
      if (keypoint.confidence > 0.3) {
        fill(255, 0, 255);
        noStroke();
        circle(keypoint.x, keypoint.y, 10);

        // Show keypoint name
        fill(255);
        textSize(10);
        text(keypoint.name, keypoint.x + 8, keypoint.y);
      }
    }
  }

  // Info
  fill(255);
  noStroke();
  textSize(14);
  text(`Keypoints: 17 total`, 10, 25);
}
