# ML5 Pose Detection - Simple Example

A minimal implementation of real-time pose detection using ml5.js and p5.js with webcam input.

## Quick Start

```bash
# Navigate to this folder
cd /Users/gorki/Herd/neuronso-connection/archived/ml5-simple

# Serve the files (any static server works)
npx serve .

# Open http://localhost:3000 in your browser
```

## Files

| File | Description |
|------|-------------|
| `index.html` | HTML entry point with CDN links |
| `sketch.js` | Main p5.js sketch with pose detection |
| `actions.js` | ActionRecognizer class for gesture detection |
| `README.md` | This documentation |
| `docs/` | Progressive learning examples |

## How It Works

### 1. Load the Libraries (index.html)

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
<script src="https://unpkg.com/ml5@1/dist/ml5.min.js"></script>
```

### 2. Initialize the Model (sketch.js)

```javascript
let bodyPose;

function preload() {
  // Load MoveNet model before setup
  bodyPose = ml5.bodyPose("MoveNet");
}
```

### 3. Set Up Camera

```javascript
let video;

function setup() {
  createCanvas(640, 480);

  // Create webcam capture
  video = createCapture(VIDEO);
  video.size(640, 480);
  video.hide(); // Hide default HTML video element

  // Start continuous pose detection
  bodyPose.detectStart(video, gotPoses);
}
```

### 4. Receive Pose Data

```javascript
let poses = [];

function gotPoses(results) {
  poses = results; // Array of detected poses
}
```

### 5. Draw the Results

```javascript
function draw() {
  image(video, 0, 0);

  for (let pose of poses) {
    drawKeypoints(pose);
    drawSkeleton(pose);
  }
}
```

---

## Pose Data Structure

Each detected pose contains:

```javascript
{
  keypoints: [
    { x: 320, y: 150, confidence: 0.95, name: "nose" },
    { x: 310, y: 140, confidence: 0.92, name: "left_eye" },
    // ... 17 keypoints total
  ],
  box: { xMin, yMin, xMax, yMax, width, height }
}
```

---

## 17 Body Keypoints

| Index | Name | Description |
|-------|------|-------------|
| 0 | nose | Nose tip |
| 1 | left_eye | Left eye |
| 2 | right_eye | Right eye |
| 3 | left_ear | Left ear |
| 4 | right_ear | Right ear |
| 5 | left_shoulder | Left shoulder |
| 6 | right_shoulder | Right shoulder |
| 7 | left_elbow | Left elbow |
| 8 | right_elbow | Right elbow |
| 9 | left_wrist | Left wrist |
| 10 | right_wrist | Right wrist |
| 11 | left_hip | Left hip |
| 12 | right_hip | Right hip |
| 13 | left_knee | Left knee |
| 14 | right_knee | Right knee |
| 15 | left_ankle | Left ankle |
| 16 | right_ankle | Right ankle |

### Access by Name

```javascript
// Get specific keypoint by name
let nose = pose.keypoints.find(k => k.name === "nose");
console.log(nose.x, nose.y, nose.confidence);

// Or by index
let leftWrist = pose.keypoints[9];
```

---

## Skeleton Connections

Get the skeleton connections array:

```javascript
let connections = bodyPose.getSkeleton();
// Returns: [[0,1], [0,2], [1,3], [2,4], ...]
// Each pair represents indices of connected keypoints
```

Draw skeleton:

```javascript
function drawSkeleton(pose) {
  let connections = bodyPose.getSkeleton();

  for (let [indexA, indexB] of connections) {
    let pointA = pose.keypoints[indexA];
    let pointB = pose.keypoints[indexB];

    if (pointA.confidence > 0.3 && pointB.confidence > 0.3) {
      line(pointA.x, pointA.y, pointB.x, pointB.y);
    }
  }
}
```

---

## Model Options

### MoveNet (Default - Fastest)

```javascript
// Single pose (faster)
bodyPose = ml5.bodyPose("MoveNet");

// Multiple poses
bodyPose = ml5.bodyPose("MoveNet", { modelType: "MULTIPOSE_LIGHTNING" });
```

### BlazePose (3D Support)

```javascript
bodyPose = ml5.bodyPose("BlazePose");

// Access 3D keypoints
let keypoint3D = pose.keypoints3D[0];
console.log(keypoint3D.x, keypoint3D.y, keypoint3D.z);
```

---

## Confidence Threshold

Filter out low-confidence detections:

```javascript
const CONFIDENCE_THRESHOLD = 0.3;

function drawKeypoints(pose) {
  for (let keypoint of pose.keypoints) {
    if (keypoint.confidence > CONFIDENCE_THRESHOLD) {
      circle(keypoint.x, keypoint.y, 10);
    }
  }
}
```

---

## Common Patterns

### Smoothing with Lerp

Reduce jitter by interpolating positions:

```javascript
let smoothedNose = { x: 0, y: 0 };
const LERP_AMOUNT = 0.3;

function draw() {
  if (poses.length > 0) {
    let nose = poses[0].keypoints[0];
    smoothedNose.x = lerp(smoothedNose.x, nose.x, LERP_AMOUNT);
    smoothedNose.y = lerp(smoothedNose.y, nose.y, LERP_AMOUNT);
    circle(smoothedNose.x, smoothedNose.y, 20);
  }
}
```

### Calculate Distance Between Points

```javascript
function getDistance(pointA, pointB) {
  return dist(pointA.x, pointA.y, pointB.x, pointB.y);
}

// Example: distance between hands
let leftWrist = pose.keypoints[9];
let rightWrist = pose.keypoints[10];
let handDistance = getDistance(leftWrist, rightWrist);
```

### Calculate Angle

```javascript
function getAngle(pointA, pointB, pointC) {
  let angle = Math.atan2(pointC.y - pointB.y, pointC.x - pointB.x) -
              Math.atan2(pointA.y - pointB.y, pointA.x - pointB.x);
  return Math.abs(angle * 180 / Math.PI);
}

// Example: elbow angle
let shoulder = pose.keypoints[5];
let elbow = pose.keypoints[7];
let wrist = pose.keypoints[9];
let elbowAngle = getAngle(shoulder, elbow, wrist);
```

### Multi-Person Tracking

```javascript
function draw() {
  let colors = ["#00FFFF", "#FFFF00", "#00FF00", "#FF6600"];

  for (let i = 0; i < poses.length; i++) {
    let color = colors[i % colors.length];
    fill(color);
    drawKeypoints(poses[i]);
  }
}
```

---

## Action Recognition (actions.js)

The `ActionRecognizer` class detects 6 actions based on body pose:

| Action | Detection Logic |
|--------|-----------------|
| **Standing** | Upright posture, legs relatively straight |
| **Sitting** | Knee angle < 120°, hips below shoulders |
| **Squatting** | Knee angle < 90°, hips lowered |
| **T-Pose** | Arms extended horizontally at shoulder level |
| **Jumping/Arms Up** | Both wrists above nose level |
| **Waving** | Hand near head + side-to-side motion |

### Using ActionRecognizer

```javascript
// Create instance
let actionRecognizer = new ActionRecognizer();

// In draw loop
if (poses.length > 0) {
  let result = actionRecognizer.recognize(poses[0]);
  console.log(result.action);      // "Standing", "Sitting", etc.
  console.log(result.confidence);  // 0.0 - 1.0
  console.log(result.allActions);  // All detection results
}
```

### Individual Detection Methods

```javascript
// Convert keypoints to named object
let named = actionRecognizer.getNamedKeypoints(pose.keypoints);

// Check specific actions
let sitting = actionRecognizer.detectSitting(named);
// Returns: { detected: true/false, confidence: 0.0-1.0 }

let tpose = actionRecognizer.detectTPose(named);
let squatting = actionRecognizer.detectSquatting(named);
let standing = actionRecognizer.detectStanding(named);
let jumping = actionRecognizer.detectJumping(named);
let waving = actionRecognizer.detectWaving(named);
```

### Helper Methods

```javascript
// Calculate angle between three points (degrees)
let angle = actionRecognizer.calculateAngle(pointA, pointB, pointC);

// Calculate distance between two points
let dist = actionRecognizer.calculateDistance(pointA, pointB);

// Check confidence threshold
let isValid = actionRecognizer.isConfident(keypoint, 0.3);
```

---

## Simple Action Detection (without class)

### Hands Raised

```javascript
function areHandsRaised(pose) {
  let nose = pose.keypoints[0];
  let leftWrist = pose.keypoints[9];
  let rightWrist = pose.keypoints[10];

  return leftWrist.y < nose.y && rightWrist.y < nose.y;
}
```

### T-Pose

```javascript
function isTpose(pose) {
  let leftShoulder = pose.keypoints[5];
  let rightShoulder = pose.keypoints[6];
  let leftWrist = pose.keypoints[9];
  let rightWrist = pose.keypoints[10];

  // Wrists roughly at shoulder height (within 50px)
  let leftLevel = Math.abs(leftWrist.y - leftShoulder.y) < 50;
  let rightLevel = Math.abs(rightWrist.y - rightShoulder.y) < 50;

  // Arms extended outward
  let leftExtended = leftWrist.x < leftShoulder.x;
  let rightExtended = rightWrist.x > rightShoulder.x;

  return leftLevel && rightLevel && leftExtended && rightExtended;
}
```

---

## Video File Input

Use a video file instead of camera:

```javascript
let video;

function setup() {
  createCanvas(640, 480);

  // Load video file
  video = createVideo("path/to/video.mp4", videoLoaded);
  video.hide();
}

function videoLoaded() {
  video.loop();
  video.volume(0);
  bodyPose.detectStart(video, gotPoses);
}
```

---

## Troubleshooting

### Camera Not Working

- Check browser permissions for camera access
- Ensure HTTPS or localhost (camera requires secure context)
- Try a different browser

### Low FPS

- Use `MoveNet` instead of `BlazePose`
- Reduce canvas size
- Check if other tabs are using camera

### Poses Not Detected

- Ensure good lighting
- Stand further from camera (full body visible)
- Avoid busy backgrounds

### Model Not Loading

- Check internet connection (CDN required)
- Verify ml5.js version compatibility
- Check browser console for errors

---

## Resources

- [ml5.js Documentation](https://docs.ml5js.org/)
- [ml5.js BodyPose](https://docs.ml5js.org/#/reference/bodypose)
- [p5.js Reference](https://p5js.org/reference/)
- [MoveNet Paper](https://blog.tensorflow.org/2021/05/next-generation-pose-detection-with-movenet-and-tensorflowjs.html)

---

## License

MIT
