# modules/controllers/mapping/xbox_constants.py

# 🎮 Button Mappings
BTN_A        = 0
BTN_B        = 1
BTN_X        = 2
BTN_Y        = 3
BTN_LB       = 4
BTN_RB       = 5
BTN_BACK     = 6
BTN_START    = 7
BTN_GUIDE    = 8
BTN_LS       = 9
BTN_RS       = 10

# 🎯 D-pad (if buttons, not hat)
# Some systems expose D-pad as button 11–14:
BTN_DPAD_UP    = 11
BTN_DPAD_DOWN  = 12
BTN_DPAD_LEFT  = 13
BTN_DPAD_RIGHT = 14

# 🎚️ Axis Mappings
AXIS_LX      = 0
AXIS_LY      = 1
AXIS_RX      = 3
AXIS_RY      = 4
AXIS_LT      = 2  # Left trigger (0 to 1)
AXIS_RT      = 5  # Right trigger (0 to 1)

# Note: Some systems report LT/RT as a shared axis (-1 to +1) on AXIS 2 — adjust as needed
