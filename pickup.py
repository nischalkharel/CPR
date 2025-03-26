import serial
import json
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# Initialize I2C bus and PCA9685 at I2C address 0x40
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50  # Standard for most servos

# Initialize servo on channel 0
gripper_servo = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)  # Adjust min/max if needed

# Define Open and Close positions (increase range)
CLOSE_POS= 177.5   # Increase this value if not opening fully
OPEN_POS = 167  # Increase this value if not closing fully

# Set up serial connection
ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=1)
ser.setRTS(False)
ser.setDTR(False)

# File containing pre-recorded positions
pickup_position_file = "pickup_g8.json"
placedown_position_file = "placedown_g8.json"

# Function to send a command to the RoArm
def send_command(command):
    cmd_json = json.dumps(command) + "\n"
    ser.write(cmd_json.encode())
    time.sleep(0.5)  # Allow time for response

# Function to move the RoArm to a recorded position
def move_to_position(position):
    send_command({
        "T": 104, 
        "x": position["x"], 
        "y": position["y"], 
        "z": position["z"], 
        "t": position["t"],
        "spd": position["spd"],
        "acc": position["acc"]
    })
    print(f"Moving to X:{position['x']} Y:{position['y']} Z:{position['z']} T:{position['t']}")
    time.sleep(2)  # Wait for movement to complete

# Main script
def execute_positions(position_file):
    try:
        # Load positions from file
        with open(position_file, "r") as file:
            positions = json.load(file)

        print("=== Executing Pre-Recorded Positions from", position_file, "===")

        # Execute positions in order (sorted numerically)
        for key in sorted(positions.keys(), key=int):
            print(f"\nMoving to position {key}...")
            position = positions[key]
            move_to_position(position)

            if position.get("grab"):
                gripper_servo.angle = CLOSE_POS  # Trigger gripper to close

            if position.get("release"):
                gripper_servo.angle = OPEN_POS  # Trigger gripper to close

            time.sleep(.5)  # Small delay before next move

        print("Movement sequence complete!")

    except FileNotFoundError:
        print(f"Error: {position_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {position_file}.")
        
# Run the movement sequence
if __name__ == "__main__":
    gripper_servo.angle =  OPEN_POS
    execute_positions(pickup_position_file)
    execute_positions(placedown_position_file)
    
    ser.close()
