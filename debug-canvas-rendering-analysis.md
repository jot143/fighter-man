# Canvas Rendering Analysis: ml5-simple vs poseVisualizer

## Executive Summary
The `poseVisualizer.js` uses native Canvas 2D API with potential coordinate system and scaling mismatches compared to the working `ml5-simple` implementation which uses p5.js. Key issues involve canvas dimensions, video coordinate mapping, and context setup.

---

## 1. Canvas Framework Differences

### ml5-simple/sketch.js (WORKING - p5.js)
```javascript
// p5.js handles canvas creation automatically
function setup() {
    let canvas = createCanvas(640, 480);  // Creates canvas automatically
    canvas.parent("canvas-container");
    video = createCapture(VIDEO);         // p5.js wrapper for video
    video.size(640, 480);
}

function draw() {
    image(video, 0, 0, width, height);    // p5.js handles rendering
    // All drawing uses p5.js high-level API
    circle(x, y, size);                   // Automatic coordinate mapping
    line(x1, y1, x2, y2);                 // Automatic coordinate mapping
}
```

**Key Advantages:**
- p5.js manages coordinate system uniformly
- Canvas size and video size are explicitly controlled (640x480)
- No manual context management
- Built-in transformation and scaling

### poseVisualizer.js (NATIVE Canvas 2D)
```javascript
// Manual canvas setup
this.ctx = this.canvas.getContext('2d');

// Canvas dimensions based on VIDEO DISPLAY SIZE (CSS-affected)
const rect = this.video.getBoundingClientRect();
this.canvas.width = rect.width;
this.canvas.height = rect.height;

// Manual drawing
this.ctx.fillRect(10, 10, 100, 50);
this.ctx.beginPath();
this.ctx.arc(x, y, radius, 0, Math.PI * 2);
this.ctx.fill();
```

**Key Issues:**
- Canvas size depends on CSS display size, not video source size
- Manual context management required
- Coordinate system not automatically scaled
- More prone to mismatch errors

---

## 2. Canvas Dimensions Issues

### Problem: Width/Height Attribute vs CSS Size

#### record.html CSS Setup
```css
#video-container {
    position: relative;
    max-width: 640px;
    max-height: 480px;
    margin: 0 auto 2rem;
}

#video-preview {
    width: 100%;
    height: auto;
    border-radius: 8px;
    background: #000;
    transform: scaleX(-1);  /* Mirror effect */
}

#pose-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
```

#### What poseVisualizer Does (Line 164-165)
```javascript
this.canvas.width = rect.width;      // CSS display width
this.canvas.height = rect.height;    // CSS display height
```

### Issue 1: CSS Transform Scaling
- Video has `transform: scaleX(-1)` for mirroring
- getBoundingClientRect() returns **visual** dimensions, NOT affected by CSS transform
- Canvas is set to visual size, but transform might affect rendering

### Issue 2: Responsive Sizing
- If video container is responsive (width: 100%), actual canvas size depends on parent
- Canvas dimensions might not match 640x480
- Could be 320x240 or other sizes depending on viewport

### Issue 3: Canvas Resolution vs Display Size
**CRITICAL ISSUE:**
```
Video Source Resolution: ~256x256 (MoveNet input)
Video Display Size: ~640x480 (in HTML)
Canvas Attribute (width/height): getBoundingClientRect() size
Canvas CSS (width: 100%): Might override canvas attributes!
```

When you set `canvas.width` and `canvas.height` properties (NOT CSS), they define:
1. The actual drawing surface resolution
2. The coordinate system bounds (0,0 to width,height)

If CSS also sets width/height, the canvas gets **stretched/scaled** to fit CSS dimensions.

---

## 3. Coordinate System and Scaling Analysis

### How ml5 Reports Coordinates
```javascript
// ml5.bodyPose returns keypoints in VIDEO SOURCE coordinates
pose.keypoints[i] = {
    x: 128,      // 0-256 (or native video width)
    y: 64,       // 0-256 (or native video height)
    confidence: 0.95
}
```

### poseVisualizer Scaling (Lines 369-374)
```javascript
scaleCoordinates(x, y) {
    return {
        x: x * this.scaleX,
        y: y * this.scaleY
    };
}

// Scale factors calculated (Lines 170-171)
this.scaleX = rect.width / videoWidth;
this.scaleY = rect.height / videoHeight;
```

### Potential Problems

**Problem A: Video Not Ready**
- Line 82-101 waits for video metadata
- But if video hasn't started playing, `videoWidth` and `videoHeight` might still be 0
- This results in scaleX = Infinity, scaleY = Infinity
- Coordinates become NaN or very large

**Problem B: getBoundingClientRect() Issues**
```javascript
const rect = this.video.getBoundingClientRect();
// rect includes padding, margin, border calculations
// Might not match actual canvas display size
```

**Problem C: Dynamic Resizing**
- Lines 237-243 check for size changes every frame
- But if dimensions change mid-stream, scale factors recalculated
- Might cause jumpiness or missed frames

---

## 4. Canvas Context Setup Verification

### What's Done Correctly
```javascript
// Line 72: Get 2D context
this.ctx = this.canvas.getContext('2d');

// Lines 307-309: Draw skeleton
this.ctx.strokeStyle = this.config.skeletonColor;  // '#00ffff'
this.ctx.lineWidth = this.config.skeletonWidth;    // 3
this.ctx.lineCap = 'round';

// Lines 347: Draw keypoints
this.ctx.fillStyle = this.config.keypointColor;    // '#ff00ff'
```

### What Might Be Missing
```javascript
// Before drawing, should clear with video or proper background
this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
// This is done (line 234), but no video drawn underneath

// Canvas doesn't draw the video - just poses on transparent background
// This is fine if CSS layers work, but...
```

### Canvas Layering Issue
record.html has canvas absolutely positioned over video:
```html
<video id="video-preview"></video>
<canvas id="pose-canvas"></canvas>
```

CSS makes canvas overlap video, which should work. But if:
1. Canvas context isn't cleared properly
2. Video hasn't loaded when canvas draws
3. Z-index issues occur

Then canvas renders but content is invisible.

---

## 5. Drawing Commands Analysis

### Test Rectangle (Lines 254-261) - Verification Method
```javascript
if (this.frameCount < 120) {
    this.ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    this.ctx.fillRect(10, 10, 100, 50);
    this.ctx.fillStyle = 'white';
    this.ctx.font = '14px Arial';
    this.ctx.fillText('Canvas OK', 20, 40);
}
```

**This is good for debugging:** If you see "Canvas OK" in red box for 2 seconds, canvas is working.

### Skeleton Drawing (Lines 323-326)
```javascript
this.ctx.beginPath();
this.ctx.moveTo(scaledA.x, scaledA.y);
this.ctx.lineTo(scaledB.x, scaledB.y);
this.ctx.stroke();  // This IS being called
```

**This looks correct**, but if scaledA/scaledB are NaN (from infinity scale), nothing draws.

### Keypoint Drawing (Lines 354-356)
```javascript
this.ctx.beginPath();
this.ctx.arc(scaled.x, scaled.y, this.config.keypointRadius, 0, Math.PI * 2);
this.ctx.fill();
```

**This looks correct** if scaled coordinates are valid.

---

## 6. Actual Issues Summary

### Critical Issues

| Issue | Severity | Impact | Location |
|-------|----------|--------|----------|
| Canvas width/height set from CSS display size, not video source | HIGH | Coordinate mismatch if responsive | Line 164-165 |
| scaleX/scaleY calculated with videoWidth/videoHeight that may be 0 | HIGH | Scale factors become Infinity | Lines 170-171 |
| Canvas CSS width: 100% might override width/height attributes | HIGH | Canvas stretched/distorted | record.html CSS |
| No video background drawn on canvas | MEDIUM | Only skeleton visible (might look empty) | N/A - by design |
| Dynamic resize check happens every frame | LOW | Minor performance/stability impact | Lines 237-243 |

### How ml5-simple Avoids These

1. **Fixed dimensions**: `createCanvas(640, 480)` - always 640x480
2. **Consistent video size**: `video.size(640, 480)` - always 640x480
3. **Direct p5.js drawing**: No manual scaling needed, p5.js handles it
4. **Video drawn on canvas**: `image(video, 0, 0, width, height)` - background included
5. **Single coordinate system**: Everything in 640x480, no scaling math needed

---

## 7. Specific Rendering Fixes to Try

### Fix 1: Ensure Canvas Has Proper Width/Height Attributes
```javascript
updateCanvasDimensions() {
    const videoWidth = this.video.videoWidth;
    const videoHeight = this.video.videoHeight;
    
    // IMPORTANT: Use video dimensions, not display dimensions
    // or use a fixed size matching the video display
    
    // Option A: Match video native resolution (recommended)
    this.canvas.width = videoWidth;
    this.canvas.height = videoHeight;
    
    // Then scale in CSS if needed:
    // this.canvas.style.width = rect.width + 'px';
    // this.canvas.style.height = rect.height + 'px';
    
    // Scale factors remain 1:1 if no CSS scaling
    this.scaleX = 1;
    this.scaleY = 1;
}
```

### Fix 2: Validate Scale Factors
```javascript
startDetection() {
    // Add validation after setting scale factors
    if (!isFinite(this.scaleX) || !isFinite(this.scaleY)) {
        console.warn('[PoseVisualizer] Invalid scale factors, resetting to 1:1');
        this.scaleX = 1;
        this.scaleY = 1;
    }
    
    if (this.scaleX <= 0 || this.scaleY <= 0) {
        console.warn('[PoseVisualizer] Scale factors <= 0, resetting to 1:1');
        this.scaleX = 1;
        this.scaleY = 1;
    }
}
```

### Fix 3: Draw Video on Canvas
```javascript
draw() {
    // First, draw the video as background
    if (this.video && this.video.readyState === this.video.HAVE_FUTURE_DATA) {
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
    } else {
        // Clear canvas if no video
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    // Then draw poses on top
    for (const pose of this.poses) {
        this.drawSkeleton(pose);
        this.drawKeypoints(pose);
    }
}
```

### Fix 4: Add Safe Coordinate Checking
```javascript
drawSkeleton(pose) {
    // ... existing code ...
    
    for (const connection of connections) {
        const pointA = pose.keypoints[connection[0]];
        const pointB = pose.keypoints[connection[1]];
        
        if (pointA && pointB &&
            pointA.confidence > this.config.confidenceThreshold &&
            pointB.confidence > this.config.confidenceThreshold) {
            
            const scaledA = this.scaleCoordinates(pointA.x, pointA.y);
            const scaledB = this.scaleCoordinates(pointB.x, pointB.y);
            
            // VALIDATE: Check for NaN or out-of-bounds
            if (!isFinite(scaledA.x) || !isFinite(scaledA.y) ||
                !isFinite(scaledB.x) || !isFinite(scaledB.y)) {
                console.warn('[PoseVisualizer] Invalid scaled coordinates');
                continue;
            }
            
            if (scaledA.x < 0 || scaledA.y < 0 || 
                scaledA.x > this.canvas.width || scaledA.y > this.canvas.height ||
                scaledB.x < 0 || scaledB.y < 0 ||
                scaledB.x > this.canvas.width || scaledB.y > this.canvas.height) {
                if (this.frameCount % 60 === 0) {
                    console.warn('[PoseVisualizer] Coordinates out of bounds');
                }
                continue;
            }
            
            this.ctx.beginPath();
            this.ctx.moveTo(scaledA.x, scaledA.y);
            this.ctx.lineTo(scaledB.x, scaledB.y);
            this.ctx.stroke();
            drawnLines++;
        }
    }
}
```

### Fix 5: Remove CSS Override of Canvas Size
In record.html, change:
```css
/* OLD - causes stretching */
#pose-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

/* NEW - let canvas attributes control size */
#pose-canvas {
    position: absolute;
    top: 0;
    left: 0;
    /* Remove width: 100%; height: 100%; */
    display: block;
    /* Use image-rendering for crisp pixels if needed */
    image-rendering: pixelated;
}
```

---

## 8. Debugging Checklist

To verify which fix works:

1. **Test the test rectangle** (Lines 254-261)
   - Does "Canvas OK" appear in red box first 2 seconds?
   - If YES: Canvas is initialized and rendering
   - If NO: Canvas not being rendered at all

2. **Check console logs**
   - Look for "[PoseVisualizer] Canvas dimensions set to: X x Y"
   - Look for "[PoseVisualizer] Scale factors: X x Y"
   - Look for "NaN" in any numbers

3. **Add temporary test**
   ```javascript
   if (this.frameCount === 1) {
       console.log('Canvas properties:');
       console.log('  - canvas.width:', this.canvas.width);
       console.log('  - canvas.height:', this.canvas.height);
       console.log('  - canvas.style.width:', this.canvas.style.width);
       console.log('  - canvas.style.height:', this.canvas.style.height);
       console.log('  - computed style width:', window.getComputedStyle(this.canvas).width);
       console.log('  - computed style height:', window.getComputedStyle(this.canvas).height);
   }
   ```

4. **Check video readiness**
   - Is `video.readyState >= 1` (HAVE_CURRENT_DATA)?
   - Are `videoWidth` and `videoHeight` > 0?

5. **Verify pose detection**
   - Are poses being detected? Check console for "Pose detection callback - poses detected: X"
   - Are pose coordinates reasonable (0-256 for MoveNet)?

6. **Test with ml5-simple first**
   - Verify ml5.bodyPose works in your environment
   - Verify browser supports canvas
   - Verify WebGL/tensor backend works

---

## 9. Root Cause Analysis

### Why ml5-simple Works
1. p5.js abstracts away canvas complexity
2. Fixed 640x480 resolution everywhere
3. Everything uses same coordinate system
4. No scaling math needed
5. Video drawn directly on canvas

### Why poseVisualizer Might Not Work
1. **Most likely**: Canvas attributes vs CSS width/height conflict
   - Canvas width/height set to display size (line 164-165)
   - But record.html CSS might have width: 100% on canvas
   - Result: Canvas drawn at one size, content scaled to another

2. **Second most likely**: Invalid scale factors from videoWidth=0
   - If video hasn't loaded when scale factors calculated
   - scaleX and scaleY become Infinity
   - Coordinates become NaN
   - Nothing renders

3. **Third most likely**: Canvas cleared but video not drawn
   - Canvas is transparent with just pose skeleton
   - User expects to see video underneath (but CSS layering should handle this)
   - If z-index issues, canvas appears empty

---

## 10. Recommended Priority Fixes

### Immediate (Highest Priority)
1. **Fix #5**: Remove CSS width/height on canvas
2. **Fix #1**: Change canvas size to video native resolution (not display rect)
3. **Fix #2**: Add validation for scale factors

### Short-term
4. **Fix #4**: Add NaN and bounds checking to drawing functions
5. **Fix #3**: Draw video background on canvas (if needed)

### Testing
6. Check test rectangle renders
7. Verify scale factors are finite and reasonable
8. Confirm video dimensions are being read correctly

---

## 11. Code Locations Reference

| Issue | File | Line(s) |
|-------|------|---------|
| Canvas width set to display size | poseVisualizer.js | 164-165 |
| Scale factors calculated | poseVisualizer.js | 170-171 |
| Drawing skeleton lines | poseVisualizer.js | 323-326 |
| Drawing keypoint circles | poseVisualizer.js | 354-356 |
| Test rectangle (for debugging) | poseVisualizer.js | 254-261 |
| Canvas CSS with width: 100% | record.html | 56-66 |
| Canvas initialization call | record.html | 888 |

---

## Conclusion

The poseVisualizer.js implementation is functionally sound in its approach, but likely has **canvas dimension/scaling mismatches** preventing proper rendering. The most common issue is that the canvas width/height attributes don't match the CSS dimensions, causing the drawing surface to be scaled incorrectly.

Implement Fix #1 and Fix #5 first, verify with the test rectangle, then add validation checks from Fix #2 and #4.
