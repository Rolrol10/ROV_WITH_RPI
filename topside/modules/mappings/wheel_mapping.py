# modules/controllers/mapping/wheel_mapping.py

# 🏎️ Wheel Face Buttons
BTN_A         = 0
BTN_B         = 1
BTN_X         = 2
BTN_Y         = 3
BTN_LB        = 4
BTN_RB        = 5
BTN_SELECT    = 6   # Back/View
BTN_START     = 7   # Start/Menu
BTN_XBOX      = 8   # Xbox logo button
BTN_LS        = 9   # Left stick press (if mapped)
BTN_RS        = 10  # Right stick press (if mapped)

# 🕹️ Shifter (if attached)
BTN_GEAR_1    = 12
BTN_GEAR_2    = 13
BTN_GEAR_3    = 14
BTN_GEAR_4    = 15
BTN_GEAR_5    = 16
BTN_GEAR_6    = 17
BTN_REVERSE   = 18  # Sometimes requires pushing down on stick or remapped

# 🎚️ Axis Mapping
AXIS_STEER    = 0   # Steering wheel (–1.0 to 1.0)
AXIS_BRAKE    = 1   # Brake pedal
AXIS_ACCEL    = 2   # Accelerator pedal
AXIS_CLUTCH   = 3   # Clutch pedal

# 🎯 D-pad via hat
# Access with: joystick.get_hat(0)
# Hat values:
#   (0, 1) = up
#   (0, -1) = down
#   (-1, 0) = left
#   (1, 0) = right
