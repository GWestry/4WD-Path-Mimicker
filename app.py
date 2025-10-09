# app.py
import cv2
import numpy as np
import base64
import time
import atexit
import math
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- GPIO cleanup function ---
def cleanup_gpio():
    """Clean up GPIO resources on exit"""
    try:
        if 'car' in globals():
            print("Cleaning up Freenove motor...")
            car.set_motor_model(0, 0, 0, 0)
            car.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")

atexit.register(cleanup_gpio)

# --- Freenove library setup ---
try:
    import sys
    sys.path.append('/home/gwestry/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server')
    import motor
    car = motor.Ordinary_Car()
    print("Using Freenove motor library")
except ImportError as e:
    print(f"Freenove library not found: {e}")
    exit(1)

# --- Flask setup ---
app = Flask(__name__)
CORS(app)

# --- Motor movement functions ---
def move_car(direction, duration, speed=1000):
    print(f"Moving {direction} for {duration:.2f}s")
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
        time.sleep(duration)
        car.set_motor_model(0, 0, 0, 0)
    except Exception as e:
        print(f"Motor control error: {e}")

def coordinates_to_moves(coords, pixels_per_second=100, min_distance=20):
    """
    Convert drawing coordinates to robot movements.
    Filters out duplicate coordinates and tiny movements.
    Robot starts facing UP (270 degrees in standard math coordinates).
    """
    if len(coords) < 2:
        return []

    # Filter out duplicate coordinates and tiny movements
    filtered_coords = [coords[0]]  # Always keep first coordinate
    
    for i in range(1, len(coords)):
        x1, y1 = filtered_coords[-1]
        x2, y2 = coords[i]
        distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Only keep coordinates that are significantly far apart
        if distance >= min_distance:
            filtered_coords.append(coords[i])
    
    print(f"Filtered from {len(coords)} to {len(filtered_coords)} coordinates")
    print(f"Final coordinates: {filtered_coords}")
    
    if len(filtered_coords) < 2:
        return []

    moves = []
    robot_angle = 270  # Robot starts facing UP on canvas
    
    for i in range(1, len(filtered_coords)):
        x1, y1 = filtered_coords[i - 1]
        x2, y2 = filtered_coords[i]
        
        # Calculate target direction using math
        dx = x2 - x1
        dy = y2 - y1
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Normalize to 0-360 range
        while target_angle < 0:
            target_angle += 360
        while target_angle >= 360:
            target_angle -= 360
            
        # Calculate turn needed
        angle_diff = target_angle - robot_angle
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360
            
        print(f"Segment {i}: ({x1},{y1}) -> ({x2},{y2})")
        print(f"  Robot at {robot_angle:.1f}°, target {target_angle:.1f}°, turn {angle_diff:.1f}°")
        
        # Turn if angle difference > 30 degrees
        if abs(angle_diff) > 30:
            # REVERSED: left becomes right, right becomes left
            turn_direction = "right" if angle_diff > 0 else "left"
            # INCREASED: Add 20 degrees to the turn angle for more complete turns
            turn_angle = abs(angle_diff) + 20
            turn_duration = turn_angle / 90 * 0.5  # 0.5 seconds per 90 degrees
            print(f"  Turn {turn_direction} {turn_angle:.1f}° for {turn_duration:.2f}s")
            moves.append((turn_direction, turn_duration))
            robot_angle = target_angle
        
        # Always drive forward to reach the next coordinate
        distance = math.sqrt(dx*dx + dy*dy)
        drive_duration = max(0.2, distance / pixels_per_second)  # Minimum 0.2s duration
        print(f"  Drive forward {distance:.1f}px for {drive_duration:.2f}s")
        moves.append(("forward", drive_duration))
    
    return moves

# --- Flask endpoints ---
@app.route("/path", methods=["POST"])
def receive_path():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data received"}), 400

        # Use real-time drawing coordinates if available
        if "pathPoints" in data and data["pathPoints"]:
            coords = data["pathPoints"]
            print(f"Using real-time coordinates: {len(coords)} points")
        else:
            return jsonify({"message": "No path coordinates provided"}), 400

        if len(coords) < 2:
            return jsonify({"message": "Need at least 2 coordinates"}), 400

        # Convert coordinates to robot moves
        moves = coordinates_to_moves(coords)
        
        if not moves:
            return jsonify({"message": "No moves generated"}), 400

        print(f"Executing {len(moves)} moves:")
        
        # Execute each move
        for i, (direction, duration) in enumerate(moves):
            print(f"Move {i+1}/{len(moves)}: {direction} for {duration:.2f}s")
            move_car(direction, duration)
            time.sleep(0.1)  # Small pause between moves

        return jsonify({
            "message": "Path executed successfully",
            "moves_executed": len(moves),
            "coordinates_processed": len(coords)
        }), 200

    except Exception as e:
        print(f"Error processing path: {e}")
        return jsonify({"message": "Error processing path", "error": str(e)}), 500

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({"status": "running", "motor_library": "freenove"}), 200

# --- Run server ---
if __name__ == "__main__":
    print("Starting robot path server")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        cleanup_gpio()