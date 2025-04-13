import pygame
import asyncio
import websockets
import json

# Controller-specific classes or modules
from controllers.mappings.ps4_mapping import *
from . import xbox_mapping
from . import wheel_mapping

TYPE = "servo"
ACTION = "set_angle"

DEADZONE = 0.1
SCALE = 90
SEND_INTERVAL = 0.1

STREAM_TYPE = "stream"




BUTTON_MAP = {
    "start_stream": BTN_CIRCLE,
    "stop_stream": BTN_CROSS,
    "restart_stream": BTN_SQUARE,
}

DEBOUNCE_TIME = 0.5
last_button_time = 0

DEFAULT_FAILSAFE_COMMAND = {
    "type": TYPE,
    "action": ACTION,
    "pan": 90,
    "tilt": 90
}

def normalize(value):
    return int(90 + value * SCALE)

def apply_deadzone(value):
    return 0.0 if abs(value) < DEADZONE else value

async def keep_connection_alive(ws):
    """Background task to keep the websocket alive by listening for pings."""
    try:
        async for _ in ws:
            pass  # We ignore messages, but this keeps the connection open
    except websockets.ConnectionClosed:
        print("🔌 Keepalive: WebSocket closed")

async def run(ws_url):
    global last_button_time

    pygame.init()
    pygame.joystick.init()

    joystick = None
    was_connected = False

    try:
        async with websockets.connect(ws_url, ping_interval=30, ping_timeout=20) as ws:
            print(f"🔗 Connected to topside ws relay at: {ws_url}")

            # Start listener task to keep connection responsive
            asyncio.create_task(keep_connection_alive(ws))

            while True:
                pygame.event.pump()
                joystick_count = pygame.joystick.get_count()

                if joystick_count == 0:
                    if was_connected:
                        print("⚠️ Joystick disconnected! Sending failsafe.")
                        await ws.send(json.dumps(DEFAULT_FAILSAFE_COMMAND))
                        was_connected = False
                    await asyncio.sleep(1)
                    continue

                if not was_connected:
                    joystick = pygame.joystick.Joystick(0)
                    joystick.init()
                    print(f"✅ {joystick.get_name()} reconnected")
                    was_connected = True

                x = apply_deadzone(joystick.get_axis(AXIS_RX))
                y = apply_deadzone(joystick.get_axis(AXIS_RY))

                pan = normalize(x)
                tilt = normalize(-y)

                command = {
                    "type": TYPE,
                    "action": ACTION,
                    "pan": pan,
                    "tilt": tilt
                }

                try:
                    await ws.send(json.dumps(command))

                    for action, button_index in BUTTON_MAP.items():
                        if joystick.get_button(button_index):
                            now = pygame.time.get_ticks()
                            if now - last_button_time > DEBOUNCE_TIME * 1000:
                                stream_cmd = {
                                    "type": STREAM_TYPE,
                                    "action": action
                                }
                                await ws.send(json.dumps(stream_cmd))
                                print(f"🎬 Sent stream command: {action}")
                                last_button_time = now

                except websockets.ConnectionClosed:
                    print("🔌 Joystick WebSocket disconnected.")
                    return

                await asyncio.sleep(SEND_INTERVAL)

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
