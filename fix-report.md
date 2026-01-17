# Pose Visualization Fix Report

**Issue:** Skeleton/keypoint overlay not displaying on video feed in `record.html`
**Branch:** `feature/record-pose-visualization`
**Date:** 2026-01-17
**Status:** RESOLVED

---

## Executive Summary

The pose detection skeleton and keypoint visualization was not appearing on the video feed in `frontend/record.html` during recording sessions. After multiple debugging attempts over several days, the root cause was identified as an **architectural mismatch** between how the original code handled video/canvas rendering versus how the working reference implementation (`archived/ml5-simple/`) approached the problem.

The fix involved replacing the canvas overlay approach with a **p5.js-based single-canvas implementation** that draws both video and skeleton on the same canvas, matching the working reference implementation.

---

## Problem Analysis

### Symptom
- Video feed displayed correctly during recording
- No skeleton lines or keypoint circles visible
- Activity detection showed "Waiting..." or only used sensor data
- Console showed poses being detected (`Poses: 0` or `Poses: 1`) but no visual output

### Root Causes Identified

| Issue | Description | Impact |
|-------|-------------|--------|
| **Canvas Overlay Approach** | Original poseVisualizer.js used a separate canvas overlaid on the video element | CSS transform conflicts, z-index issues, coordinate mismatches |
| **Video readyState Check** | Waited for `readyState >= 1` (HAVE_METADATA) instead of `>= 2` (HAVE_CURRENT_DATA) | ml5 received video with no actual frame pixels |
| **CSS Transform Conflicts** | Video used `transform: scaleX(-1)` for mirroring, canvas coordinates were inverted | Skeleton drawn off-screen or inverted |
| **Async/Promise API Mismatch** | Used `await ml5.bodyPose()` which behaved differently than callback pattern | Model initialization timing issues |

### Why Previous Fixes Failed

1. **Canvas overlay positioning** - Attempted CSS fixes (z-index, position absolute) didn't solve coordinate transformation issues
2. **Coordinate inversion** - Fixed X coordinates for mirroring, but skeleton still invisible
3. **Debug rectangles** - Added visible debug borders that appeared, proving canvas was rendered but skeleton wasn't
4. **readyState fixes** - Changed to wait for readyState >= 2, still failed due to architectural issues

---

## Solution: p5.js Single-Canvas Approach

### Key Insight

The working `archived/ml5-simple/sketch.js` implementation uses **p5.js to draw EVERYTHING on ONE canvas**:
- Video frame is drawn with `image(video, 0, 0)`
- Skeleton is drawn with `line()` calls
- Keypoints are drawn with `circle()` calls

This eliminates ALL coordinate transformation issues because everything uses the same coordinate system.

### Implementation

Created new file `frontend/js/poseSketch.js` (288 lines) that:
1. Uses p5.js **instance mode** to avoid global conflicts
2. Creates video capture with `p.createCapture(p.VIDEO)`
3. Loads ml5 model using **callback pattern** (not Promise)
4. Draws video and skeleton on same canvas in the draw loop
5. Provides `getCanvasStream()` method for MediaRecorder

### Critical Code Change

**Before (broken - async/await pattern):**
```javascript
// poseVisualizer.js approach
bodyPose = await ml5.bodyPose('MoveNet');
bodyPose.detectStart(video, gotPoses);
```

**After (working - callback pattern):**
```javascript
// poseSketch.js approach - matches working ml5-simple
bodyPose = ml5.bodyPose('MoveNet', function() {
    console.log('[PoseSketch] ml5.bodyPose model loaded via callback');
    bodyPose.detectStart(video, gotPoses);
});
```

---

## Files Changed

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/js/poseSketch.js` | 288 | p5.js-based pose detection with skeleton visualization |
| `frontend/js/poseVisualizer.js` | 555 | Original failed attempt (canvas overlay approach) - kept for reference |

### Modified Files

| File | Insertions | Deletions | Net Change |
|------|-----------|-----------|------------|
| `frontend/record.html` | +54 | -26 | +28 lines |

### record.html Changes Summary

```diff
+ Added p5.js library (CDN)
+ Added ml5.js library (CDN)
+ Added poseSketch.js script
- Removed <video id="video-preview"> element
+ p5.js creates canvas dynamically in #video-container
- Removed videoRecorder.init('video-preview') call
+ Added poseSketch = createPoseSketch('video-container', {...})
+ Added canvasStream = await poseSketch.getCanvasStream()
+ Added poseSketch.stop() cleanup on recording stop
```

---

## Architecture Comparison

### Old Architecture (Broken)

```
┌─────────────────────────────────┐
│     #video-container            │
│  ┌───────────────────────────┐  │
│  │  <video id="video-preview">│  │  ← Video with CSS transform: scaleX(-1)
│  │  (getUserMedia stream)     │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  <canvas id="pose-overlay">│  │  ← Canvas overlay (position: absolute)
│  │  (skeleton drawn here)     │  │    Coordinate mismatch!
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
    MediaRecorder records video only (no skeleton)
```

### New Architecture (Working)

```
┌─────────────────────────────────┐
│     #video-container            │
│  ┌───────────────────────────┐  │
│  │  <canvas> (p5.js created)  │  │  ← Single canvas
│  │  - Video drawn with image()│  │
│  │  - Skeleton drawn with line│  │    Same coordinate system!
│  │  - Keypoints drawn w/circle│  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
    canvas.captureStream(30) → MediaRecorder
    Records video WITH skeleton overlay!
```

---

## Working Reference: ml5-simple

The solution was modeled after `archived/ml5-simple/sketch.js` (146 lines):

```javascript
// preload() - Load model BEFORE setup
function preload() {
  bodyPose = ml5.bodyPose("MoveNet");  // No await!
}

// setup() - Create video, start detection
function setup() {
  createCanvas(640, 480);
  video = createCapture(VIDEO);
  video.hide();
  bodyPose.detectStart(video, gotPoses);
}

// draw() - Render everything on same canvas
function draw() {
  image(video, 0, 0);      // Draw video
  drawSkeleton(pose);       // Draw skeleton
  drawKeypoints(pose);      // Draw keypoints
}
```

---

## Verification

### Console Output (Working)
```
[PoseSketch] Creating p5 instance in container: video-container
[PoseSketch] Setup starting...
[PoseSketch] Canvas created: 640 x 480
[PoseSketch] Video capture ready, now loading ml5...
[PoseSketch] Loading ml5.bodyPose...
[PoseSketch] ml5.bodyPose model loaded via callback
[PoseSketch] Video element: <video ...>
[PoseSketch] Video readyState: 4
[PoseSketch] Video dimensions: 640 x 480
[PoseSketch] Pose detection started
[PoseSketch] Canvas ready, creating stream...
[Video] Got canvas stream with skeleton overlay
[Video] Recording started with skeleton overlay
```

### Visual Confirmation
- Cyan skeleton lines connecting body joints: ✅
- Magenta keypoint circles at 17 body points: ✅
- Info overlay showing "Poses: 1 | FPS: 61": ✅
- Mirrored display (selfie mode): ✅
- Recorded video includes skeleton overlay: ✅

---

## Debug Files Created

The following debug analysis files were created during investigation:

| File | Purpose |
|------|---------|
| `debug-canvas-rendering-analysis.md` | Canvas coordinate and CSS transform analysis |
| `debug-css-analysis.md` | CSS z-index and positioning issues |
| `debug-loading-timing-analysis.md` | ml5 model loading race conditions |
| `debug-ml5-api-analysis.md` | Promise vs callback API differences |
| `debug-video-element-analysis.md` | Video readyState requirements |
| `issue.md` | Original issue description |

---

## Lessons Learned

1. **Match the working reference** - When something works elsewhere, replicate the exact approach rather than trying to adapt a different architecture
2. **Single canvas > overlay** - Drawing everything on one canvas eliminates coordinate system mismatches
3. **Callback vs Promise** - ml5.js behaves more reliably with callback pattern for model loading
4. **p5.js instance mode** - Essential for avoiding global conflicts when integrating with existing applications
5. **Video readyState** - Must be >= 2 (HAVE_CURRENT_DATA) for ml5 to read actual pixel data

---

## Recommendations

1. **Remove poseVisualizer.js** - The canvas overlay approach is abandoned; file can be deleted
2. **Clean up debug files** - The debug-*.md files can be removed after this report is reviewed
3. **Consider model caching** - ml5 model loading takes 2-3 seconds; consider preloading
4. **Test on mobile** - p5.js and ml5 may behave differently on mobile browsers

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Days spent debugging | Multiple |
| Failed approaches tried | 5+ |
| New files created | 2 |
| Lines of new code | 843 (288 + 555) |
| Lines modified in record.html | 80 (+54/-26) |
| Root cause | Architecture mismatch (overlay vs single canvas) |
| Final fix | p5.js callback pattern + single canvas |
