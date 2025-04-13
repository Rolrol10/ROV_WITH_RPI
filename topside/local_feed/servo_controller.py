import requests
import time

# Pi IP
PI_IP = "192.168.2.185"

def move_servo(pan, tilt):
    requests.post(f"http://{PI_IP}:5050/move", json={"pan": pan, "tilt": tilt})

# move_servo(90, 90)  # Center
# move_servo(120, 80) # Turn

move_servo(0, 0)
time.sleep(1)
move_servo(180,180)
time.sleep(1)