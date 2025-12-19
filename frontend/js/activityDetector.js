/**
 * Activity Detector - Real-time activity recognition from sensor data
 *
 * Analyzes foot pressure and accelerometer readings to detect:
 * - Standing, Sitting, Bent_Forward, Lying_Down, Jumping
 *
 * Returns: { activity: string, confidence: number (0-100) }
 */

class ActivityDetector {
    constructor() {
        // State for latest sensor readings
        this.latestFootData = { left: null, right: null };
        this.latestAccelData = null;
        this.detectedActivity = 'Unknown';
        this.detectionConfidence = 0;
    }

    /**
     * Update foot sensor data (called when new foot_data arrives)
     */
    updateFootData(footData) {
        if (footData.foot === 'LEFT') {
            this.latestFootData.left = footData;
        } else if (footData.foot === 'RIGHT') {
            this.latestFootData.right = footData;
        }
    }

    /**
     * Update accelerometer data (called when new accel_data arrives)
     */
    updateAccelData(accelData) {
        this.latestAccelData = accelData;
    }

    /**
     * Main detection method - analyzes current sensor state
     * @returns {{ activity: string, confidence: number }}
     */
    detectActivity() {
        if (!this.latestAccelData) {
            return { activity: 'Unknown', confidence: 0 };
        }

        const accel = this.latestAccelData.acc;
        const gyro = this.latestAccelData.gyro;
        const angle = this.latestAccelData.angle;

        // Calculate derived metrics
        const accelY = accel.y;
        const pitch = angle.pitch;
        const gyroMagnitude = Math.sqrt(gyro.x**2 + gyro.y**2 + gyro.z**2);

        // Get average foot pressure if available
        const avgPressure = this._calculateAvgPressure();

        // Run detection checks in priority order
        let result;

        result = this._checkLyingDown(accelY, pitch, angle.roll);
        if (result) return result;

        result = this._checkJumping(gyroMagnitude);
        if (result) return result;

        result = this._checkBentForward(pitch, accelY);
        if (result) return result;

        result = this._checkSitting(pitch, avgPressure, gyroMagnitude);
        if (result) return result;

        result = this._checkStanding(accelY, pitch, gyroMagnitude);
        if (result) return result;

        // Fallback
        return this._fallbackDetection(accelY);
    }

    /**
     * Check for Lying_Down activity
     */
    _checkLyingDown(accelY, pitch, roll) {
        if (Math.abs(accelY) < 0.3) {
            const horizontalAngle = Math.abs(pitch) > 75 || Math.abs(roll) > 75;
            if (horizontalAngle) {
                const confidence = Math.round(95 - Math.abs(accelY) * 100);
                return { activity: 'Lying_Down', confidence };
            }
        }
        return null;
    }

    /**
     * Check for Jumping activity
     */
    _checkJumping(gyroMagnitude) {
        if (gyroMagnitude > 100) {
            const confidence = Math.round(Math.min(95, 60 + (gyroMagnitude - 100) / 5));
            return { activity: 'Jumping', confidence };
        }
        return null;
    }

    /**
     * Check for Bent_Forward activity
     */
    _checkBentForward(pitch, accelY) {
        if (pitch > 40 && pitch < 85) {
            let confidence = Math.min(95, 50 + pitch / 2);
            if (accelY < 0.7) confidence += 10;
            return { activity: 'Bent_Forward', confidence: Math.round(confidence) };
        }
        return null;
    }

    /**
     * Check for Sitting activity
     */
    _checkSitting(pitch, avgPressure, gyroMagnitude) {
        if (pitch > 20 && pitch < 45 && avgPressure < 90) {
            let confidence = 75;
            if (gyroMagnitude < 15) confidence += 10;
            if (avgPressure < 60) confidence += 5;
            return { activity: 'Sitting', confidence: Math.round(Math.min(95, confidence)) };
        }
        return null;
    }

    /**
     * Check for Standing activity
     */
    _checkStanding(accelY, pitch, gyroMagnitude) {
        if (accelY >= 0.85 && accelY <= 1.15) {
            let confidence = 80;
            if (Math.abs(pitch) < 10) confidence += 10;
            if (gyroMagnitude < 30) confidence += 5;
            return { activity: 'Standing', confidence: Math.round(Math.min(95, confidence)) };
        }
        return null;
    }

    /**
     * Fallback detection when no clear pattern matches
     */
    _fallbackDetection(accelY) {
        if (accelY > 0.6) {
            return { activity: 'Standing', confidence: 50 };
        }
        return { activity: 'Unknown', confidence: 0 };
    }

    /**
     * Calculate average foot pressure across both feet
     */
    _calculateAvgPressure() {
        let avgPressure = 0;
        let footCount = 0;

        if (this.latestFootData.left) {
            avgPressure += this.latestFootData.left.avg || 0;
            footCount++;
        }
        if (this.latestFootData.right) {
            avgPressure += this.latestFootData.right.avg || 0;
            footCount++;
        }

        return footCount > 0 ? avgPressure / footCount : 0;
    }

    /**
     * Reset detector state (called on recording start/stop)
     */
    reset() {
        this.latestFootData = { left: null, right: null };
        this.latestAccelData = null;
        this.detectedActivity = 'Unknown';
        this.detectionConfidence = 0;
    }

    /**
     * Get current detection state
     */
    getState() {
        return {
            activity: this.detectedActivity,
            confidence: this.detectionConfidence
        };
    }
}

// Export for use in record.html
if (typeof window !== 'undefined') {
    window.ActivityDetector = ActivityDetector;
}
