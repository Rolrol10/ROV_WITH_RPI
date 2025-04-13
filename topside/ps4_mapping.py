# ps4_input_mapper.py

import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No joystick detected.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"✅ Controller connected: {joystick.get_name()}")
print("🕹️ Press buttons, move sticks, or press D-pad. Press Ctrl+C to exit.\n")

last_buttons = [0] * joystick.get_numbuttons()
last_axes = [0.0] * joystick.get_numaxes()
last_hats = [(0, 0)] * joystick.get_numhats()

try:
    while True:
        pygame.event.pump()

        # Buttons
        for i in range(joystick.get_numbuttons()):
            val = joystick.get_button(i)
            if val != last_buttons[i]:
                state = "pressed" if val else "released"
                print(f"🅱️  Button {i} {state}")
                last_buttons[i] = val

        # Axes
        for i in range(joystick.get_numaxes()):
            val = joystick.get_axis(i)
            if abs(val - last_axes[i]) > 0.1:  # Deadzone for printing
                print(f"🎚️  Axis {i}: {val:.2f}")
                last_axes[i] = val

        # Hats
        for i in range(joystick.get_numhats()):
            val = joystick.get_hat(i)
            if val != last_hats[i]:
                print(f"🎯 Hat {i}: {val}")
                last_hats[i] = val

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n👋 Exiting")

# ps4_constants.py

# Button Mappings
BTN_CROSS      = 0
BTN_CIRCLE     = 1
BTN_SQUARE     = 2
BTN_TRIANGLE   = 3
BTN_SHARE      = 4
BTN_PS         = 5
BTN_OPTIONS    = 6
BTN_L3         = 7
BTN_R3         = 8
BTN_L1         = 9
BTN_R1         = 10
# D-pad
HAT_UP         = 11
HAT_DOWN       = 12
HAT_LEFT       = 13
HAT_RIGHT      = 14
# Touchpad
BTN_TOUCHPAD   = 15

# Axis Mappings
AXIS_LX        = 0
AXIS_LY        = 1
AXIS_RX        = 2
AXIS_RY        = 3
AXIS_L2        = 4
AXIS_R2        = 5




