// Body Pose augmented with hat and other effects
// https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection

let video;
let bodyPose;
let poses = [];
let emitter;

function preload() {
  // Initialize MoveNet model with flipped video input
  bodyPose = ml5.bodyPose("MoveNet", { flipped: true });
}

function mousePressed() {
  // Log detected pose data
  console.log(poses);
}

function gotPoses(results) {
  // Store detected poses
  poses = results;
}

function setup() {
  createCanvas(640, 480);
  video = createCapture(VIDEO, { flipped: true });
  video.hide();
  bodyPose.detectStart(video, gotPoses);

  // Initialize particle emitter at the bottom center of the canvas
  emitter = new Emitter(width / 2, height - 40);
}

function draw() {
  image(video, 0, 0);

  if (poses.length > 0) {
    let pose = poses[0];
    let { nose, left_ear, right_ear } = pose;

    // Calculate the position and orientation for the hat
    let hatx = (left_ear.x + right_ear.x) / 2;
    let haty = (left_ear.y + right_ear.y) / 2;
    let v = createVector(right_ear.x - left_ear.x, right_ear.y - left_ear.y);
    let angle = v.heading();

    push();
    translate(hatx, haty);
    rotate(angle);

    let d = dist(left_ear.x, left_ear.y, right_ear.x, right_ear.y);
    translate(0, -d / 2);

    // Draw a triangle-shaped hat
    strokeWeight(4);
    stroke(252, 238, 33);
    fill(236, 1, 90);
    triangle(-d / 2, 0, d / 2, 0, 0, -d);

    // Position the particle emitter above the hat
    emitter.origin.x = hatx + sin(angle) * d * 1.5;
    emitter.origin.y = haty - cos(angle) * d * 1.5;

    pop();
  }

  // Update and generate particles
  emitter.run();
  emitter.addParticle();
}
