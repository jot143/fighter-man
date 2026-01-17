# ML5 API Usage Differences Analysis

## Summary

The broken implementation fails because:
1. **ml5.bodyPose() returns a Promise** that must be awaited
2. **Video element type mismatch** - HTMLVideoElement vs p5.Renderer
3. **No model ready confirmation** - arbitrary 500ms wait instead of callback

## Critical Finding: ml5 v1 Returns Promise

**WORKING (ml5-simple with p5.js):**
```javascript
function preload() {
  bodyPose = ml5.bodyPose("MoveNet");  // p5.js preload handles Promise automatically
}
```

**BROKEN (poseVisualizer.js before fix):**
```javascript
this.bodyPose = ml5.bodyPose('MoveNet');  // Stores Promise, not model!
// Then immediately calls:
this.bodyPose.detectStart(video, callback);  // ERROR: detectStart is not a function
```

**FIX APPLIED:**
```javascript
this.bodyPose = await ml5.bodyPose('MoveNet');  // Await to get actual model
```

## Video Element Type Difference

| Aspect | ml5-simple (Works) | record.html (Broken) |
|--------|-------------------|---------------------|
| Video source | p5.createCapture(VIDEO) | document.getElementById() |
| Video type | p5.Renderer object | HTMLVideoElement |
| Integration | Full p5.js | Vanilla JavaScript |

## Initialization Timing

**WORKING:** p5.js lifecycle guarantees order:
```
preload() → model loads completely
setup() → create canvas, start detection
draw() → continuous rendering
```

**BROKEN:** Manual timing with race conditions:
```
DOMContentLoaded → create PoseVisualizer
startRecording() → init video, init ml5 simultaneously
→ Race condition: ml5 not ready when detectStart() called
```

## Root Cause

The ml5.js v1 API is deeply integrated with p5.js. When used without p5.js:
1. Must explicitly await the Promise from ml5.bodyPose()
2. Must ensure video has actual frame data (readyState >= 2)
3. Must verify model is ready before calling detectStart()

## Fixes Applied

1. **Await the Promise:** `this.bodyPose = await ml5.bodyPose('MoveNet')`
2. **Wait for frame data:** Check `readyState >= 2` not just `>= 1`
