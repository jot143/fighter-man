// 3D Pose Detection with BlazePose and WEBGL
// https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection

let video;
let bodyPose;
let connections;
let poses = [];
let angle = 0;

function preload() {
  // Initialize BlazePose model for 3D pose estimation
  bodyPose = ml5.bodyPose("BlazePose");
}

function gotPoses(results) {
  poses = results;
}

function setup() {
  createCanvas(640, 360, WEBGL);

  // Load and loop the video for pose detection
  video = createVideo("dan_3D_test.mov");
  video.loop();

  // Start detecting poses
  bodyPose.detectStart(video, gotPoses);

  // Retrieve the skeleton connections used by the model
  connections = bodyPose.getSkeleton();
}

function draw() {
  scale(height / 2);
  orbitControl();
  //rotateY(angle);
  angle += 0.02;
  background(0);

  // Ensure at least one pose is detected
  if (poses.length > 0) {
    let pose = poses[0];

    // Draw skeleton connections
    for (let i = 0; i < connections.length; i++) {
      let connection = connections[i];
      let a = connection[0];
      let b = connection[1];
      let keyPointA = pose.keypoints3D[a];
      let keyPointB = pose.keypoints3D[b];

      let confA = keyPointA.confidence;
      let confB = keyPointB.confidence;

      // Only draw connections with sufficient confidence
      if (confA > 0.1 && confB > 0.1) {
        stroke(0, 255, 255);
        strokeWeight(4);
        beginShape();
        vertex(keyPointA.x, keyPointA.y, keyPointA.z);
        vertex(keyPointB.x, keyPointB.y, keyPointB.z);
        endShape();
      }
    }

    // Draw keypoints as rotating 3D boxes
    for (let i = 0; i < pose.keypoints.length; i++) {
      let keypoint = pose.keypoints3D[i];
      stroke(255, 0, 255);
      strokeWeight(1);
      fill(255, 150);

      if (keypoint.confidence > 0.1) {
        push();
        translate(keypoint.x, keypoint.y, keypoint.z);
        rotateZ(angle);
        box(0.1);
        pop();
      }
    }
  }

  // Draw a ground plane
  stroke(255);
  rectMode(CENTER);
  strokeWeight(1);
  fill(255, 100);
  translate(0, 1);
  rotateX(PI / 2);
  square(0, 0, 2);
}

function mousePressed() {
  console.log(poses);
}
