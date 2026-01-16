/**
 * PoseDetector - Real-time pose skeleton visualization using ml5.js MoveNet
 *
 * Features:
 * - MoveNet Lightning model (fast, accurate single-person detection)
 * - 17 keypoint detection (nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles)
 * - Real-time skeleton overlay on video preview
 * - Activity classification from pose keypoints
 * - Synchronized with video recording lifecycle
 */

class PoseDetector {
    constructor(options = {}) {
        // Configuration
        this.config = {
            modelType: options.modelType || 'SINGLEPOSE_LIGHTNING',
            enableSmoothing: options.smoothing !== false,
            minPoseScore: options.minScore || 0.25,
            flipped: options.flipped !== false  // Mirror detection for natural interaction
        };

        // State management
        this.state = 'idle';  // idle, loading, ready, detecting, error
        this.bodyPose = null;
        this.poses = [];
        this.videoElement = null;
        this.canvasElement = null;
        this.ctx = null;

        // Current activity detection
        this.currentActivity = { activity: 'Unknown', confidence: 0 };

        // Visual styling
        this.colors = {
            keypoint: 'rgb(0, 255, 0)',       // Green circles
            skeleton: 'rgb(255, 0, 255)',     // Magenta lines
            confidence: 'rgba(255, 255, 0, 0.5)'  // Yellow semi-transparent
        };
        this.keypointRadius = 8;
        this.lineWidth = 2;

        // Scale factors for coordinate mapping
        this.scaleX = 1;
        this.scaleY = 1;
    }

    /**
     * Initialize camera and check permissions
     */
    async init(videoElementId, canvasElementId) {
        if (this.state !== 'idle' && this.state !== 'ready') {
            throw new Error(`Cannot initialize in state: ${this.state}`);
        }

        if (typeof ml5 === 'undefined') {
            throw new Error('ml5.js library not loaded');
        }

        this.state = 'loading';

        try {
            // Get DOM elements
            this.videoElement = document.getElementById(videoElementId);
            this.canvasElement = document.getElementById(canvasElementId);

            if (!this.videoElement || !this.canvasElement) {
                throw new Error('Video or canvas element not found');
            }

            // Setup canvas
            this.ctx = this.canvasElement.getContext('2d');
            this.resizeCanvas();

            // Load BodyPose model
            console.log('[PoseDetector] Loading MoveNet model...');
            this.bodyPose = await ml5.bodyPose('MoveNet', {
                modelType: this.config.modelType,
                enableSmoothing: this.config.enableSmoothing,
                minPoseScore: this.config.minPoseScore,
                flipped: this.config.flipped
            });

            console.log('[PoseDetector] Model loaded successfully');
            this.state = 'ready';

            return true;

        } catch (error) {
            console.error('[PoseDetector] Initialization failed:', error);
            this.state = 'error';
            throw error;
        }
    }

    /**
     * Resize canvas to match video element
     */
    resizeCanvas() {
        // Match canvas dimensions to video element
        const rect = this.videoElement.getBoundingClientRect();
        this.canvasElement.width = rect.width;
        this.canvasElement.height = rect.height;

        // Get actual video dimensions
        const videoWidth = this.videoElement.videoWidth || 1280;
        const videoHeight = this.videoElement.videoHeight || 720;

        // Scale factor for proper coordinate mapping
        this.scaleX = this.canvasElement.width / videoWidth;
        this.scaleY = this.canvasElement.height / videoHeight;

        console.log(`[PoseDetector] Canvas resized: ${this.canvasElement.width}x${this.canvasElement.height}`);
        console.log(`[PoseDetector] Scale factors: ${this.scaleX.toFixed(3)}x, ${this.scaleY.toFixed(3)}y`);
    }

    /**
     * Start continuous pose detection
     */
    async startDetection() {
        if (this.state !== 'ready') {
            throw new Error(`Cannot start detection in state: ${this.state}`);
        }

        if (!this.videoElement || !this.bodyPose) {
            throw new Error('Not initialized. Call init() first.');
        }

        this.state = 'detecting';

        // Start continuous detection with callback
        await this.bodyPose.detectStart(this.videoElement, (results) => {
            this.handleDetectionResults(results);
        });

        console.log('[PoseDetector] Detection started');
    }

    /**
     * Handle detection results
     */
    handleDetectionResults(results) {
        this.poses = results;

        // Classify activity from first detected pose
        if (results && results.length > 0) {
            this.currentActivity = this.classifyActivity(results[0]);
        } else {
            this.currentActivity = { activity: 'Unknown', confidence: 0 };
        }

        // Draw poses on canvas
        this.drawPoses(results);
    }

    /**
     * Stop continuous detection
     */
    stopDetection() {
        if (this.state !== 'detecting') {
            console.warn(`[PoseDetector] Not detecting (state: ${this.state})`);
            return;
        }

        if (this.bodyPose) {
            this.bodyPose.detectStop();
        }

        this.clearCanvas();
        this.poses = [];
        this.currentActivity = { activity: 'Unknown', confidence: 0 };
        this.state = 'ready';

        console.log('[PoseDetector] Detection stopped');
    }

    /**
     * Classify activity from pose keypoints
     */
    classifyActivity(pose) {
        if (!pose || !pose.keypoints) {
            return { activity: 'Unknown', confidence: 0 };
        }

        // Extract key body points (keypoint indices from MoveNet)
        const nose = pose.keypoints[0];           // 0: nose
        const leftShoulder = pose.keypoints[5];   // 5: left_shoulder
        const rightShoulder = pose.keypoints[6];  // 6: right_shoulder
        const leftHip = pose.keypoints[11];       // 11: left_hip
        const rightHip = pose.keypoints[12];      // 12: right_hip
        const leftKnee = pose.keypoints[13];      // 13: left_knee
        const rightKnee = pose.keypoints[14];     // 14: right_knee

        // Check if key points have sufficient confidence
        const minConfidence = this.config.minPoseScore;
        if (nose.confidence < minConfidence ||
            leftShoulder.confidence < minConfidence ||
            rightShoulder.confidence < minConfidence ||
            leftHip.confidence < minConfidence ||
            rightHip.confidence < minConfidence) {
            return { activity: 'Unknown', confidence: 0 };
        }

        // Calculate body angles and positions
        const shoulderMidY = (leftShoulder.y + rightShoulder.y) / 2;
        const hipMidY = (leftHip.y + rightHip.y) / 2;

        // Torso angle (vertical = 0, horizontal = 90)
        const torsoAngle = Math.abs(Math.atan2(hipMidY - shoulderMidY, 1) * 180 / Math.PI);

        // Head to hip distance (vertical alignment)
        const headToHipDistance = Math.abs(nose.y - hipMidY);

        // Knee bend detection
        const leftKneeBend = leftKnee.confidence > minConfidence &&
                            Math.abs(leftKnee.y - leftHip.y) < 100;
        const rightKneeBend = rightKnee.confidence > minConfidence &&
                             Math.abs(rightKnee.y - rightHip.y) < 100;

        // Classification rules (priority order)
        // Priority: Lying → Sitting → Bent_Forward → Standing

        // Lying Down: Torso nearly horizontal
        if (torsoAngle > 70) {
            const confidence = Math.round(85 + (torsoAngle - 70) / 2);
            return { activity: 'Lying_Down', confidence: Math.min(95, confidence) };
        }

        // Sitting: Torso tilted, knees bent, head close to hips
        if (torsoAngle > 40 && torsoAngle <= 70 && headToHipDistance < 150) {
            let confidence = 75;
            if (leftKneeBend || rightKneeBend) confidence += 10;
            return { activity: 'Sitting', confidence: Math.min(95, confidence) };
        }

        // Bent Forward: Torso moderately tilted
        if (torsoAngle > 20 && torsoAngle <= 40) {
            let confidence = 70 + (torsoAngle - 20);
            return { activity: 'Bent_Forward', confidence: Math.min(95, Math.round(confidence)) };
        }

        // Standing: Torso mostly vertical
        if (torsoAngle <= 20) {
            let confidence = 85;
            if (torsoAngle < 10) confidence += 5;  // Very upright
            return { activity: 'Standing', confidence: Math.min(95, confidence) };
        }

        // Fallback
        return { activity: 'Unknown', confidence: 50 };
    }

    /**
     * Get current detected activity
     */
    getCurrentActivity() {
        return this.currentActivity;
    }

    /**
     * Draw all detected poses
     */
    drawPoses(poses) {
        if (!this.ctx || !poses || poses.length === 0) {
            this.clearCanvas();
            return;
        }

        try {
            // Clear previous frame
            this.clearCanvas();

            // Draw each detected pose
            for (const pose of poses) {
                this.drawSkeleton(pose);
                this.drawKeypoints(pose);
            }
        } catch (error) {
            console.error('[PoseDetector] Drawing error:', error);
            // Skip this frame, continue on next
        }
    }

    /**
     * Draw skeleton connections
     */
    drawSkeleton(pose) {
        if (!pose || !pose.keypoints) return;

        const connections = this.getSkeletonConnections();

        this.ctx.strokeStyle = this.colors.skeleton;
        this.ctx.lineWidth = this.lineWidth;

        for (const [i, j] of connections) {
            const kp1 = pose.keypoints[i];
            const kp2 = pose.keypoints[j];

            // Only draw if both keypoints are confident
            if (kp1.confidence < this.config.minPoseScore ||
                kp2.confidence < this.config.minPoseScore) {
                continue;
            }

            // Scale coordinates to canvas size
            const x1 = kp1.x * this.scaleX;
            const y1 = kp1.y * this.scaleY;
            const x2 = kp2.x * this.scaleX;
            const y2 = kp2.y * this.scaleY;

            // Draw line
            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.stroke();
        }
    }

    /**
     * Draw keypoint circles
     */
    drawKeypoints(pose) {
        if (!pose || !pose.keypoints) return;

        for (const keypoint of pose.keypoints) {
            // Only draw if confidence is high enough
            if (keypoint.confidence < this.config.minPoseScore) continue;

            // Scale coordinates to canvas size
            const x = keypoint.x * this.scaleX;
            const y = keypoint.y * this.scaleY;

            // Draw keypoint circle
            this.ctx.fillStyle = this.colors.keypoint;
            this.ctx.beginPath();
            this.ctx.arc(x, y, this.keypointRadius, 0, 2 * Math.PI);
            this.ctx.fill();

            // Draw confidence indicator for low-confidence points
            if (keypoint.confidence < 0.5) {
                this.ctx.fillStyle = this.colors.confidence;
                this.ctx.beginPath();
                this.ctx.arc(x, y, this.keypointRadius * 0.5, 0, 2 * Math.PI);
                this.ctx.fill();
            }
        }
    }

    /**
     * Get skeleton connection pairs
     * Based on MoveNet 17 keypoint structure
     */
    getSkeletonConnections() {
        // MoveNet keypoint indices:
        // 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
        // 5: left_shoulder, 6: right_shoulder
        // 7: left_elbow, 8: right_elbow
        // 9: left_wrist, 10: right_wrist
        // 11: left_hip, 12: right_hip
        // 13: left_knee, 14: right_knee
        // 15: left_ankle, 16: right_ankle

        return [
            // Head
            [0, 1],   // nose → left_eye
            [0, 2],   // nose → right_eye
            [1, 3],   // left_eye → left_ear
            [2, 4],   // right_eye → right_ear

            // Torso
            [5, 6],   // left_shoulder → right_shoulder
            [5, 11],  // left_shoulder → left_hip
            [6, 12],  // right_shoulder → right_hip
            [11, 12], // left_hip → right_hip

            // Left arm
            [5, 7],   // left_shoulder → left_elbow
            [7, 9],   // left_elbow → left_wrist

            // Right arm
            [6, 8],   // right_shoulder → right_elbow
            [8, 10],  // right_elbow → right_wrist

            // Left leg
            [11, 13], // left_hip → left_knee
            [13, 15], // left_knee → left_ankle

            // Right leg
            [12, 14], // right_hip → right_knee
            [14, 16]  // right_knee → right_ankle
        ];
    }

    /**
     * Clear canvas
     */
    clearCanvas() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    }

    /**
     * Get current state
     */
    getState() {
        return this.state;
    }

    /**
     * Clean up resources
     */
    destroy() {
        console.log('[PoseDetector] Cleaning up...');

        // Stop detection if active
        if (this.state === 'detecting') {
            this.stopDetection();
        }

        // Release model resources (ml5.js handles cleanup internally)
        this.bodyPose = null;

        // Clear canvas
        this.clearCanvas();

        // Clear references
        this.videoElement = null;
        this.canvasElement = null;
        this.ctx = null;
        this.poses = [];
        this.currentActivity = { activity: 'Unknown', confidence: 0 };
        this.state = 'idle';

        console.log('[PoseDetector] Cleanup complete');
    }

    /**
     * Check if browser supports pose detection
     */
    static isSupported() {
        // Check for canvas support
        const canvas = document.createElement('canvas');
        const hasCanvas = !!(canvas.getContext && canvas.getContext('2d'));

        // Check for required browser APIs
        const hasModernJS = typeof Promise !== 'undefined';

        return hasCanvas && hasModernJS;
    }
}

// Export for use in record.html
if (typeof window !== 'undefined') {
    window.PoseDetector = PoseDetector;
}
