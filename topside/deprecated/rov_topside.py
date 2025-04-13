import asyncio
import importlib
import os
import websockets

PI_WS_URL = "ws://10.253.0.10:8765"
CONTROL_MODULES = ["joystick_ps4"]

async def load_module(name, ws):
    try:
        mod = importlib.import_module(f"modules.{name}")
        if hasattr(mod, "run"):
            print(f"✅ Starting {name}")
            await mod.run(ws)
    except Exception as e:
        print(f"❌ Failed to load {name}: {e}")

async def main():
    async with websockets.connect(PI_WS_URL) as ws:
        await asyncio.gather(*(load_module(name, ws) for name in CONTROL_MODULES))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutdown")