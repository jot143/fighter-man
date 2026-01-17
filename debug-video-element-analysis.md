# Video Element Differences Analysis

## Summary

The working ml5-simple uses **p5.js createCapture()** which properly handles video frame rendering. The broken record.html uses **MediaRecorder API** which sets up the stream but doesn't ensure frames are decoded before passing to ml5.

## Critical Finding: Video readyState

**PROBLEM:** poseVisualizer.js was waiting for `readyState >= 1` (HAVE_METADATA), but ml5 needs `readyState >= 2` (HAVE_CURRENT_DATA) to have actual pixels to analyze.

**Video readyState values:**
- 0: HAVE_NOTHING - no data
- 1: HAVE_METADATA - dimensions only (NOT ENOUGH!)
- 2: HAVE_CURRENT_DATA - at least one frame (MINIMUM for ml5)
- 3: HAVE_FUTURE_DATA - next frame available
- 4: HAVE_ENOUGH_DATA - playing smoothly

**BEFORE (broken):**
```javascript
if (this.video.readyState < 1) {
    await waitFor('loadedmetadata');  // Only waits for dimensions!
}
```

**AFTER (fixed):**
```javascript
if (this.video.readyState < 2) {
    await waitFor('canplay' OR 'playing' OR 'loadeddata');  // Waits for actual frames
}
```

## Video Creation Comparison

| Aspect | ml5-simple | record.html |
|--------|-----------|-------------|
| Creation | p5.createCapture(VIDEO) | navigator.mediaDevices.getUserMedia() |
| Resolution | 640x480 | 1280x720 (ideal) |
| Rendering | Drawn to canvas via image() | Only in HTML video element |
| Frame guarantee | Yes (p5 draw loop) | No (may not be decoded) |

## Why ml5 Detection Failed

1. Video stream was attached via `srcObject`
2. `loadedmetadata` event fired (readyState = 1)
3. poseVisualizer immediately called `detectStart()`
4. But video only had metadata, NO ACTUAL FRAME PIXELS
5. ml5 tried to read frame data, got empty/black frame
6. Pose detection returned empty results: `poses = []`

## Resolution Consideration

videoRecorder.js requests 1280x720, but MoveNet is trained on ~640x480. This may cause:
- Scaling artifacts
- Coordinate mismatches
- Detection accuracy issues

Consider lowering to 640x480 for better ml5 compatibility.

## Fixes Applied

1. Wait for `readyState >= 2` instead of `>= 1`
2. Listen for multiple events: `loadeddata`, `canplay`, `playing`
3. Verify frames are available before starting detection
