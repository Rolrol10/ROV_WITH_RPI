import asyncio
import subprocess
import threading
import importlib
import os
import websockets
import json

MODULES = []

def load_modules():
    for file in os.listdir("modules"):
        if file.endswith(".py") and not file.startswith("__"):
            mod_name = file[:-3]
            module = importlib.import_module(f"modules.{mod_name}")
            MODULES.append(module)
            print(f"✅ Loaded module: {mod_name}")

async def handler(websocket):
    print("🟢 WebSocket client connected.")
    try:
        async for message in websocket:
            data = json.loads(message)
            for mod in MODULES:
                mod.handle(data)
    except websockets.exceptions.ConnectionClosed:
        print("🔴 WebSocket client disconnected.")

async def websocket_server():
    load_modules()
    print("🚀 Starting WebSocket control server...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

def start_camera_stream():
    print("🎥 Starting camera stream...")
    gst_command = (
        "libcamera-vid --codec h264 --inline --framerate 30 "
        "--mode 1640:1232:30/1 --width 640 --height 480 --timeout 0 -o - | "
        "gst-launch-1.0 fdsrc ! h264parse config-interval=1 ! "
        "rtph264pay pt=96 config-interval=1 ! udpsink host=10.253.0.9 port=8554"
    )
    subprocess.Popen(gst_command, shell=True, executable="/bin/bash")

if __name__ == "__main__":
    threading.Thread(target=start_camera_stream, daemon=True).start()
    asyncio.run(websocket_server())
