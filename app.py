# This program runs a Freenove 4WD Smart Car
# The Freenove motor library is imported via its specific system path.
# Library is used to communicate clearly to the Pi and Freenove GPIO pins.
# This path must be adjusted for any new environment/car.

import cv2
import numpy as np
import time
import atexit
import math
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from picamera2 import Picamera2

# global boolean variables
object_detected = False
detection_thread = None
stop_detection = False


# gpio cleanup
def cleanup_gpio():
    """Stop all motors on exit"""
    try:
        if "car" in globals():
            print("Cleaning up Freenove motor")
            car.set_motor_model(0, 0, 0, 0)
            car.close()
    except Exception as e:
        print(f"Cleanup error: {e}")


atexit.register(cleanup_gpio)


# setting up motors
try:
    import sys

    sys.path.append(
        #this would be dependent on your file structure/path to the Freenove motor library
        "/home/gwestry/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server"
    )
    import motor

    car = motor.Ordinary_Car()
    print("Freenove motor library loaded")
except ImportError as e:
    print(f"Freenove motor library not found: {e}")
    exit(1)


# flask setup
app = Flask(__name__)
CORS(app)


# motor control/movement logic
def move_car(direction, duration, speed=800):
    """Consistent movement with short stop pause"""
    print(f"Moving {direction} for {duration:.2f}s (speed={speed})")

    try:
        if direction == "forward":
            car.set_motor_model(speed, speed, speed, speed)
        elif direction == "backward":
            car.set_motor_model(-speed, -speed, -speed, -speed)
        elif direction == "left":
            car.set_motor_model(-speed, -speed, speed, speed)
        elif direction == "right":
            car.set_motor_model(speed, speed, -speed, -speed)
        elif direction == "stop":
            car.set_motor_model(0, 0, 0, 0)
            return

        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(0.01)  # timing

        car.set_motor_model(0, 0, 0, 0)
        time.sleep(0.15)  # short pause between movementss

    except Exception as e:
        print(f"Motor control error: {e}")
        car.set_motor_model(0, 0, 0, 0)


# green object detection
def detect_green_object():
    """Continuously detect pale/lime green objects using Picamera2 + OpenCV"""
    global object_detected, stop_detection

    picam2 = Picamera2()
    #configuration for low resolution. Good for limited hardware for smooth movement/detection.
    config = picam2.create_preview_configuration(main={"size": (320, 240)})
    picam2.configure(config)
    picam2.start()
    time.sleep(2)
    print("Green object detection started")

    while not stop_detection:
        try:
            frame = picam2.capture_array()
            if frame is None:
                continue

            # Convert to HSV to accurately detect colors
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Green color bounds for detection
            lower_green = np.array([35, 40, 40])
            upper_green = np.array([90, 255, 255])

            mask = cv2.inRange(hsv, lower_green, upper_green)
            green_pixels = cv2.countNonZero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            green_percent = (green_pixels / total_pixels) * 100

            if green_percent > 6:
                if not object_detected:
                    object_detected = True
                    print("GREEN OBJECT DETECTED!")
            else:
                object_detected = False

            time.sleep(0.1)

        except Exception as e:
            print(f"Camera error: {e}")
            time.sleep(0.2)

    picam2.stop()
    print("Green detection stopped.")


def start_detection():
    """Run detection in background"""
    global detection_thread, stop_detection
    if detection_thread and detection_thread.is_alive():
        print("Detection already running")
        return
    stop_detection = False
    detection_thread = threading.Thread(target=detect_green_object, daemon=True)
    detection_thread.start()


def stop_detection_thread():
    """Stop detection safely"""
    global stop_detection
    stop_detection = True


# converts drawn path to coordinates
def coordinates_to_moves(coords, pixels_per_second=100, min_distance=20):
    """Convert drawn coordinates into smooth motor movements"""
    if len(coords) < 2:
        return []

    filtered = [coords[0]]
    for i in range(1, len(coords)):
        x1, y1 = filtered[-1]
        x2, y2 = coords[i]
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if dist >= min_distance:
            filtered.append(coords[i])

    print(f"Simplified from {len(coords)} to {len(filtered)} points")
    if len(filtered) < 2:
        return []

    moves = []
    robot_angle = 270  # sets the robot to facing up initially

    for i in range(1, len(filtered)):
        x1, y1 = filtered[i - 1]
        x2, y2 = filtered[i]
        dx, dy = x2 - x1, y2 - y1
        target_angle = math.degrees(math.atan2(dy, dx))
        target_angle = (target_angle + 360) % 360

        angle_diff = target_angle - robot_angle
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        # turns only if necessary
        if abs(angle_diff) > 30:
            turn_dir = "right" if angle_diff > 0 else "left"
            turn_angle = abs(angle_diff) + 40
            turn_dur = turn_angle / 90 * 0.5
            print(f"Turn {turn_dir} {turn_angle:.1f}° ({turn_dur:.2f}s)")
            moves.append((turn_dir, turn_dur))
            robot_angle = target_angle

        dist = math.sqrt(dx * dx + dy * dy)
        dur = max(0.2, dist / pixels_per_second)
        moves.append(("forward", dur))
        print(f"Forward {dist:.1f}px ({dur:.2f}s)")

    return moves


# flask routes
@app.route("/path", methods=["POST"])
def receive_path():
    """Execute a drawn path"""
    try:
        data = request.json
        if not data or "pathPoints" not in data:
            return jsonify({"message": "No path data"}), 400

        coords = data["pathPoints"]
        if len(coords) < 2:
            return jsonify({"message": "Not enough coordinates"}), 400

        moves = coordinates_to_moves(coords)
        print(f"Executing {len(moves)} moves")

        for i, (direction, duration) in enumerate(moves):
            print(f"Move {i + 1}/{len(moves)}: {direction} ({duration:.2f}s)")
            move_car(direction, duration)

        return jsonify({"message": "Path executed successfully"}), 200
    except Exception as e:
        print(f"Path error: {e}")
        return jsonify({"message": str(e)}), 500


@app.route("/detection/start", methods=["POST"])
def start_detection_route():
    start_detection()
    return jsonify({"message": "Detection started"}), 200


@app.route("/detection/stop", methods=["POST"])
def stop_detection_route():
    stop_detection_thread()
    return jsonify({"message": "Detection stopped"}), 200


@app.route("/detection/status", methods=["GET"])
def detection_status():
    return jsonify({"object_detected": object_detected}), 200


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(
        {
            "status": "running",
            "motor_library": "freenove",
            "object_detected": object_detected,
        }
    )


# run flask server
if __name__ == "__main__":
    print("Starting Flask server")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        cleanup_gpio()
