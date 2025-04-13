from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# --- Module type ---

TYPE = "servo"

# Actions list at bottom of file

# --- Setup ---
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

pan_servo = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)
tilt_servo = servo.Servo(pca.channels[4], min_pulse=500, max_pulse=2500)

# --- Initial positions ---
last_pan = 90
last_tilt = 90
pan_servo.angle = last_pan
tilt_servo.angle = last_tilt

# --- Threshold in degrees ---
ANGLE_THRESHOLD = 2

def set_angle(data):
    global last_pan, last_tilt

    # if data.get("type") != "servo":
    #     return

    pan = int(data.get("pan", last_pan))
    tilt = int(data.get("tilt", last_tilt))

    pan_changed = abs(pan - last_pan) >= ANGLE_THRESHOLD
    tilt_changed = abs(tilt - last_tilt) >= ANGLE_THRESHOLD

    if pan_changed:
        pan_servo.angle = pan
        last_pan = pan

    if tilt_changed:
        tilt_servo.angle = tilt
        last_tilt = tilt

    if pan_changed or tilt_changed:
        print(f"🕹️ Updated → Pan: {last_pan}, Tilt: {last_tilt}")

# --- Actions ---

ACTIONS = {
    "set_angle": set_angle,
    # "calibrate": calibrate,
}