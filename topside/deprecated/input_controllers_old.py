# modules/input_controllers.py

import asyncio
import pygame
import importlib

# Mapping of controller names to modules
CONTROLLERS = {
    "ps4": "modules.controllers.ps4",
    "xbox": "modules.controllers.xbox",
    "wheel": "modules.controllers.wheel",
}

def detect_controller_type():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌ No joystick detected.")
        return None

    name = pygame.joystick.Joystick(0).get_name().lower()
    print(f"🎮 Detected controller name: {name}")

    if "xbox" in name:
        return "xbox"
    elif "playstation" in name or "wireless" in name or "ps4" in name:
        return "ps4"
    elif "logitech" in name or "g920" in name or "wheel" in name:
        return "wheel"
    else:
        print("⚠️ Unknown controller type, defaulting to PS4")
        return "ps4"

async def run(ws_url):
    controller_type = detect_controller_type()
    if controller_type is None:
        return

    module_path = CONTROLLERS.get(controller_type)
    if not module_path:
        print(f"❌ Unsupported controller type: {controller_type}")
        return

    try:
        controller = importlib.import_module(module_path)
        await controller.run(ws_url)
    except Exception as e:
        print(f"❌ Failed to start controller module '{module_path}': {e}")
