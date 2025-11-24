// ml5.js Body Pose Detection Example
// Based on https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection

let img;
let bodyPose;
let connections;
let poses = [];

function preload() {
  // Initialize MoveNet model for body pose detection
  bodyPose = ml5.bodyPose("MoveNet");

  // Load an image to analyze
  img = loadImage("embarrassing.jpg");
}

function setup() {
  // Create canvas matching the image dimensions
  createCanvas(img.width, img.height);

  // Start detecting poses in the loaded image
  bodyPose.detectStart(img, gotPoses);

  // Retrieve the skeleton structure used by the model
  connections = bodyPose.getSkeleton();
}

function gotPoses(results) {
  // Store detected poses in the global array
  poses = results;
}

function draw() {
  // Display the image as the background
  image(img, 0, 0);

  // Ensure at least one pose is detected before proceeding
  if (poses.length > 0) {
    let pose = poses[0];

    // Loop through the skeleton connections and draw lines
    for (let i = 0; i < connections.length; i++) {
      let connection = connections[i];
      let a = connection[0];
      let b = connection[1];
      let keyPointA = pose.keypoints[a];
      let keyPointB = pose.keypoints[b];
      let confA = keyPointA.confidence;
      let confB = keyPointB.confidence;

      // Only draw lines if both keypoints have sufficient confidence
      if (confA > 0.1 && confB > 0.1) {
        stroke(255, 0, 255);
        strokeWeight(8);
        line(keyPointA.x, keyPointA.y, keyPointB.x, keyPointB.y);
      }
    }

    // Loop through all keypoints and draw circles
    for (let i = 0; i < pose.keypoints.length; i++) {
      let keypoint = pose.keypoints[i];
      fill(255);
      noStroke();

      // Only draw keypoints with sufficient confidence
      if (keypoint.confidence > 0.1) {
        circle(keypoint.x, keypoint.y, 8);
      }
    }
  }
}
