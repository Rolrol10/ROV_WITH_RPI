# modules/input_controllers.py
import asyncio, json, time
from typing import Dict, Any, Optional
import pygame
import websockets
from modules.mappings.gamepad_mappings import (DETECT_HINTS, MAPPINGS, BINDINGS)

# -------- Tunables --------
DEADZONE = 0.10
SCALE = 90                 # stick -> degrees around 90
SEND_INTERVAL = 0.10       # min seconds between servo updates
DEBOUNCE = 0.35            # for one-shot bindings
KEEPALIVE_PING = 30
RECONNECT_DELAY = 1.0
SEND_RAW_EVENTS = False     # also emit "gamepad" events for everything
DEFAULT_FAILSAFE = {"type": "servo", "action": "set_angle", "pan": 90, "tilt": 90}
# --------------------------

def dz(v: float) -> float: return 0.0 if abs(v) < DEADZONE else v
def to_angle(v: float) -> int: return int(90 + v * SCALE)
def now() -> float: return time.monotonic()

def _button_name(map_: dict, idx: int) -> str:
    for k, v in map_.items():
        if k.startswith("BTN_") and v == idx: return k
    return f"BTN_{idx}"

def _axis_name(map_: dict, idx: int) -> str:
    for k, v in map_.items():
        if k.startswith("AXIS_") and v == idx: return k
    return f"AXIS_{idx}"

def _detect_type() -> Optional[str]:
    pygame.init(); pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("❌ No joystick detected.")
        return None
    name = pygame.joystick.Joystick(0).get_name().lower()
    print(f"🎮 Detected controller name: {name}")
    for key, hints in DETECT_HINTS.items():
        if any(h in name for h in hints):
            return key
    print("⚠️ Unknown controller type, defaulting to ps4 mapping")
    return "ps4"

async def run(ws_url: str):
    ctrl_type = _detect_type()
    if not ctrl_type: return

    mapping = MAPPINGS[ctrl_type]
    binds: Dict[str, Dict[str, Any]] = BINDINGS.get(ctrl_type, {})
    print(f"🕹️ Using mapping: {ctrl_type}")

    js = pygame.joystick.Joystick(0); js.init()
    print(f"   axes={js.get_numaxes()} buttons={js.get_numbuttons()} hats={js.get_numhats()}")

    last_sent = 0.0
    last_pan = last_tilt = None
    last_buttons = [0] * js.get_numbuttons()
    last_hat = (0,0) if js.get_numhats() > 0 else None
    last_bind_fire: Dict[str, float] = {}

    while True:
        try:
            print(f"🔌 Connecting to {ws_url} …")
            async with websockets.connect(ws_url, ping_interval=KEEPALIVE_PING, ping_timeout=KEEPALIVE_PING) as ws:
                print("✅ WebSocket connected")

                while True:
                    pygame.event.pump()

                    # Hot-unplug handling
                    if pygame.joystick.get_count() == 0:
                        print("🔌 Joystick disconnected. Waiting …")
                        await ws.send(json.dumps(DEFAULT_FAILSAFE))
                        while pygame.joystick.get_count() == 0:
                            await asyncio.sleep(0.5)
                        js = pygame.joystick.Joystick(0); js.init()
                        print(f"✅ {js.get_name()} reconnected")
                        last_buttons = [0] * js.get_numbuttons()
                        last_hat = (0,0) if js.get_numhats() > 0 else None
                        last_pan = last_tilt = None

                    # Right stick -> servo pan/tilt
                    rx, ry = mapping.get("AXIS_RX"), mapping.get("AXIS_RY")
                    try:
                        x = js.get_axis(rx) if rx is not None and rx < js.get_numaxes() else 0.0
                        y = js.get_axis(ry) if ry is not None and ry < js.get_numaxes() else 0.0
                    except Exception:
                        x = y = 0.0

                    pan = to_angle(dz(x))
                    tilt = to_angle(dz(-y))
                    t = now()
                    if (pan != last_pan or tilt != last_tilt) and (t - last_sent) >= SEND_INTERVAL:
                        await ws.send(json.dumps({
                            "type": "servo","action": "set_angle","pan": pan,"tilt": tilt
                        }))
                        last_pan, last_tilt, last_sent = pan, tilt, t

                    # Buttons (edge-triggered)
                    for i in range(js.get_numbuttons()):
                        val = 1 if js.get_button(i) else 0
                        if val != last_buttons[i]:
                            pressed = bool(val)
                            bname = _button_name(mapping, i)

                            # Fire binding on press (debounced)
                            if pressed and bname in binds:
                                last_fire = last_bind_fire.get(bname, 0.0)
                                if (t - last_fire) >= DEBOUNCE:
                                    await ws.send(json.dumps(binds[bname]))
                                    print(f"🔘 Binding: {ctrl_type}.{bname} -> {binds[bname]}")
                                    last_bind_fire[bname] = t

                            if SEND_RAW_EVENTS:
                                await ws.send(json.dumps({
                                    "type":"gamepad","event":"button","controller":ctrl_type,
                                    "name":bname,"index":i,"pressed":pressed
                                }))
                            last_buttons[i] = val

                    # Axes (analog) — includes triggers
                    if SEND_RAW_EVENTS:
                        for ax_idx in range(js.get_numaxes()):
                            try:
                                val = float(js.get_axis(ax_idx))
                            except Exception:
                                continue
                            await ws.send(json.dumps({
                                "type":"gamepad","event":"axis","controller":ctrl_type,
                                "name":_axis_name(mapping, ax_idx),"index":ax_idx,"value":round(val,3)
                            }))

                    # D-pad (hat)
                    hat_idx = mapping.get("HAT_0", 0)
                    if js.get_numhats() > hat_idx:
                        hat = js.get_hat(hat_idx)
                        if hat != last_hat:
                            if SEND_RAW_EVENTS:
                                await ws.send(json.dumps({
                                    "type":"gamepad","event":"hat","controller":ctrl_type,
                                    "index":hat_idx,"x":hat[0],"y":hat[1]
                                }))
                            last_hat = hat

                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"⚠️ WS error: {e}. Reconnecting in {RECONNECT_DELAY}s …")
            await asyncio.sleep(RECONNECT_DELAY)
