#!/usr/bin/env python
"""
Posture Detection System for WT901BLE67 IMU Sensor
===================================================

Sensor Setup:
- Mounted on upper back (below neck)
- Y-axis is vertical when user is standing upright
- Detects: Standing, Bent Forward, Sitting, Lying Down, Jumping

Usage:
    # Live analysis from sensor
    python analyze.py --live

    # Analyze from log file
    python analyze.py --file sensor_log.txt

    # Test mode with current data
    python analyze.py --test
"""

from __future__ import print_function
import sys
import re
import time
import argparse
from collections import deque
import math

# ANSI Colors for terminal output
ANSI_RED = '\033[31m'
ANSI_GREEN = '\033[32m'
ANSI_YELLOW = '\033[33m'
ANSI_BLUE = '\033[34m'
ANSI_MAGENTA = '\033[35m'
ANSI_CYAN = '\033[36m'
ANSI_WHITE = '\033[37m'
ANSI_BOLD = '\033[1m'
ANSI_OFF = '\033[0m'

# ============================================================================
# POSTURE DETECTION THRESHOLDS
# ============================================================================
# Adjust these based on your sensor orientation and calibration

class PostureConfig:
    """Configuration for posture detection thresholds"""

    # Standing detection
    STANDING_ACC_Y_MIN = 0.85      # Minimum Y acceleration for standing (g)
    STANDING_ACC_Y_MAX = 1.15      # Maximum Y acceleration for standing (g)
    STANDING_PITCH_MAX = 15.0      # Maximum pitch angle for standing (degrees)
    STANDING_GYRO_MAX = 50.0       # Maximum gyro activity for stable standing (deg/s)

    # Bent forward detection
    BENT_PITCH_MIN = 30.0          # Minimum pitch to consider bent forward (degrees)
    BENT_ACC_Y_MAX = 0.7           # Y acceleration decreases when bending

    # Sitting detection
    SITTING_PITCH_MIN = 15.0       # Minimum pitch for sitting
    SITTING_PITCH_MAX = 45.0       # Maximum pitch for sitting
    SITTING_ACC_Y_MIN = 0.5        # Y acceleration range for sitting
    SITTING_ACC_Y_MAX = 0.9
    SITTING_STABILITY_TIME = 2.0   # Seconds to be stable to confirm sitting

    # Lying down detection
    LYING_ACC_Y_MAX = 0.3          # Y acceleration near 0 when lying
    LYING_ACC_XZ_MIN = 0.8         # X or Z acceleration should be ~1g when lying

    # Jumping detection
    JUMP_ACC_Y_SPIKE_HIGH = 1.3    # Acceleration spike during jump (g)
    JUMP_ACC_Y_SPIKE_LOW = 0.6     # Acceleration drop during jump (g)
    JUMP_GYRO_THRESHOLD = 100.0    # Gyro activity during jump (deg/s)
    JUMP_COOLDOWN = 1.0            # Seconds before detecting another jump

    # Smoothing and filtering
    SMOOTHING_WINDOW = 5           # Number of samples for moving average
    STATE_CHANGE_THRESHOLD = 0.8   # Confidence needed to change state (0-1)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class SensorData:
    """Container for parsed sensor data"""
    def __init__(self, acc_x=0, acc_y=0, acc_z=0,
                 gyro_x=0, gyro_y=0, gyro_z=0,
                 roll=0, pitch=0, yaw=0,
                 mag_x=0, mag_y=0, mag_z=0):
        # Accelerometer (g)
        self.acc_x = acc_x
        self.acc_y = acc_y
        self.acc_z = acc_z

        # Gyroscope (deg/s)
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z

        # Angles (degrees)
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

        # Magnetometer (optional)
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z

        self.timestamp = time.time()

    def __str__(self):
        return "acc:%.2f,%.2f,%.2f gyro:%.2f,%.2f,%.2f angle:%.2f,%.2f,%.2f" % (
            self.acc_x, self.acc_y, self.acc_z,
            self.gyro_x, self.gyro_y, self.gyro_z,
            self.roll, self.pitch, self.yaw
        )

class PostureState:
    """Enumeration of possible postures"""
    UNKNOWN = "Unknown"
    STANDING = "Standing"
    BENT_FORWARD = "Bent Forward"
    SITTING = "Sitting"
    LYING_DOWN = "Lying Down"
    JUMPING = "Jumping"

    @staticmethod
    def get_color(state):
        """Get ANSI color for each state"""
        colors = {
            PostureState.UNKNOWN: ANSI_WHITE,
            PostureState.STANDING: ANSI_GREEN,
            PostureState.BENT_FORWARD: ANSI_YELLOW,
            PostureState.SITTING: ANSI_CYAN,
            PostureState.LYING_DOWN: ANSI_BLUE,
            PostureState.JUMPING: ANSI_MAGENTA,
        }
        return colors.get(state, ANSI_WHITE)

    @staticmethod
    def get_emoji(state):
        """Get emoji representation for each state"""
        emojis = {
            PostureState.UNKNOWN: "?",
            PostureState.STANDING: "🧍",
            PostureState.SITTING: "🪑",
            PostureState.BENT_FORWARD: "🙇",
            PostureState.LYING_DOWN: "🛌",
            PostureState.JUMPING: "🤸",
        }
        return emojis.get(state, "?")

# ============================================================================
# DATA PARSING
# ============================================================================

def parse_sensor_line(line):
    """
    Parse a line of sensor data

    Format: acc:x,y,z gyro:x,y,z angle:roll,pitch,yaw [mag:x,y,z]

    Returns:
        SensorData object or None if parsing fails
    """
    try:
        # Parse accelerometer
        acc_match = re.search(r'acc:([-\d.]+),([-\d.]+),([-\d.]+)', line)
        if not acc_match:
            return None
        acc_x, acc_y, acc_z = map(float, acc_match.groups())

        # Parse gyroscope
        gyro_match = re.search(r'gyro:([-\d.]+),([-\d.]+),([-\d.]+)', line)
        if not gyro_match:
            return None
        gyro_x, gyro_y, gyro_z = map(float, gyro_match.groups())

        # Parse angles
        angle_match = re.search(r'angle:([-\d.]+),([-\d.]+),([-\d.]+)', line)
        if not angle_match:
            return None
        roll, pitch, yaw = map(float, angle_match.groups())

        # Parse magnetometer (optional)
        mag_x, mag_y, mag_z = 0, 0, 0
        mag_match = re.search(r'mag:([-\d.]+),([-\d.]+),([-\d.]+)', line)
        if mag_match:
            mag_x, mag_y, mag_z = map(float, mag_match.groups())

        return SensorData(acc_x, acc_y, acc_z,
                         gyro_x, gyro_y, gyro_z,
                         roll, pitch, yaw,
                         mag_x, mag_y, mag_z)
    except Exception as e:
        return None

# ============================================================================
# POSTURE DETECTION
# ============================================================================

class PostureAnalyzer:
    """Main posture detection and analysis class"""

    def __init__(self, config=None):
        self.config = config or PostureConfig()
        self.current_state = PostureState.UNKNOWN
        self.state_confidence = 0.0
        self.last_jump_time = 0

        # History for smoothing
        self.acc_y_history = deque(maxlen=self.config.SMOOTHING_WINDOW)
        self.pitch_history = deque(maxlen=self.config.SMOOTHING_WINDOW)
        self.gyro_history = deque(maxlen=self.config.SMOOTHING_WINDOW)

        # State timing
        self.state_start_time = time.time()
        self.state_duration = 0

        # Statistics
        self.total_samples = 0
        self.state_counts = {state: 0 for state in [
            PostureState.UNKNOWN, PostureState.STANDING, PostureState.BENT_FORWARD,
            PostureState.SITTING, PostureState.LYING_DOWN, PostureState.JUMPING
        ]}

    def analyze(self, sensor_data):
        """
        Analyze sensor data and determine posture

        Args:
            sensor_data: SensorData object

        Returns:
            tuple: (posture_state, confidence, details_dict)
        """
        self.total_samples += 1

        # Update history
        self.acc_y_history.append(sensor_data.acc_y)
        self.pitch_history.append(abs(sensor_data.pitch))

        # Calculate gyro magnitude
        gyro_mag = math.sqrt(sensor_data.gyro_x**2 +
                            sensor_data.gyro_y**2 +
                            sensor_data.gyro_z**2)
        self.gyro_history.append(gyro_mag)

        # Get smoothed values
        avg_acc_y = sum(self.acc_y_history) / len(self.acc_y_history) if self.acc_y_history else sensor_data.acc_y
        avg_pitch = sum(self.pitch_history) / len(self.pitch_history) if self.pitch_history else abs(sensor_data.pitch)
        avg_gyro = sum(self.gyro_history) / len(self.gyro_history) if self.gyro_history else gyro_mag

        # Detect posture (priority order matters!)
        detected_state, confidence, details = self._detect_posture(
            sensor_data, avg_acc_y, avg_pitch, avg_gyro
        )

        # Update state if confidence is high enough
        if detected_state != self.current_state:
            if confidence >= self.config.STATE_CHANGE_THRESHOLD:
                self.current_state = detected_state
                self.state_confidence = confidence
                self.state_start_time = time.time()
            else:
                # Keep current state but update confidence
                detected_state = self.current_state
                confidence = self.state_confidence
        else:
            self.state_confidence = confidence

        # Update duration
        self.state_duration = time.time() - self.state_start_time

        # Update statistics
        self.state_counts[detected_state] += 1

        details['duration'] = self.state_duration
        details['smoothed_acc_y'] = avg_acc_y
        details['smoothed_pitch'] = avg_pitch
        details['smoothed_gyro'] = avg_gyro

        return detected_state, confidence, details

    def _detect_posture(self, data, avg_acc_y, avg_pitch, avg_gyro):
        """Internal posture detection logic"""

        details = {}

        # 1. Check for JUMPING (highest priority - transient state)
        current_time = time.time()
        if current_time - self.last_jump_time > self.config.JUMP_COOLDOWN:
            if (data.acc_y > self.config.JUMP_ACC_Y_SPIKE_HIGH or
                data.acc_y < self.config.JUMP_ACC_Y_SPIKE_LOW) and \
               avg_gyro > self.config.JUMP_GYRO_THRESHOLD:
                self.last_jump_time = current_time
                details['trigger'] = 'acceleration spike + gyro activity'
                return PostureState.JUMPING, 0.95, details

        # 2. Check for LYING DOWN
        acc_x_abs = abs(data.acc_x)
        acc_z_abs = abs(data.acc_z)
        if abs(avg_acc_y) < self.config.LYING_ACC_Y_MAX and \
           (acc_x_abs > self.config.LYING_ACC_XZ_MIN or
            acc_z_abs > self.config.LYING_ACC_XZ_MIN):
            details['trigger'] = 'horizontal orientation (acc_y ≈ 0, acc_x or acc_z ≈ 1)'
            confidence = min(0.95, 1.0 - abs(avg_acc_y) / self.config.LYING_ACC_Y_MAX)
            return PostureState.LYING_DOWN, confidence, details

        # 3. Check for BENT FORWARD
        if avg_pitch > self.config.BENT_PITCH_MIN and \
           avg_acc_y < self.config.BENT_ACC_Y_MAX:
            details['trigger'] = 'high pitch angle + reduced acc_y'
            details['pitch'] = avg_pitch
            confidence = min(0.95, avg_pitch / 90.0)  # Scale with pitch angle
            return PostureState.BENT_FORWARD, confidence, details

        # 4. Check for SITTING
        if self.config.SITTING_PITCH_MIN < avg_pitch < self.config.SITTING_PITCH_MAX and \
           self.config.SITTING_ACC_Y_MIN < avg_acc_y < self.config.SITTING_ACC_Y_MAX and \
           avg_gyro < self.config.STANDING_GYRO_MAX:
            # Require stability for sitting confirmation
            if self.state_duration > self.config.SITTING_STABILITY_TIME or \
               self.current_state == PostureState.SITTING:
                details['trigger'] = 'moderate pitch + stable position'
                details['pitch'] = avg_pitch
                confidence = 0.85
                return PostureState.SITTING, confidence, details
            else:
                # Might be transitioning to sitting
                details['trigger'] = 'possibly sitting (waiting for stability)'
                return PostureState.UNKNOWN, 0.5, details

        # 5. Check for STANDING (default stable state)
        if self.config.STANDING_ACC_Y_MIN < avg_acc_y < self.config.STANDING_ACC_Y_MAX and \
           avg_pitch < self.config.STANDING_PITCH_MAX and \
           avg_gyro < self.config.STANDING_GYRO_MAX:
            details['trigger'] = 'vertical orientation + stable'
            confidence = 0.9
            return PostureState.STANDING, confidence, details

        # Unknown state
        details['trigger'] = 'no clear posture detected'
        return PostureState.UNKNOWN, 0.3, details

# ============================================================================
# VISUALIZATION
# ============================================================================

def clear_screen():
    """Clear terminal screen"""
    print("\033[2J\033[H", end='')

def draw_posture_display(state, confidence, sensor_data, details, analyzer):
    """Draw real-time posture display in terminal"""

    clear_screen()

    # Header
    print(ANSI_BOLD + "="*70 + ANSI_OFF)
    print(ANSI_BOLD + ANSI_CYAN + "     POSTURE DETECTION SYSTEM - WT901BLE67 IMU Sensor" + ANSI_OFF)
    print(ANSI_BOLD + "="*70 + ANSI_OFF)
    print()

    # Current posture (large display)
    color = PostureState.get_color(state)
    emoji = PostureState.get_emoji(state)
    print(color + ANSI_BOLD + "  CURRENT POSTURE: " + emoji + " " + state.upper() + ANSI_OFF)
    print(color + "  Confidence: " + ("█" * int(confidence * 20)) + " %.1f%%" % (confidence * 100) + ANSI_OFF)
    print("  Duration: %.1fs" % details.get('duration', 0))
    print()

    # Sensor data
    print(ANSI_BOLD + "Sensor Data:" + ANSI_OFF)
    print("  Accelerometer (g):  X=%6.2f  Y=%6.2f  Z=%6.2f" % (
        sensor_data.acc_x, sensor_data.acc_y, sensor_data.acc_z))
    print("  Gyroscope (°/s):    X=%6.2f  Y=%6.2f  Z=%6.2f" % (
        sensor_data.gyro_x, sensor_data.gyro_y, sensor_data.gyro_z))
    print("  Angles (°):      Roll=%6.2f  Pitch=%6.2f  Yaw=%6.2f" % (
        sensor_data.roll, sensor_data.pitch, sensor_data.yaw))
    print()

    # Smoothed values
    print(ANSI_BOLD + "Smoothed Values:" + ANSI_OFF)
    print("  Acc Y: %.2f g" % details.get('smoothed_acc_y', 0))
    print("  Pitch: %.2f°" % details.get('smoothed_pitch', 0))
    print("  Gyro:  %.2f°/s" % details.get('smoothed_gyro', 0))
    print()

    # Detection details
    print(ANSI_BOLD + "Detection:" + ANSI_OFF)
    print("  Trigger: " + details.get('trigger', 'N/A'))
    print()

    # Statistics
    print(ANSI_BOLD + "Session Statistics:" + ANSI_OFF)
    print("  Total Samples: %d" % analyzer.total_samples)
    for posture, count in analyzer.state_counts.items():
        if count > 0:
            percentage = (count / analyzer.total_samples) * 100
            print("  %s: %d (%.1f%%)" % (posture, count, percentage))
    print()

    # ASCII art representation
    print(ANSI_BOLD + "Visual:" + ANSI_OFF)
    draw_ascii_posture(state, sensor_data)
    print()

    print(ANSI_BOLD + "="*70 + ANSI_OFF)
    print("Press Ctrl+C to exit")

def draw_ascii_posture(state, sensor_data):
    """Draw simple ASCII art of current posture"""

    if state == PostureState.STANDING:
        print("""
        O      <- Head
       /|\\     <- Arms
        |      <- Body
       / \\     <- Legs
    (STANDING)
        """)

    elif state == PostureState.BENT_FORWARD:
        print("""
        O
       /|___   <- Bending forward
        |
       / \\
    (BENT FORWARD)
        """)

    elif state == PostureState.SITTING:
        print("""
        O
       /|\\
        |___   <- Sitting
       /   /
    (SITTING)
        """)

    elif state == PostureState.LYING_DOWN:
        print("""

    ___O___/|\\___/___  <- Lying horizontally

    (LYING DOWN)
        """)

    elif state == PostureState.JUMPING:
        print("""
       \\O/     <- Arms up
        |
       / \\     <- In air
    (JUMPING!)
        """)

    else:
        print("""
        ?
       /|\\
        |
       / \\
    (UNKNOWN)
        """)

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def analyze_live():
    """Analyze live data from sensor (to be implemented with wit_ble.py integration)"""
    print(ANSI_RED + "Live analysis mode not yet implemented." + ANSI_OFF)
    print("This will integrate with wit_ble.py to receive real-time data.")
    print("\nFor now, use --test mode or --file mode.")

def analyze_file(filename):
    """Analyze data from a log file"""
    print("Analyzing data from file: %s" % filename)

    analyzer = PostureAnalyzer()

    try:
        with open(filename, 'r') as f:
            for line in f:
                sensor_data = parse_sensor_line(line)
                if sensor_data:
                    state, confidence, details = analyzer.analyze(sensor_data)
                    draw_posture_display(state, confidence, sensor_data, details, analyzer)
                    time.sleep(0.1)  # Slow down for visualization
    except IOError as e:
        print(ANSI_RED + "Error reading file: " + str(e) + ANSI_OFF)
    except KeyboardInterrupt:
        print("\n\nAnalysis stopped by user")

def analyze_test():
    """Test mode with sample data"""
    print("Running in TEST mode with sample sensor data...")
    print("Simulating different postures...\n")

    analyzer = PostureAnalyzer()

    # Sample data for different postures
    test_scenarios = [
        ("Standing", [
            "acc:0.02,-0.01,1.01 gyro:0.31,-0.06,-0.06 angle:-0.43,-0.91,0.00",
            "acc:0.01,0.00,1.00 gyro:0.20,0.00,-0.05 angle:-0.50,-1.00,0.00",
            "acc:0.03,-0.02,0.99 gyro:0.25,-0.03,-0.04 angle:-0.45,-0.95,0.00",
        ]),
        ("Bent Forward", [
            "acc:0.50,-0.05,0.65 gyro:5.0,2.0,1.0 angle:35.0,-45.0,0.00",
            "acc:0.48,-0.03,0.68 gyro:3.5,1.5,0.8 angle:38.0,-48.0,0.00",
            "acc:0.52,-0.06,0.63 gyro:4.2,1.8,1.2 angle:36.0,-46.0,0.00",
        ]),
        ("Sitting", [
            "acc:0.30,0.70,0.40 gyro:0.50,0.20,0.10 angle:20.0,-25.0,0.00",
            "acc:0.32,0.68,0.42 gyro:0.45,0.15,0.12 angle:22.0,-26.0,0.00",
            "acc:0.28,0.72,0.38 gyro:0.48,0.18,0.08 angle:19.0,-24.0,0.00",
        ]),
        ("Lying Down", [
            "acc:0.98,0.05,0.02 gyro:0.10,0.05,0.08 angle:85.0,-2.0,0.00",
            "acc:0.97,0.03,0.01 gyro:0.08,0.03,0.06 angle:87.0,-1.5,0.00",
            "acc:0.99,0.06,0.03 gyro:0.12,0.04,0.09 angle:84.0,-2.5,0.00",
        ]),
        ("Jumping", [
            "acc:0.02,1.45,1.01 gyro:120.0,80.0,95.0 angle:10.0,-5.0,0.00",
            "acc:0.01,0.40,0.98 gyro:110.0,75.0,88.0 angle:12.0,-4.0,0.00",
            "acc:0.03,1.52,1.03 gyro:125.0,85.0,100.0 angle:9.0,-6.0,0.00",
        ]),
    ]

    try:
        for scenario_name, data_lines in test_scenarios:
            print(ANSI_CYAN + "\n>>> Simulating: " + scenario_name + ANSI_OFF)
            time.sleep(1)

            for line in data_lines:
                sensor_data = parse_sensor_line(line)
                if sensor_data:
                    state, confidence, details = analyzer.analyze(sensor_data)
                    draw_posture_display(state, confidence, sensor_data, details, analyzer)
                    time.sleep(1)  # Display each sample for 1 second
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")

    print("\n" + ANSI_GREEN + "Test complete!" + ANSI_OFF)

def main():
    parser = argparse.ArgumentParser(
        description='Posture Detection System for WT901BLE67 IMU Sensor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test              Run in test mode with sample data
  %(prog)s --file log.txt      Analyze data from log file
  %(prog)s --live              Analyze live sensor data (not yet implemented)
        """
    )

    parser.add_argument('--test', action='store_true',
                        help='Run in test mode with sample data')
    parser.add_argument('--file', type=str, metavar='FILENAME',
                        help='Analyze data from log file')
    parser.add_argument('--live', action='store_true',
                        help='Analyze live sensor data')

    args = parser.parse_args()

    # Determine mode
    if args.test:
        analyze_test()
    elif args.file:
        analyze_file(args.file)
    elif args.live:
        analyze_live()
    else:
        # Default to test mode
        print("No mode specified, running in test mode...")
        print("Use --help to see available options\n")
        time.sleep(1)
        analyze_test()

if __name__ == "__main__":
    main()
