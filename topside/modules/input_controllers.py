# modules/input_controllers.py
import asyncio, json, time
from typing import Dict, Any, Optional
import pygame
import websockets
from modules.mappings.gamepad_mappings import (DETECT_HINTS, MAPPINGS, BINDINGS)
import contextlib

# -------- Tunables --------
DEADZONE = 0.10
SCALE = 90                 # stick -> degrees around 90
SEND_INTERVAL = 0.10       # min seconds between servo updates
DEBOUNCE = 0.35            # for one-shot bindings
KEEPALIVE_PING = 30
RECONNECT_DELAY = 1.0
SEND_RAW_EVENTS = False     # also emit "gamepad" events for everything
DEFAULT_FAILSAFE = {"type": "servo", "action": "set_angle", "pan": 90, "tilt": 90}

# --- Motion (throttle + turn) ---
THROTTLE_DZ_PCT = 8        # trigger deadzone in percent (0..100)
TURN_DZ = 0.08             # deadzone for right-stick X (turn)
DRIVE_SEND_INTERVAL = 0.1 # seconds between motion packets
DEFAULT_MOTION_FAILSAFE = {"type": "motor", "action": "set", "throttle": 0, "turn": 0}
MOTION_KEEPALIVE = 0.10   # seconds; MUST be < MCU watchdog timeout
SERVO_KEEPALIVE  = 1.0    # optional UI/state heartbeat for pan/tilt
# --------------------------

async def _drain(ws):
    # Read and discard everything (lets websockets handle ping/pong internally)
    try:
        async for _ in ws:
            pass
    except Exception:
        pass

def dz(v: float) -> float: return 0.0 if abs(v) < DEADZONE else v
def to_angle(v: float) -> int: return int(90 + v * SCALE)
def now() -> float: return time.monotonic()

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def trigger_pct(raw: float) -> int:
    """Map -1..1 or 0..1 trigger to 0..100 int."""
    if -1.001 <= raw <= 1.001:
        v = (raw + 1.0) * 0.5
    else:
        v = clamp(raw, 0.0, 1.0)
    return int(round(clamp(v, 0.0, 1.0) * 100))

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

async def _wait_for_controller(ws, prefer_guid=None, poll_s=0.05):
    """Send one-shot failsafe, then wait until a controller is present.
       Prefer previous GUID if available. Returns (js, name, guid)."""
    with contextlib.suppress(Exception):
        await ws.send(json.dumps(DEFAULT_FAILSAFE, separators=(',',':')))
        await ws.send(json.dumps(DEFAULT_MOTION_FAILSAFE, separators=(',',':')))
    print("🔌 Joystick disconnected. Waiting …")

    while True:
        await asyncio.sleep(poll_s)
        pygame.event.pump()
        with contextlib.suppress(Exception):
            pygame.joystick.quit(); pygame.joystick.init()

        n = pygame.joystick.get_count()
        if n == 0:
            continue

        # pick by GUID if possible
        idx = 0
        if prefer_guid:
            for i in range(n):
                j = pygame.joystick.Joystick(i); j.init()
                if hasattr(j, "get_guid") and j.get_guid() == prefer_guid:
                    idx = i
                    break

        # (re)create stick
        try:
            js = pygame.joystick.Joystick(idx); js.init()
            name = js.get_name()
            guid = js.get_guid() if hasattr(js, "get_guid") else None
        except Exception:
            continue  # race; try again

        print(f"✅ {name} reconnected" + (f" (guid {guid})" if guid else ""))
        await asyncio.sleep(0.05)  # tiny settle
        return js, name, guid
    
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

    # Motion state
    last_motion_sent = 0.0
    last_throttle: Optional[int] = None   # -100..100
    last_turn: Optional[int] = None       # -100..100

    while True:
        try:
            print(f"🔌 Connecting to {ws_url} …")
            async with websockets.connect(ws_url, ping_interval=(KEEPALIVE_PING-20), ping_timeout=KEEPALIVE_PING) as ws:
                print("✅ WebSocket connected")
                drain_task = asyncio.create_task(_drain(ws))
                
                while True:
                    pygame.event.pump()

                    # Hot-unplug handling (robust)
                    if pygame.joystick.get_count() == 0:
                        prefer_guid = js.get_guid() if 'js' in locals() and hasattr(js, "get_guid") else None
                        js, name, guid = await _wait_for_controller(ws, prefer_guid=prefer_guid)

                        # Re-detect mapping only if name suggests a different pad; otherwise keep previous
                        detected = None
                        for key, hints in DETECT_HINTS.items():
                            if any(h in name.lower() for h in hints):
                                detected = key; break
                        if detected and detected != ctrl_type:
                            ctrl_type = detected
                            mapping = MAPPINGS[ctrl_type]
                            binds   = BINDINGS.get(ctrl_type, {})
                            print(f"🎮 Mapping switched to: {ctrl_type}")
                        else:
                            print(f"🎮 Mapping kept: {ctrl_type}")

                        # Reset caches so change detection resumes cleanly
                        last_buttons = [0] * js.get_numbuttons()
                        last_hat = (0,0) if js.get_numhats() > 0 else None
                        last_pan = last_tilt = None
                        last_throttle = last_turn = None

                    # Resolve axes (servos on LEFT stick; RIGHT stick X reserved for turning)
                    rx, ry = mapping.get("AXIS_RX"), mapping.get("AXIS_RY")
                    lx, ly = mapping.get("AXIS_LX"), mapping.get("AXIS_LY")
                    lt_idx, rt_idx = mapping.get("AXIS_LT"), mapping.get("AXIS_RT")

                    # Left stick -> servo pan/tilt
                    try:
                        x = js.get_axis(lx) if lx is not None and lx < js.get_numaxes() else 0.0
                        y = js.get_axis(ly) if ly is not None and ly < js.get_numaxes() else 0.0
                    except Exception:
                        x = y = 0.0

                    # Left stick -> servo pan/tilt
                    pan = to_angle(dz(x))
                    tilt = to_angle(dz(-y))
                    t = now()
                    
                    servo_changed = (pan != last_pan or tilt != last_tilt)
                    if (servo_changed and (t - last_sent) >= SEND_INTERVAL) or ((t - last_sent) >= SERVO_KEEPALIVE):
                        await ws.send(json.dumps({
                            "type": "servo","action": "set_angle","pan": pan,"tilt": tilt
                        }, separators=(',',':')))
                        last_pan, last_tilt, last_sent = pan, tilt, t

                    # ---- Motion: throttle (-100..100) and turn (-100..100) ----
                    try:
                        lt_raw = js.get_axis(lt_idx) if lt_idx is not None and lt_idx < js.get_numaxes() else 0.0
                        rt_raw = js.get_axis(rt_idx) if rt_idx is not None and rt_idx < js.get_numaxes() else 0.0
                    except Exception:
                        lt_raw = rt_raw = 0.0

                    lt_pct = trigger_pct(float(lt_raw))  # 0..100
                    rt_pct = trigger_pct(float(rt_raw))  # 0..100

                    lt_eff = lt_pct if lt_pct > THROTTLE_DZ_PCT else 0
                    rt_eff = rt_pct if rt_pct > THROTTLE_DZ_PCT else 0

                    throttle = int(clamp(rt_eff - lt_eff, -100, 100))  # +forward, -reverse

                    # Right stick X -> signed percent -100..100 (0 idle)
                    try:
                        rx_val = js.get_axis(rx) if rx is not None and rx < js.get_numaxes() else 0.0
                    except Exception:
                        rx_val = 0.0
                    if abs(rx_val) < TURN_DZ:
                        turn = 0
                    else:
                        turn = int(round(clamp(float(rx_val), -1.0, 1.0) * 100))
                        turn = int(clamp(turn, -100, 100))

                    # Send on change (rate-limited), OR send a periodic keepalive when unchanged
                    motion_changed = (
                        last_throttle is None or last_turn is None or
                        throttle != last_throttle or turn != last_turn)
                    
                    if (motion_changed and (t - last_motion_sent) >= DRIVE_SEND_INTERVAL) \
                        or ((t - last_motion_sent) >= MOTION_KEEPALIVE):
                        await ws.send(json.dumps({
                            "type":"motor","action":"set","throttle":throttle,"turn":turn
                        }, separators=(',',':')))
                        last_throttle, last_turn, last_motion_sent = throttle, turn, t

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
                                    await ws.send(json.dumps(binds[bname], separators=(',',':')))
                                    print(f"🔘 Binding: {ctrl_type}.{bname} -> {binds[bname]}")
                                    last_bind_fire[bname] = t

                            if SEND_RAW_EVENTS:
                                await ws.send(json.dumps({
                                    "type":"gamepad","event":"button","controller":ctrl_type,
                                    "name":bname,"index":i,"pressed":pressed
                                }, separators=(',',':')))
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
                            }, separators=(',',':')))

                    # D-pad (hat)
                    hat_idx = mapping.get("HAT_0", 0)
                    if js.get_numhats() > hat_idx:
                        hat = js.get_hat(hat_idx)
                        if hat != last_hat:
                            if SEND_RAW_EVENTS:
                                await ws.send(json.dumps({
                                    "type":"gamepad","event":"hat","controller":ctrl_type,
                                    "index":hat_idx,"x":hat[0],"y":hat[1]
                                }, separators=(',',':')))
                            last_hat = hat

                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"⚠️ WS error: {e}. Reconnecting in {RECONNECT_DELAY}s …")
            await asyncio.sleep(RECONNECT_DELAY)
