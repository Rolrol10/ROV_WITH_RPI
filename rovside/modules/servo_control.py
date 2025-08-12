# modules/servo.py
# Print-only (no hardware) servo module keeping the same interface.

# --- Module type ---
TYPE = "servo"

# --- State ---
last_pan = 90
last_tilt = 90

# Only print updates if change >= threshold (degrees)
ANGLE_THRESHOLD = 2

def _maybe_int(v, fallback):
    try:
        return int(v)
    except Exception:
        return fallback

def set_angle(data):
    """
    Expects:
      { "type": "servo", "action": "set_angle", "pan": <0..180>, "tilt": <0..180> }
    Other keys are ignored.
    """
    global last_pan, last_tilt

    pan  = _maybe_int(data.get("pan",  last_pan),  last_pan)
    tilt = _maybe_int(data.get("tilt", last_tilt), last_tilt)

    # (Optional) clamp to sane range
    pan  = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    pan_changed  = abs(pan  - last_pan)  >= ANGLE_THRESHOLD
    tilt_changed = abs(tilt - last_tilt) >= ANGLE_THRESHOLD

    if pan_changed or tilt_changed:
        last_pan, last_tilt = pan, tilt
        print(f"🕹️ [SERVO] Pan={last_pan}°, Tilt={last_tilt}°")

# --- Actions ---
ACTIONS = {
    "set_angle": set_angle,
}
