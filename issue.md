# Issue: Pose Visualization Not Working in record.html

## Problem Statement

The `frontend/record.html` page displays a webcam feed during recording sessions but **does not show skeleton/keypoint overlay** for pose detection, unlike the working implementation in `archived/ml5-simple/` which successfully displays pose visualization.

### Expected Behavior
When recording, the video feed should display:
- Cyan lines connecting body joints (skeleton)
- Magenta circles at each detected keypoint (17 body points)
- Real-time pose tracking as the user moves

### Actual Behavior
- Video feed displays correctly
- No skeleton or keypoints visible
- Activity detection shows "Waiting..." or relies only on sensor data
- No visual feedback of pose detection

---

## Screenshots

### Working Implementation (ml5-simple)
![ml5-simple working](archived/ml5-simple screenshot shows skeleton and keypoints on video)
- Shows cyan skeleton lines
- Shows magenta keypoint circles
- Displays detected action label
- FPS counter visible

### Broken Implementation (record.html)
![record.html broken](frontend/record.html shows only video feed, no pose overlay)
- Only shows raw video feed
- No skeleton visualization
- No keypoint circles
- Activity detection relies on sensors only

---