# Progressive Learning Examples

These examples build upon each other, teaching ml5 pose detection step by step.

## How to Use

Replace the main `sketch.js` with any example file to try it:

```bash
cp docs/1-minimal.js sketch.js
```

Or reference them in `index.html`:

```html
<script src="docs/1-minimal.js"></script>
```

---

## Examples

### 1. Minimal (`1-minimal.js`)

**Concepts:** Basic setup, single keypoint tracking

The simplest possible implementation. Just tracks the nose position.

```javascript
// Core pattern
let nose = poses[0].keypoints[0];
circle(nose.x, nose.y, 30);
```

---

### 2. All Keypoints (`2-all-keypoints.js`)

**Concepts:** Looping through keypoints, confidence filtering

Draws all 17 body keypoints with their names.

```javascript
for (let keypoint of pose.keypoints) {
  if (keypoint.confidence > 0.3) {
    circle(keypoint.x, keypoint.y, 10);
  }
}
```

---

### 3. Skeleton (`3-skeleton.js`)

**Concepts:** Drawing connections, getSkeleton()

Adds skeleton lines between connected keypoints.

```javascript
let connections = bodyPose.getSkeleton();
for (let [indexA, indexB] of connections) {
  line(pointA.x, pointA.y, pointB.x, pointB.y);
}
```

---

### 4. Smoothing (`4-smoothing.js`)

**Concepts:** Linear interpolation, reducing jitter

Uses `lerp()` to smooth movement and reduce jitter.

```javascript
smoothedX = lerp(smoothedX, keypoint.x, 0.3);
```

---

### 5. Actions (`5-actions.js`)

**Concepts:** Gesture detection, coordinate comparison

Detects poses like T-Pose and hands raised.

```javascript
// Hands raised: wrists above nose
if (leftWrist.y < nose.y && rightWrist.y < nose.y) {
  return "Hands Raised!";
}
```

---

### 6. Multi-Person (`6-multi-person.js`)

**Concepts:** MULTIPOSE model, tracking multiple people

Tracks up to 6 people with unique colors.

```javascript
bodyPose = ml5.bodyPose("MoveNet", {
  modelType: "MULTIPOSE_LIGHTNING"
});
```

---

## Learning Path

| Step | Example | What You'll Learn |
|------|---------|-------------------|
| 1 | Minimal | Setup, preload, gotPoses callback |
| 2 | Keypoints | Keypoint structure, confidence |
| 3 | Skeleton | Connection pairs, line drawing |
| 4 | Smoothing | Lerp interpolation, state storage |
| 5 | Actions | Coordinate math, gesture logic |
| 6 | Multi-Person | Model options, multi-tracking |

---

## Next Steps

After completing these examples, try:

1. **Add more actions** - Squatting, jumping, waving
2. **Use BlazePose** - For 3D keypoints (`keypoints3D`)
3. **Add visual effects** - Attach images/shapes to keypoints
4. **Send data** - WebSocket to send pose data to server
5. **Record poses** - Save keypoint data to JSON
