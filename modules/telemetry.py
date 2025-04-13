# modules/telemetry.py

import asyncio
import json

TYPE = "telemetry"
ACTIONS = {
    "request_status": lambda data: None  # Optional placeholder
}

battery = 100.0
temp = 35.0
depth = 0.0
orientation = [0.0, 0.0, 0.0]

async def start_background_loop(send_func):
    while True:
        global battery, temp, depth, orientation
        battery = max(0, battery - 0.05)
        temp += 0.01
        depth += 0.02
        orientation = [(o + 0.01) % 1 for o in orientation]

        message = {
            "type": TYPE,
            "battery": round(battery, 1),
            "temp": round(temp, 1),
            "depth": round(depth, 2),
            "orientation": [round(o, 2) for o in orientation]
        }

        await send_func(json.dumps(message))
        await asyncio.sleep(1)
