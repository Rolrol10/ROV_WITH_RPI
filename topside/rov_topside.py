# rov_topside.py (refactored with class-based module management)

import asyncio
import importlib
from modules import network_handler, module_launcher, launch_gui

# 🎛️ Module toggle config
ENABLED_MODULES = {
    "relay": True,              # Has to run for ws between modules on topside to work
    "input_controllers": False,
    "gui": False,
    "image_processor": False,
}

class TopsideController:
    def __init__(self):
        self.running_tasks = {}
        self.command_queue = asyncio.Queue()
        self.loop = None  # Will be set later in run()

    async def start_relay(self):
        print("📡 Starting relay")
        relay = network_handler.NetworkRelay()
        task = asyncio.create_task(relay.run())
        self.running_tasks["relay"] = task
        await asyncio.sleep(0.2)

    async def start_gui(self):
        print("🖥️ Launching GUI")
        launch_gui.launch_gui()

    async def start_input_controllers(self):
        if "input_controllers" in self.running_tasks and not self.running_tasks["input_controllers"].done():
            print("🎮 Input_controllers already running")
            return

        print("🎮 Starting input_controllers module")
        controller = importlib.import_module("modules.input_controllers")
        task = asyncio.create_task(controller.run("ws://localhost:9999"))
        self.running_tasks["input_controllers"] = task

    async def stop_input_controllers(self):
        task = self.running_tasks.get("input_controllers")
        if task and not task.done():
            print("🛑 Stopping input_controllers")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("✅ Input_controllers stopped")
        else:
            print("⚠️ Input_controllers not running")

    async def start_image_processor(self):
        print("🧠 Image processor placeholder starting (not yet implemented)")
        # Placeholder for actual image processor start logic

    async def stop_image_processor(self):
        print("🛑 Stopping image processor (not yet implemented)")
        # Placeholder for actual image processor stop logic

    async def handle_commands(self):
        while True:
            cmd = await self.command_queue.get()
            if cmd == "start_gui":
                await self.start_gui()
            elif cmd == "start_input_controllers":
                await self.start_input_controllers()
            elif cmd == "stop_input_controllers":
                await self.stop_input_controllers()
            elif cmd == "start_image":
                await self.start_image_processor()
            elif cmd == "stop_image":
                await self.stop_image_processor()
            elif cmd == "quit":
                print("🛑 Quit requested from GUI")
                break

    async def run(self):
        print("🚀 ROV Topside Booting")
        self.loop = asyncio.get_running_loop()  # ✅ Now safe to assign loop

        if ENABLED_MODULES["relay"]:
            await self.start_relay()

        if ENABLED_MODULES["gui"]:
            await self.start_gui()

        if ENABLED_MODULES["input_controllers"]:
            await self.start_input_controllers()

        if ENABLED_MODULES["image_processor"]:
            await self.start_image_processor()

        module_launcher.launch_ui(self.command_queue, self.loop)
        await self.handle_commands()

if __name__ == "__main__":
    try:
        asyncio.run(TopsideController().run())
    except KeyboardInterrupt:
        print("🛑 Exiting ROV Topside")