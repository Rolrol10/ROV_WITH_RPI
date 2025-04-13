# rov_topside.py

import asyncio
import importlib
from modules import network_handler, module_launcher, launch_gui

# 🎛️ Module toggle config
ENABLED_MODULES = {
    "relay": True,
    "joystick": False,
    "gui": True,
    "image_processor": False,
}

# 🧠 Track running modules
running_modules = {}

# 📥 Command queue for manual recovery GUI
command_queue = asyncio.Queue()

async def start_gui():
    print("🖥️ Launching GUI")
    launch_gui.launch_gui()


async def start_joystick():
    if running_modules.get("joystick"):
        print("🎮 Joystick already running")
        return
    print("🎮 Starting joystick module")
    controller = importlib.import_module("modules.joystick_ps4")
    running_modules["joystick"] = True
    try:
        await controller.run("ws://localhost:9999")
    except Exception as e:
        print(f"❌ Joystick error: {e}")
    running_modules["joystick"] = False

# 🔁 Command handler for manual button panel
async def handle_commands():
    while True:
        cmd = await command_queue.get()
        if cmd == "start_gui":
            await start_gui()
        elif cmd == "start_joystick":
            asyncio.create_task(start_joystick())
        elif cmd == "quit":
            print("🛑 Quit requested from GUI")
            break

async def main():
    print("🚀 ROV Topside Booting")

    if ENABLED_MODULES["relay"]:
        relay = network_handler.NetworkRelay()
        asyncio.create_task(relay.run())
        await asyncio.sleep(0.2)

    if ENABLED_MODULES["gui"]:
        await start_gui()

    if ENABLED_MODULES["joystick"]:
        asyncio.create_task(start_joystick())

    if ENABLED_MODULES["image_processor"]:
        print("🧠 Image processor placeholder enabled")

    # 🖲️ Start button launcher GUI with access to command_queue
    loop = asyncio.get_running_loop()
    module_launcher.launch_ui(command_queue, loop)


    # 🔁 Command queue listener
    await handle_commands()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Exiting ROV Topside")
