// ml5.js Real-Time Body Pose Detection Example
// Based on https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection

let video;
let bodyPose;
let connections;
let poses = [];

function preload() {
  // Initialize MoveNet model with flipped video input
  bodyPose = ml5.bodyPose("MoveNet", { flipped: true });
}

function mousePressed() {
  console.log(poses);
}

function gotPoses(results) {
  // Store detected poses in the global array
  poses = results;
}

function setup() {
  createCanvas(640, 480);

  // Capture live video with flipped orientation
  video = createCapture(VIDEO, { flipped: true });
  video.hide();

  // Start detecting poses from the video feed
  bodyPose.detectStart(video, gotPoses);
}

function draw() {
  image(video, 0, 0);

  // At least one pose
  if (poses.length > 0) {
    let pose = poses[0];

    // Draw a circle at the detected nose position
    fill(236, 1, 90);
    noStroke();
    circle(pose.nose.x, pose.nose.y, 48);
  }
}
