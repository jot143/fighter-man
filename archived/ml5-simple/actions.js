/**
 * Action Recognition Module for ML5 Pose Detection
 * Detects human actions based on body keypoint positions and movements
 *
 * Supported Actions:
 * - Waving (side-to-side hand motion near head)
 * - Jumping / Arms Up (both hands above head)
 * - T-Pose (arms extended horizontally)
 * - Squatting (deep knee bend)
 * - Sitting (bent knees, lowered hips)
 * - Standing (upright posture)
 */

class ActionRecognizer {
  constructor() {
    // Store previous pose for movement detection
    this.previousPose = null;
    this.handHistory = [];
    this.maxHistoryLength = 10;
  }

  /**
   * Convert keypoints array to named object for easier access
   * @param {Array} keypoints - Array of 17 keypoints
   * @returns {Object} Named keypoints object
   */
  getNamedKeypoints(keypoints) {
    const names = [
      'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
      'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
      'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
      'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
    ];

    const named = {};
    for (let i = 0; i < keypoints.length; i++) {
      named[names[i]] = keypoints[i];
    }
    return named;
  }

  /**
   * Calculate angle between three points (in degrees)
   */
  calculateAngle(pointA, pointB, pointC) {
    const radians = Math.atan2(pointC.y - pointB.y, pointC.x - pointB.x) -
                    Math.atan2(pointA.y - pointB.y, pointA.x - pointB.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) {
      angle = 360 - angle;
    }
    return angle;
  }

  /**
   * Calculate distance between two points
   */
  calculateDistance(pointA, pointB) {
    return Math.sqrt(
      Math.pow(pointB.x - pointA.x, 2) +
      Math.pow(pointB.y - pointA.y, 2)
    );
  }

  /**
   * Check if keypoint has sufficient confidence
   */
  isConfident(keypoint, threshold = 0.3) {
    return keypoint && keypoint.confidence > threshold;
  }

  /**
   * Calculate variance for movement detection
   */
  calculateVariance(values) {
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    return squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
  }

  /**
   * Detect if person is waving
   * Requires: Hand near head + side-to-side motion
   */
  detectWaving(pose) {
    if (!this.isConfident(pose.right_wrist) ||
        !this.isConfident(pose.right_shoulder) ||
        !this.isConfident(pose.right_ear)) {
      return { detected: false, confidence: 0 };
    }

    // Check if hand is near head level
    const handNearHead = pose.right_wrist.y < pose.right_ear.y + 50;

    // Track hand movement history for waving motion
    this.handHistory.push({ x: pose.right_wrist.x, y: pose.right_wrist.y });
    if (this.handHistory.length > this.maxHistoryLength) {
      this.handHistory.shift();
    }

    // Calculate movement variance (waving = side-to-side motion)
    if (this.handHistory.length >= this.maxHistoryLength) {
      const xPositions = this.handHistory.map(h => h.x);
      const xVariance = this.calculateVariance(xPositions);
      const isMoving = xVariance > 500; // Movement threshold

      if (handNearHead && isMoving) {
        return { detected: true, confidence: 0.85 };
      }
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Detect if person is jumping or has arms up
   * Requires: Both hands above nose level
   */
  detectJumping(pose) {
    if (!this.isConfident(pose.left_wrist) ||
        !this.isConfident(pose.right_wrist) ||
        !this.isConfident(pose.nose)) {
      return { detected: false, confidence: 0 };
    }

    // Both hands above head
    const leftHandUp = pose.left_wrist.y < pose.nose.y;
    const rightHandUp = pose.right_wrist.y < pose.nose.y;

    if (leftHandUp && rightHandUp) {
      return { detected: true, confidence: 0.9 };
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Detect T-Pose (arms extended horizontally)
   * Requires: Arms at shoulder level, extended outward
   */
  detectTPose(pose) {
    if (!this.isConfident(pose.left_wrist) ||
        !this.isConfident(pose.right_wrist) ||
        !this.isConfident(pose.left_shoulder) ||
        !this.isConfident(pose.right_shoulder)) {
      return { detected: false, confidence: 0 };
    }

    // Arms extended at shoulder level (within 80px)
    const leftArmLevel = Math.abs(pose.left_wrist.y - pose.left_shoulder.y) < 80;
    const rightArmLevel = Math.abs(pose.right_wrist.y - pose.right_shoulder.y) < 80;

    // Arms extended outward
    const leftArmOut = pose.left_wrist.x < pose.left_shoulder.x - 50;
    const rightArmOut = pose.right_wrist.x > pose.right_shoulder.x + 50;

    if (leftArmLevel && rightArmLevel && leftArmOut && rightArmOut) {
      return { detected: true, confidence: 0.88 };
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Detect squatting position
   * Requires: Knee angle < 90° and hips lowered
   */
  detectSquatting(pose) {
    if (!this.isConfident(pose.left_hip) ||
        !this.isConfident(pose.left_knee) ||
        !this.isConfident(pose.left_ankle)) {
      return { detected: false, confidence: 0 };
    }

    // Calculate knee angle (squatting = deeply bent knees)
    const kneeAngle = this.calculateAngle(
      pose.left_hip,
      pose.left_knee,
      pose.left_ankle
    );

    // Deep squat: very acute knee angle and hips lowered
    const deepBend = kneeAngle < 90;
    const hipsLow = pose.left_hip.y > pose.left_knee.y - 50;

    if (deepBend && hipsLow) {
      return { detected: true, confidence: 0.82 };
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Detect if person is sitting
   * Requires: Knee angle < 120° and hips below shoulders
   */
  detectSitting(pose) {
    if (!this.isConfident(pose.left_hip) ||
        !this.isConfident(pose.left_knee) ||
        !this.isConfident(pose.left_ankle) ||
        !this.isConfident(pose.left_shoulder)) {
      return { detected: false, confidence: 0 };
    }

    // Calculate knee angle (sitting = bent knees)
    const kneeAngle = this.calculateAngle(
      pose.left_hip,
      pose.left_knee,
      pose.left_ankle
    );

    // Sitting: knees bent (angle < 120°) and hips lower than shoulders
    const kneeBent = kneeAngle < 120;
    const hipsLower = pose.left_hip.y > pose.left_shoulder.y;

    if (kneeBent && hipsLower) {
      return { detected: true, confidence: 0.8 };
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Detect if person is standing
   * Requires: Upright posture with legs relatively straight
   */
  detectStanding(pose) {
    if (!this.isConfident(pose.left_hip) ||
        !this.isConfident(pose.left_knee) ||
        !this.isConfident(pose.left_ankle)) {
      return { detected: false, confidence: 0 };
    }

    // Calculate body alignment (standing = relatively straight)
    const hipY = pose.left_hip.y;
    const kneeY = pose.left_knee.y;
    const ankleY = pose.left_ankle.y;

    // Check vertical alignment
    const bodyHeight = ankleY - hipY;
    const kneeToHip = kneeY - hipY;
    const kneeToAnkle = ankleY - kneeY;

    // Standing: relatively even leg segments, body upright
    const isUpright = (kneeToHip / bodyHeight) < 0.6 && kneeToAnkle > kneeToHip * 0.7;

    if (isUpright && bodyHeight > 50) {
      return { detected: true, confidence: 0.75 };
    }

    return { detected: false, confidence: 0 };
  }

  /**
   * Main recognition function - detects all actions
   * @param {Object} pose - Pose object with keypoints array
   * @returns {Object} { action, confidence, allActions }
   */
  recognize(pose) {
    if (!pose || !pose.keypoints) {
      return { action: "No pose detected", confidence: 0 };
    }

    // Convert keypoints array to named object
    const namedPose = this.getNamedKeypoints(pose.keypoints);

    // Check all actions and find the one with highest confidence
    const actions = {
      "Waving": this.detectWaving(namedPose),
      "Jumping / Arms Up": this.detectJumping(namedPose),
      "T-Pose": this.detectTPose(namedPose),
      "Squatting": this.detectSquatting(namedPose),
      "Sitting": this.detectSitting(namedPose),
      "Standing": this.detectStanding(namedPose),
    };

    // Find action with highest confidence
    let bestAction = "Neutral";
    let bestConfidence = 0;

    for (const [action, result] of Object.entries(actions)) {
      if (result.detected && result.confidence > bestConfidence) {
        bestAction = action;
        bestConfidence = result.confidence;
      }
    }

    return {
      action: bestAction,
      confidence: bestConfidence,
      allActions: actions
    };
  }
}
