// Real-Time Body Action Recognition with ml5.js
// Supports both webcam and video file input

let video;
let bodyPose;
let poses = [];
let connections;
let actionRecognizer;

// Input source management
let inputMode = "camera"; // "camera" or "video"
let videoFile;
let isModelReady = false;

// UI elements
let toggleButton;
let fileInput;
let statusDiv;

// Performance tracking
let frameRateDisplay;
let lastFrameTime = 0;

// Color palette for multiple people
let personColors = [
  { skeleton: [0, 255, 255], keypoint: [255, 0, 255], name: "Cyan" },     // Person 1
  { skeleton: [255, 255, 0], keypoint: [255, 200, 0], name: "Yellow" },   // Person 2
  { skeleton: [0, 255, 0], keypoint: [0, 200, 0], name: "Green" },        // Person 3
  { skeleton: [255, 165, 0], keypoint: [255, 140, 0], name: "Orange" },   // Person 4
  { skeleton: [255, 105, 180], keypoint: [255, 20, 147], name: "Pink" },  // Person 5
  { skeleton: [138, 43, 226], keypoint: [186, 85, 211], name: "Purple" }  // Person 6
];

function preload() {
  // Initialize MoveNet MultiPose model for detecting multiple people
  bodyPose = ml5.bodyPose("MoveNet", {
    modelType: "MULTIPOSE_LIGHTNING"
  }, modelReady);
}

function modelReady() {
  isModelReady = true;
  console.log("BodyPose model loaded successfully!");
  updateStatus("Model loaded - Ready to start");
}

function setup() {
  createCanvas(640, 480);

  // Initialize action recognizer
  actionRecognizer = new ActionRecognizer();

  // Create UI elements
  createUI();

  // Start with camera by default
  startCamera();

  // Get skeleton connections for visualization
  connections = bodyPose.getSkeleton();
}

function createUI() {
  // Status display
  statusDiv = createDiv("Loading model...");
  statusDiv.position(10, height + 10);
  statusDiv.style("font-family", "monospace");
  statusDiv.style("font-size", "14px");
  statusDiv.style("color", "#333");

  // Toggle button
  toggleButton = createButton("Switch to Video File");
  toggleButton.position(10, height + 40);
  toggleButton.mousePressed(toggleInputMode);
  toggleButton.style("padding", "10px 20px");
  toggleButton.style("font-size", "14px");
  toggleButton.style("cursor", "pointer");

  // File input (initially hidden)
  fileInput = createFileInput(handleVideoFile);
  fileInput.position(180, height + 40);
  fileInput.style("display", "none");
  fileInput.attribute("accept", "video/*");
}

function toggleInputMode() {
  if (inputMode === "camera") {
    // Switch to video file mode
    inputMode = "video";
    toggleButton.html("Switch to Camera");
    fileInput.style("display", "block");

    // Stop camera
    if (video && video.elt.srcObject) {
      bodyPose.detectStop();
      video.stop();
      video.remove();
      video = null;
    }

    updateStatus("Please select a video file");
  } else {
    // Switch to camera mode
    inputMode = "camera";
    toggleButton.html("Switch to Video File");
    fileInput.style("display", "none");

    // Stop video file
    if (videoFile) {
      bodyPose.detectStop();
      videoFile.stop();
      videoFile.remove();
      videoFile = null;
    }

    startCamera();
  }
}

function startCamera() {
  if (!isModelReady) {
    updateStatus("Waiting for model to load...");
    setTimeout(startCamera, 500);
    return;
  }

  video = createCapture(VIDEO);
  video.size(640, 480);
  video.hide();

  // Start pose detection on camera
  bodyPose.detectStart(video, gotPoses);
  updateStatus("Camera active - Detecting poses");
}

function handleVideoFile(file) {
  if (file.type !== "video") {
    updateStatus("Please select a video file");
    return;
  }

  // Stop previous video if exists
  if (videoFile) {
    bodyPose.detectStop();
    videoFile.stop();
    videoFile.remove();
  }

  // Create video element from file
  videoFile = createVideo(file.data, videoLoaded);
  videoFile.size(640, 480);
  videoFile.hide();
  videoFile.loop();

  updateStatus("Loading video file...");
}

function videoLoaded() {
  // Start pose detection on video file
  bodyPose.detectStart(videoFile, gotPoses);
  updateStatus("Video loaded - Detecting poses");
}

function gotPoses(results) {
  poses = results;
}

function updateStatus(message) {
  if (statusDiv) {
    statusDiv.html(message);
  }
}

function draw() {
  background(0);

  // Display video source
  if (inputMode === "camera" && video) {
    image(video, 0, 0, width, height);
  } else if (inputMode === "video" && videoFile) {
    image(videoFile, 0, 0, width, height);
  }

  // Draw overlay info
  drawInfoPanel();

  // Process and visualize ALL detected poses
  if (poses.length > 0) {
    // Loop through all detected people
    for (let i = 0; i < poses.length; i++) {
      let pose = poses[i];
      let personIndex = i; // Use index for color selection
      let colors = personColors[personIndex % personColors.length];

      // Draw skeleton with person-specific color
      drawSkeleton(pose, colors);

      // Draw keypoints with person-specific color
      drawKeypoints(pose, colors);

      // Recognize and display action for this person
      let result = actionRecognizer.recognize(pose);
      drawActionLabel(result, pose, personIndex + 1, colors);
    }
  } else {
    // No pose detected message
    drawNoDetectionMessage();
  }

  // Calculate and display FPS
  calculateFPS();
}

function drawSkeleton(pose, colors) {
  // Draw skeleton connections with person-specific color
  stroke(colors.skeleton[0], colors.skeleton[1], colors.skeleton[2]);
  strokeWeight(2);

  for (let i = 0; i < connections.length; i++) {
    let connection = connections[i];
    let a = connection[0];
    let b = connection[1];
    let keyPointA = pose.keypoints[a];
    let keyPointB = pose.keypoints[b];

    // Only draw if both keypoints are confident
    if (keyPointA.confidence > 0.3 && keyPointB.confidence > 0.3) {
      line(keyPointA.x, keyPointA.y, keyPointB.x, keyPointB.y);
    }
  }
}

function drawKeypoints(pose, colors) {
  // Draw all keypoints with person-specific color
  for (let i = 0; i < pose.keypoints.length; i++) {
    let keypoint = pose.keypoints[i];

    if (keypoint.confidence > 0.3) {
      fill(colors.keypoint[0], colors.keypoint[1], colors.keypoint[2]);
      noStroke();
      circle(keypoint.x, keypoint.y, 8);

      // Optional: Draw keypoint labels
      // fill(255);
      // textSize(10);
      // text(keypoint.name, keypoint.x + 5, keypoint.y - 5);
    }
  }
}

function drawActionLabel(result, pose, personNumber, colors) {
  // Find the highest point (top of head) to position label above
  let highestY = height;
  let centerX = width / 2;

  // Find nose or highest confident keypoint
  if (pose.nose && pose.nose.confidence > 0.3) {
    highestY = pose.nose.y;
    centerX = pose.nose.x;
  } else {
    // Find any confident keypoint
    for (let kp of pose.keypoints) {
      if (kp.confidence > 0.3 && kp.y < highestY) {
        highestY = kp.y;
        centerX = kp.x;
      }
    }
  }

  // Draw label above person's head
  push();

  // Background box
  let boxWidth = 200;
  let boxHeight = 60;
  let boxX = centerX - boxWidth / 2;
  let boxY = highestY - boxHeight - 20;

  // Ensure box stays on screen
  boxX = constrain(boxX, 5, width - boxWidth - 5);
  boxY = constrain(boxY, 5, height - boxHeight - 5);

  fill(0, 0, 0, 180);
  noStroke();
  rect(boxX, boxY, boxWidth, boxHeight, 5);

  // Person label with color indicator
  fill(colors.skeleton[0], colors.skeleton[1], colors.skeleton[2]);
  textSize(14);
  textStyle(BOLD);
  textAlign(LEFT, TOP);
  text("Person " + personNumber, boxX + 10, boxY + 8);

  // Action name
  fill(255);
  textSize(18);
  textStyle(BOLD);
  text(result.action, boxX + 10, boxY + 25);

  // Confidence percentage
  textSize(12);
  textStyle(NORMAL);
  let confidenceText = (result.confidence * 100).toFixed(0) + "%";
  text(confidenceText, boxX + boxWidth - 45, boxY + 8);

  // Confidence bar
  let barWidth = boxWidth - 20;
  fill(colors.skeleton[0], colors.skeleton[1], colors.skeleton[2], 150);
  rect(boxX + 10, boxY + 47, result.confidence * barWidth, 6, 3);
  noFill();
  stroke(255, 150);
  strokeWeight(1);
  rect(boxX + 10, boxY + 47, barWidth, 6, 3);

  pop();
}

function drawNoDetectionMessage() {
  push();
  fill(255, 100, 100, 200);
  noStroke();
  textAlign(CENTER, CENTER);
  textSize(20);
  text("No person detected", width / 2, height / 2);
  pop();
}

function drawInfoPanel() {
  // Bottom-right info panel with people counter
  push();
  fill(0, 0, 0, 180);
  noStroke();
  rect(width - 160, height - 80, 150, 70);

  fill(255);
  textSize(12);
  textAlign(LEFT);

  // People counter
  let peopleText = poses.length === 1 ? "1 person" : poses.length + " people";
  fill(0, 255, 0);
  text("Detecting: " + peopleText, width - 150, height - 60);

  // Mode and FPS
  fill(255);
  text("Mode: " + (inputMode === "camera" ? "Camera" : "Video"), width - 150, height - 40);
  text("FPS: " + frameRateDisplay, width - 150, height - 20);

  pop();
}

function calculateFPS() {
  let currentTime = millis();
  let fps = 1000 / (currentTime - lastFrameTime);
  lastFrameTime = currentTime;
  frameRateDisplay = fps.toFixed(1);
}

// Keyboard shortcuts
function keyPressed() {
  if (key === 't' || key === 'T') {
    toggleInputMode();
  }
  if (key === ' ') {
    // Pause/play video
    if (inputMode === "video" && videoFile) {
      if (videoFile.elt.paused) {
        videoFile.play();
      } else {
        videoFile.pause();
      }
    }
  }
}
