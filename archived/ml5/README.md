# 🤖 Real-Time Body Action Recognition

A minimal, real-time body action recognition system using **ml5.js** and **p5.js**. Detects human poses and recognizes actions from camera feed or video files.

## ✨ Features

- **Multi-person tracking** - Detect and track up to 6 people simultaneously
- **Color-coded skeletons** - Each person gets a unique color (Cyan, Yellow, Green, Orange, Pink, Purple)
- **Real-time pose detection** using MoveNet MultiPose model
- **6 detectable actions**: Waving, Jumping, T-Pose, Squatting, Sitting, Standing
- **Individual action recognition** - Each person's action detected independently
- **Dual input modes**: Live camera feed OR video file upload
- **Full skeleton visualization** with keypoints and connections
- **Confidence scoring** for detected actions per person
- **People counter** - Shows how many people are currently detected
- **Simple toggle interface** to switch between input sources
- **FPS display** for performance monitoring

## 🎯 Detectable Actions

| Action | Description | Detection Method |
|--------|-------------|------------------|
| 👋 Waving | Hand moving near head level | Hand position + movement variance |
| 🦘 Jumping / Arms Up | Both arms raised above head | Hand positions relative to head |
| 🙆 T-Pose | Arms extended horizontally | Arm alignment at shoulder level |
| 🏋️ Squatting | Deep knee bend with lowered hips | Knee angle < 90° |
| 🪑 Sitting | Bent knees with hips lower than shoulders | Knee angle + hip position |
| 🧍 Standing | Upright posture with straight legs | Body alignment and leg segments |

## 🚀 Quick Start

### Prerequisites

- A modern web browser (Chrome, Firefox, Edge, Safari)
- Webcam access (for camera mode)
- Internet connection (to load libraries from CDN)

### Installation

1. **Clone or download** this repository to your local machine

2. **Open `index.html`** in your web browser:
   ```bash
   # Option 1: Direct open
   open index.html

   # Option 2: Use a local server (recommended)
   python3 -m http.server 8000
   # Then visit: http://localhost:8000
   ```

3. **Grant camera permissions** when prompted by your browser

4. **Start detecting!** The application will automatically begin analyzing poses

## 📖 Usage

### Camera Mode (Default)

1. Open the application - camera starts automatically
2. Position yourself in front of the camera
3. Perform actions to see real-time recognition
4. Action name and confidence score appear in top-left corner

### Video File Mode

1. Click **"Switch to Video File"** button
2. Click **"Choose File"** and select a video file
3. Video will loop automatically
4. Press **Space** to pause/play the video

### Keyboard Shortcuts

- **`T`** - Toggle between Camera and Video File modes
- **`Space`** - Pause/Play video (when in video mode)

### Multi-Person Tracking

The system automatically detects and tracks multiple people:

1. **Up to 6 people** can be detected simultaneously
2. **Each person gets a unique color**:
   - Person 1: Cyan (light blue)
   - Person 2: Yellow
   - Person 3: Green
   - Person 4: Orange
   - Person 5: Pink
   - Person 6: Purple

3. **Individual action labels** appear above each person's head showing:
   - Person number
   - Detected action
   - Confidence percentage

4. **People counter** in bottom-right shows: "Detecting X people"

5. **Best practices for multi-person tracking**:
   - Ensure all people are fully visible in frame
   - Stand at different positions to avoid overlap
   - Good lighting helps improve detection accuracy
   - More people = slightly lower FPS (still 30-50 FPS with 2-3 people)

## 📁 Project Structure

```
ml5/
├── index.html          # Main HTML page with UI
├── sketch.js           # p5.js sketch with pose detection
├── actions.js          # Action recognition logic
├── README.md           # This file
└── documentation/      # Tutorial examples (1.js - 6.js)
```

## 🔧 Technical Details

### Architecture

The system consists of three main components:

1. **index.html**
   - Loads p5.js and ml5.js libraries from CDN
   - Provides UI structure and styling
   - Displays action list and instructions

2. **sketch.js**
   - Handles video input (camera/file)
   - Runs MoveNet pose detection
   - Draws skeleton and keypoints
   - Manages UI elements and interactions

3. **actions.js**
   - `ActionRecognizer` class with detection algorithms
   - Analyzes pose keypoints for patterns
   - Calculates angles, distances, and movements
   - Returns detected action with confidence score

### Pose Detection

- **Model**: MoveNet (MultiPose Lightning)
- **Multi-person support**: Detects up to 6 people simultaneously
- **Keypoints**: 17 body landmarks detected per person
- **Confidence threshold**: 0.3 (30%)
- **Frame rate**: ~30-60 FPS with multiple people (depends on hardware)
- **Color coding**: Each person gets a unique color for easy identification

### Action Recognition Algorithm

Each action uses a rule-based detection system:

```javascript
// Example: Waving detection
1. Check if hand is near head level
2. Track hand position history (last 10 frames)
3. Calculate horizontal movement variance
4. If variance > threshold → "Waving" detected
```

## 🎨 Customization

### Adjust Confidence Thresholds

Edit `actions.js` to modify detection sensitivity:

```javascript
// Change from 0.3 to your preferred value
isConfident(keypoint, threshold = 0.3) {
  return keypoint && keypoint.confidence > threshold;
}
```

### Add New Actions

Add a new detection method in `ActionRecognizer` class:

```javascript
detectMyAction(pose) {
  // Your detection logic here
  if (/* condition */) {
    return { detected: true, confidence: 0.85 };
  }
  return { detected: false, confidence: 0 };
}

// Add to recognize() method
"My Action": this.detectMyAction(pose),
```

### Change Canvas Size

Modify `sketch.js`:

```javascript
function setup() {
  createCanvas(1280, 720); // Change dimensions
  // ...
}
```

## 🐛 Troubleshooting

### Camera Not Working

- Check browser permissions for camera access
- Try a different browser (Chrome recommended)
- Ensure no other application is using the camera

### Video File Not Loading

- Supported formats: MP4, WebM, OGG
- Check browser console (F12) for error messages
- Try a different video file or format

### Slow Performance

- Close other browser tabs
- Try a smaller video resolution
- Switch to MoveNet Lightning model (already default)
- Check hardware acceleration is enabled

### No Pose Detected

- Ensure full body is visible in frame
- Improve lighting conditions
- Stand further from camera
- Check if model loaded successfully (console message)

## 🧪 Testing the Actions

### Waving
- Raise your right hand near your head
- Move it side-to-side continuously

### Jumping / Arms Up
- Raise both hands above your head
- Keep them elevated

### T-Pose
- Extend both arms horizontally at shoulder level
- Form a "T" shape with your body

### Squatting
- Bend knees deeply (< 90° angle)
- Lower hips close to knee level

### Sitting
- Sit on a chair with knees bent
- Keep back relatively upright

### Standing
- Stand upright with legs relatively straight
- Maintain natural posture

## 📚 Resources

- [ml5.js Documentation](https://docs.ml5js.org/)
- [p5.js Reference](https://p5js.org/reference/)
- [MoveNet Model](https://www.tensorflow.org/hub/tutorials/movenet)
- [The Coding Train Tutorials](https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/7-bodypose/pose-detection)

## 🤝 Contributing

Feel free to:
- Add new action detection algorithms
- Improve detection accuracy
- Add more visualization options
- Optimize performance
- Report bugs or suggest features

## 📝 License

This project is open source and available for educational purposes.

## 🙏 Acknowledgments

- **ml5.js** - Friendly machine learning library
- **p5.js** - Creative coding framework
- **TensorFlow.js** - MoveNet model
- **The Coding Train** - Tutorial inspiration

---

Made with ❤️ using ml5.js and p5.js
