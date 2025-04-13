import pygame
import requests
import time

# --- Setup ---
PI_HOST = "http://10.253.0.10:5050/move"
PAN_CENTER = 90
TILT_CENTER = 90
PAN_RANGE = 90
TILT_RANGE = 90
DEADZONE = 0.1  # Analog range: 0.0 to 1.0

pan = PAN_CENTER
tilt = TILT_CENTER
last_sent = (pan, tilt)

def clamp(val, min_val=0, max_val=180):
    return max(min_val, min(max_val, int(val)))

def send_position(pan, tilt):
    global last_sent
    if (pan, tilt) != last_sent:
        try:
            requests.post(PI_HOST, json={"pan": pan, "tilt": tilt}, timeout=0.1)
            last_sent = (pan, tilt)
        except:
            print("⚠️ Could not reach Pi")

# Init pygame
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No controller found. Plug in your PS4 controller.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"🎮 Connected: {joystick.get_name()}")

# Main loop
while True:
    pygame.event.pump()  # Required to read input

    lx = joystick.get_axis(2)  # Left stick X
    ly = joystick.get_axis(3)  # Left stick Y

    # Apply deadzone
    lx = lx if abs(lx) > DEADZONE else 0
    ly = ly if abs(ly) > DEADZONE else 0

    # Scale and invert Y
    pan = clamp(PAN_CENTER + lx * PAN_RANGE)
    tilt = clamp(TILT_CENTER - ly * TILT_RANGE)

    send_position(pan, tilt)
    time.sleep(0.05)
