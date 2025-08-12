#!/usr/bin/env python3
# universal_controller.py
# Python 3.13.6 ONLY – auto-installs deps, unifies PS4/Xbox, single-controller,
# built-in tester (default) and WebSocket control loop (--ws).
# Prints button presses/releases so you can verify input.

import sys, subprocess, argparse, time, asyncio, json
from typing import Optional, Tuple, Dict, TYPE_CHECKING

# ---- Version hard-check (exact 3.13.6 to avoid mixed-DLL issues on Windows) --
REQ_MAJOR, REQ_MINOR, REQ_MICRO = 3, 13, 6
if sys.version_info[:3] != (REQ_MAJOR, REQ_MINOR, REQ_MICRO):
    raise RuntimeError(
        f"This script is locked to Python {REQ_MAJOR}.{REQ_MINOR}.{REQ_MICRO}. "
        f"You are running {sys.version.split()[0]}."
    )

# ----------------------- Auto-install missing packages ------------------------
def ensure_package(pkg_name, import_name=None):
    import_name = import_name or pkg_name
    try:
        return __import__(import_name)
    except ImportError:
        print(f"[Installer] Missing '{pkg_name}', installing for {sys.executable}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        except Exception:
            pass
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
        return __import__(import_name)

# Prefer pygame-ce (has 3.13 wheels). Import it as 'pygame'.
pygame = ensure_package("pygame-ce", "pygame")
websockets = ensure_package("websockets")

# For type-checkers only (prevents Pylance reportInvalidTypeForm)
if TYPE_CHECKING:
    import pygame as pygame_mod
    import websockets as websockets_mod

# ======================= Public, importable mappings ==========================
BUTTONS: Dict[str, int] = {}   # e.g. BUTTONS["A"], BUTTONS["CIRCLE"], BUTTONS["L1"]
AXES:    Dict[str, int] = {}   # e.g. AXES["RIGHT_STICK_X"], AXES["LT"], AXES["L2"]

# Sensitivity / timing
DEADZONE: float = 0.1
SCALE: int = 90
SEND_INTERVAL: float = 0.1
DEBOUNCE_TIME: float = 0.5

DEFAULT_FAILSAFE_COMMAND = {"type": "servo", "action": "set_angle", "pan": 90, "tilt": 90}

# --------------------------------- Mapping -----------------------------------
class ControllerMapping:
    def __init__(self, rx: int, ry: int): self.axis_rx, self.axis_ry = rx, ry
    @staticmethod
    def for_ps4():  return ControllerMapping(2, 3)  # RX, RY
    @staticmethod
    def for_xbox(): return ControllerMapping(3, 4)

def detect_controller_type() -> Tuple[
    Optional[str],
    Optional[ControllerMapping],
    Optional["pygame_mod.joystick.Joystick"]  # type: ignore[name-defined]
]:
    pygame.init(); pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("❌ No joystick detected. Connect a PS4/Xbox controller."); return None, None, None
    js = pygame.joystick.Joystick(0); js.init()
    name = (js.get_name() or "").lower()
    if "xbox" in name:
        print(f"✅ Xbox controller detected: {js.get_name()}"); return "xbox", ControllerMapping.for_xbox(), js
    if any(k in name for k in ("playstation", "ps4", "dualshock", "wireless")):
        print(f"✅ PS4 controller detected: {js.get_name()}"); return "ps4", ControllerMapping.for_ps4(), js
    print(f"⚠️ Unknown controller '{js.get_name()}'; defaulting to PS4 layout")
    return "ps4", ControllerMapping.for_ps4(), js

def _apply_deadzone(v: float) -> float: return 0.0 if abs(v) < DEADZONE else v
def _normalize(v: float) -> int: return int(90 + v * SCALE)

def _set_runtime_mappings(controller_type: str, m: ControllerMapping) -> None:
    BUTTONS.clear(); AXES.clear()
    if controller_type == "ps4":
        BUTTONS.update({
            "CROSS":0,"A":0,"CIRCLE":1,"B":1,"SQUARE":2,"X":2,"TRIANGLE":3,"Y":3,
            "SHARE":4,"PS":5,"OPTIONS":6,"START":6,"L3":7,"LS":7,"R3":8,"RS":8,
            "L1":9,"LB":9,"R1":10,"RB":10,"TOUCHPAD":15,
            "DPAD_UP":11,"DPAD_DOWN":12,"DPAD_LEFT":13,"DPAD_RIGHT":14
        })
        AXES.update({
            "LEFT_STICK_X":0,"LEFT_STICK_Y":1,"RIGHT_STICK_X":m.axis_rx,"RIGHT_STICK_Y":m.axis_ry,
            "L2":4,"LT":4,"R2":5,"RT":5
        })
    else:
        BUTTONS.update({
            "A":0,"CROSS":0,"B":1,"CIRCLE":1,"X":2,"SQUARE":2,"Y":3,"TRIANGLE":3,
            "LB":4,"L1":4,"RB":5,"R1":5,"BACK":6,"SELECT":6,"SHARE":6,
            "START":7,"OPTIONS":7,"GUIDE":8,"XBOX":8,"PS":8,"LS":9,"L3":9,"RS":10,"R3":10,
            "DPAD_UP":11,"DPAD_DOWN":12,"DPAD_LEFT":13,"DPAD_RIGHT":14
        })
        AXES.update({
            "LEFT_STICK_X":0,"LEFT_STICK_Y":1,"RIGHT_STICK_X":m.axis_rx,"RIGHT_STICK_Y":m.axis_ry,
            "LT":2,"L2":2,"RT":5,"R2":5
        })

# -------- Helpers to make pretty names + summary & live button logging --------
AXIS_PRINT_STEP = 0.05  # tester print threshold

def _rev_button_names() -> Dict[int, str]:
    rev: Dict[int, set] = {}
    for name, idx in BUTTONS.items(): rev.setdefault(idx, set()).add(name)
    priority = ["A","B","X","Y","CROSS","CIRCLE","SQUARE","TRIANGLE","L1","R1","L2","R2","LB","RB","LT","RT"]
    disp: Dict[int, str] = {}
    for idx, names in rev.items():
        ordered = sorted(names, key=lambda n: (priority.index(n) if n in priority else 999, n))
        disp[idx] = " / ".join(ordered)
    return disp

def _rev_axis_names() -> Dict[int, str]:
    rev: Dict[int, set] = {}
    for name, idx in AXES.items(): rev.setdefault(idx, set()).add(name)
    priority = ["LEFT_STICK_X","LEFT_STICK_Y","RIGHT_STICK_X","RIGHT_STICK_Y","LT","RT","L2","R2"]
    disp: Dict[int, str] = {}
    for idx, names in rev.items():
        ordered = sorted(names, key=lambda n: (priority.index(n) if n in priority else 999, n))
        disp[idx] = " / ".join(ordered)
    return disp

def _print_mapping_summary(js: "pygame_mod.joystick.Joystick") -> None:  # type: ignore[name-defined]
    print("\n--- Mapping summary ---")
    btn_names = _rev_button_names()
    axis_names = _rev_axis_names()
    print("Buttons:")
    for i in range(js.get_numbuttons()):
        print(f"  {i:02d}: {btn_names.get(i, f'BUTTON_{i}')}")
    print("Axes:")
    for i in range(js.get_numaxes()):
        print(f"  {i:02d}: {axis_names.get(i, f'AXIS_{i}')}")
    print("Hats:", js.get_numhats())
    print("-----------------------\n")

# --------------------------- WebSocket control loop ---------------------------
async def _keepalive(ws: "websockets_mod.WebSocketClientProtocol") -> None:  # type: ignore[name-defined]
    try:
        async for _ in ws: pass
    except websockets.ConnectionClosed:
        print("⚠️ Keep-alive: WebSocket closed")

async def run(ws_url: str) -> None:
    ctype, mapping, js = detect_controller_type()
    if not all([ctype, mapping, js]): return
    _set_runtime_mappings(ctype, mapping)
    _print_mapping_summary(js)  # show what the script believes the mapping is

    button_start, button_stop, button_restart = BUTTONS["B"], BUTTONS["A"], BUTTONS["X"]
    dynamic = {"start_stream": button_start, "stop_stream": button_stop, "restart_stream": button_restart}

    last_sent_time = 0.0
    last_pan = last_tilt = None
    last_btn_ts = 0

    # Track button state to print presses/releases live
    n_buttons = js.get_numbuttons()
    last_buttons = [0] * n_buttons

    try:
        async with websockets.connect(ws_url, ping_interval=30, ping_timeout=20) as ws:
            print(f"🔌 Connected to ws relay: {ws_url}")
            asyncio.create_task(_keepalive(ws))
            while True:
                pygame.event.pump()
                if pygame.joystick.get_count() == 0:
                    print("⚠️ Controller disconnected! Sending fail-safe.")
                    await ws.send(json.dumps(DEFAULT_FAILSAFE_COMMAND)); await asyncio.sleep(1); continue

                # Live button press/release logging
                btn_names = _rev_button_names()
                for i in range(n_buttons):
                    val = js.get_button(i)
                    if val != last_buttons[i]:
                        print(f"[BTN] {i:02d} — {btn_names.get(i, f'BUTTON_{i}'):<22} -> {'PRESSED' if val else 'RELEASED'}")
                        last_buttons[i] = val

                # Right stick controls pan/tilt
                x = _apply_deadzone(js.get_axis(AXES["RIGHT_STICK_X"]))
                y = _apply_deadzone(js.get_axis(AXES["RIGHT_STICK_Y"]))
                pan, tilt = _normalize(x), _normalize(-y)

                now = pygame.time.get_ticks() / 1000.0
                if (pan != last_pan or tilt != last_tilt) and (now - last_sent_time) > SEND_INTERVAL:
                    await ws.send(json.dumps({"type":"servo","action":"set_angle","pan":pan,"tilt":tilt}))
                    last_pan, last_tilt, last_sent_time = pan, tilt, now

                # Stream control buttons (debounced)
                for action, btn in dynamic.items():
                    if js.get_button(btn):
                        ticks = pygame.time.get_ticks()
                        if ticks - last_btn_ts > DEBOUNCE_TIME * 1000:
                            await ws.send(json.dumps({"type":"stream","action":action}))
                            print(f"🕹️ Sent stream command: {action}")
                            last_btn_ts = ticks

                await asyncio.sleep(0.01)
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

# --------------------------------- Tester (default) ---------------------------
def _test_loop() -> None:
    ctype, mapping, js = detect_controller_type()
    if not all([ctype, mapping, js]): return
    _set_runtime_mappings(ctype, mapping)
    _print_mapping_summary(js)

    btn_names = _rev_button_names()
    axis_names = _rev_axis_names()

    n_buttons, n_axes, n_hats = js.get_numbuttons(), js.get_numaxes(), js.get_numhats()
    print("\n=== Controller Test Ready ===")
    print(f"Buttons: {n_buttons}, Axes: {n_axes}, Hats: {n_hats}")
    print("Press buttons / move sticks. Ctrl+C to exit.\n")

    last_buttons = [0] * n_buttons
    last_axes = [0.0] * n_axes
    last_hats = [(0,0)] * n_hats
    last_axis_print = [time.time()] * n_axes

    try:
        while True:
            pygame.event.pump()
            if pygame.joystick.get_count() == 0:
                print("⚠️ Controller disconnected. Exiting tester."); break

            # Buttons (live prints)
            for i in range(n_buttons):
                v = js.get_button(i)
                if v != last_buttons[i]:
                    print(f"Button {i:02d} — {btn_names.get(i, f'BUTTON_{i}'):<22} -> {'PRESSED' if v else 'RELEASED'}")
                    last_buttons[i] = v

            # Axes (print on threshold or after 150ms)
            now = time.time()
            for i in range(n_axes):
                raw = js.get_axis(i)
                v = 0.0 if abs(raw) < DEADZONE else raw
                if abs(v - last_axes[i]) >= AXIS_PRINT_STEP or (now - last_axis_print[i]) > 0.15:
                    if abs(v - last_axes[i]) >= AXIS_PRINT_STEP:
                        print(f"Axis   {i:02d} — {axis_names.get(i, f'AXIS_{i}'):<22} -> {v:+.2f}")
                        last_axes[i] = v
                        last_axis_print[i] = now

            # D-Pad (hat)
            for h in range(n_hats):
                xy = js.get_hat(h)
                if xy != last_hats[h]:
                    print(f"Hat    {h:02d} — DPAD (x={xy[0]}, y={xy[1]})")
                    last_hats[h] = xy

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n👋 Bye!")
    finally:
        pygame.quit()

# ----------------------------------- CLI -------------------------------------
def _parse_args():
    p = argparse.ArgumentParser(description="Universal PS4/Xbox controller handler (Python 3.13.6)")
    p.add_argument("--ws", help="WebSocket URL to topside relay (run control loop)")
    # Keeping --test for compatibility, but default is test mode if no --ws is provided.
    p.add_argument("--test", action="store_true", help="Run standalone tester (prints input events)")
    return p.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    # VS Code-friendly: default to TEST mode when run without args
    if args.ws:
        asyncio.run(run(args.ws))
    else:
        _test_loop()