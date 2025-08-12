# modules/controllers/mappings/gamepad_mappings.py

# Detection hints for controller naming across OS/drivers
DETECT_HINTS = {
    "ps4":  ["playstation", "ps4", "dualsense", "dualshock", "wireless controller"],
    "xbox": ["xbox"],
}

# Axis / button / hat indices (common SDL2-style layouts)
MAPPINGS = {
    "ps4": {
        # Axes
        "AXIS_LX": 0, "AXIS_LY": 1, "AXIS_RX": 2, "AXIS_RY": 3, "AXIS_LT": 4, "AXIS_RT": 5,
        # Buttons
        "BTN_SQUARE": 0, "BTN_CROSS": 1, "BTN_CIRCLE": 2, "BTN_TRIANGLE": 3,
        "BTN_L1": 4, "BTN_R1": 5, "BTN_L2": 6, "BTN_R2": 7,
        "BTN_SHARE": 8, "BTN_OPTIONS": 9, "BTN_L3": 10, "BTN_R3": 11,
        "BTN_PS": 12, "BTN_TOUCHPAD": 13,
        # D-pad
        "HAT_0": 0,
    },
    "xbox": {
        # Axes
        "AXIS_LX": 0, "AXIS_LY": 1, "AXIS_RX": 2, "AXIS_RY": 3, "AXIS_LT": 4, "AXIS_RT": 5,
        # Buttons
        "BTN_A": 0, "BTN_B": 1, "BTN_X": 2, "BTN_Y": 3,
        "BTN_LB": 4, "BTN_RB": 5, "BTN_BACK": 6, "BTN_START": 7, "BTN_GUIDE": 8,
        "BTN_LS": 9, "BTN_RS": 10,
        # D-pad
        "HAT_0": 0,
    },
}

# Per-controller action bindings you want fired on button press (debounced)
BINDINGS = {
    "ps4": {
        "BTN_CIRCLE": {"type": "stream", "action": "start_stream"},
        "BTN_CROSS":  {"type": "stream", "action": "stop_stream"},
        "BTN_SQUARE": {"type": "stream", "action": "restart_stream"},
    },
    "xbox": {
        "BTN_B": {"type": "stream", "action": "start_stream"},
        "BTN_A": {"type": "stream", "action": "stop_stream"},
        "BTN_X": {"type": "stream", "action": "restart_stream"},
    },
}
