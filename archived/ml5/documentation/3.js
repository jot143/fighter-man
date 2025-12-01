// ml5.js Real-Time Body Pose Detection with Smoothing
// https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection

let video;
let bodyPose;
let connections;
let poses = [];

// Variables for smoothing the nose position using linear interpolation
let lerpedX = 0;
let lerpedY = 0;

function preload() {
  // Initialize MoveNet model with flipped video input
  bodyPose = ml5.bodyPose("MoveNet", { flipped: true });
}

function mousePressed() {
  // Log detected pose data to the console when the mouse is pressed
  console.log(poses);
}

function gotPoses(results) {
  // Store detected poses in the global array
  poses = results;
}

function setup() {
  // Create canvas for displaying video feed
  createCanvas(640, 480);

  // Capture live video with flipped orientation
  video = createCapture(VIDEO, { flipped: true });
  video.hide();

  // Start detecting poses from the video feed
  bodyPose.detectStart(video, gotPoses);
}

function draw() {
  // Display the live video feed
  image(video, 0, 0);

  // Ensure at least one pose is detected before proceeding
  if (poses.length > 0) {
    let pose = poses[0];
    let x = pose.nose.x;
    let y = pose.nose.y;

    // Smoothly interpolate the nose position to reduce jitter
    lerpedX = lerp(lerpedX, x, 0.3);
    lerpedY = lerp(lerpedY, y, 0.3);

    // Draw a circle at the smoothed nose position
    fill(255, 0, 0);
    circle(lerpedX, lerpedY, 20);
  }
}
