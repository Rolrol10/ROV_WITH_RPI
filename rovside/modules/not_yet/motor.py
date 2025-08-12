#!/usr/bin/env python3
# motor.py — dual motor module using spi_link.SPODriver
# Mirrors the structure of your servo.py (TYPE + ACTIONS)

import atexit
from rovside.modules.not_yet.spi_link import SPIDriver

# --- Module type ---
TYPE = "motor"

# --- Config ---
# If you use CE0: bus=0, device=0. For CE1: device=1.
SPI_BUS = 0
SPI_DEV = 0
CHANGE_THRESHOLD = 2   # percent change before sending new command

# --- State ---
_link = SPIDriver(bus=SPI_BUS, device=SPI_DEV, max_hz=1_000_000, mode=0)
_last_left  = 0
_last_right = 0

def _mix_speed_steer(speed, steer):
    """Mix arcade inputs into left/right: both in -100..100."""
    s = max(-100, min(100, int(speed)))
    t = max(-100, min(100, int(steer)))
    left  = max(-100, min(100, s + t))
    right = max(-100, min(100, s - t))
    return left, right

def _changed(a, b, th=CHANGE_THRESHOLD):
    return abs(a - b) >= th

def set_speed(data):
    """
    Data can be one of:
      { "left": -100..100, "right": -100..100 }
      { "speed": -100..100, "steer": -100..100 }
    """
    global _last_left, _last_right

    if "left" in data or "right" in data:
        left  = int(data.get("left",  _last_left))
        right = int(data.get("right", _last_right))
    else:
        speed = int(data.get("speed", 0))
        steer = int(data.get("steer", 0))
        left, right = _mix_speed_steer(speed, steer)

    send = _changed(left, _last_left) or _changed(right, _last_right)
    if send:
        _link.drive(left, right)
        _last_left, _last_right = left, right
        print(f"🛞 Updated → L: {left:>4}%, R: {right:>4}%")

def stop(_data=None):
    global _last_left, _last_right
    _link.stop()
    _last_left, _last_right = 0, 0
    print("🛑 Motors stopped")

def close(_data=None):
    try:
        stop()
    finally:
        _link.close()
        print("🔌 SPI link closed")

atexit.register(close)

# --- Actions ---
ACTIONS = {
    "set_speed": set_speed,  # accepts left/right OR speed/steer
    "stop":      stop,
    "close":     close,
}
