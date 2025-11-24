"""Data parsing functions for foot pressure and accelerometer sensors."""

import struct
import numpy as np


# Foot sensor excluded indices (no physical sensors at these positions)
EXCLUDED_INDICES = {8, 12, 16, 19, 20, 23}


def parse_foot_data(line):
    """
    Parse foot pressure sensor data packet.

    Format: L_[[v1,v2,v3,v4],[v5,v6,v7,v8],...]\n

    Args:
        line: String data packet (without newline)

    Returns:
        dict: {
            'foot': 'LEFT' or 'RIGHT',
            'max': float,
            'avg': float,
            'active_count': int,
            'values': list of 18 floats
        } or None if parsing fails
    """
    if not line or len(line) < 3:
        return None

    try:
        # Identify foot
        if line.startswith('L_'):
            foot = 'LEFT'
            data_str = line[2:]
        elif line.startswith('R_'):
            foot = 'RIGHT'
            data_str = line[2:]
        else:
            return None

        # Parse nested array: remove brackets, split on commas
        data_str = data_str.replace('[', '').replace(']', '')
        values = [float(x.strip()) for x in data_str.split(',') if x.strip()]

        if len(values) != 24:
            return None

        # Extract 18 active sensors (exclude hardcoded indices)
        active_sensors = [v for i, v in enumerate(values) if i not in EXCLUDED_INDICES]
        active_array = np.array(active_sensors)

        return {
            'foot': foot,
            'max': float(active_array.max()),
            'avg': float(active_array.mean()),
            'active_count': int(np.count_nonzero(active_array)),
            'values': [float(v) for v in active_sensors]
        }

    except Exception:
        return None


def parse_accel_data(raw_data):
    """
    Parse accelerometer IMU sensor data packet (WT901BLE67 format).

    Binary format (20 bytes):
        [0]: 0x55 (header)
        [1]: 0x61 (combined packet type)
        [2-7]: Accelerometer X,Y,Z (3 signed shorts)
        [8-13]: Gyroscope X,Y,Z (3 signed shorts)
        [14-19]: Angles Roll,Pitch,Yaw (3 signed shorts)

    Args:
        raw_data: bytes object (20 bytes)

    Returns:
        dict: {
            'acc': {'x': float, 'y': float, 'z': float},  # in g
            'gyro': {'x': float, 'y': float, 'z': float}, # in deg/s
            'angle': {'roll': float, 'pitch': float, 'yaw': float} # in degrees
        } or None if parsing fails
    """
    if len(raw_data) < 20 or raw_data[0] != 0x55 or raw_data[1] != 0x61:
        return None

    try:
        # Unpack signed shorts (little-endian)
        acc_raw = struct.unpack('<hhh', raw_data[2:8])
        gyro_raw = struct.unpack('<hhh', raw_data[8:14])
        angle_raw = struct.unpack('<hhh', raw_data[14:20])

        # Convert to physical units
        # Accelerometer: ±16g range
        acc = [x / 32768.0 * 16 for x in acc_raw]

        # Gyroscope: ±2000°/s range
        gyro = [x / 32768.0 * 2000 for x in gyro_raw]

        # Angles: ±180° range
        angle = [x / 32768.0 * 180 for x in angle_raw]

        return {
            'acc': {
                'x': round(acc[0], 3),
                'y': round(acc[1], 3),
                'z': round(acc[2], 3)
            },
            'gyro': {
                'x': round(gyro[0], 2),
                'y': round(gyro[1], 2),
                'z': round(gyro[2], 2)
            },
            'angle': {
                'roll': round(angle[0], 2),
                'pitch': round(angle[1], 2),
                'yaw': round(angle[2], 2)
            }
        }

    except Exception:
        return None
