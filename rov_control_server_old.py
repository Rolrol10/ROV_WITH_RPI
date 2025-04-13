import asyncio
import websockets
import json
import importlib
import os
import traceback

# Store loaded modules
MODULES = []

DISPATCH_TABLE = {}

# --- Load all Python modules in ./modules ---
def load_modules():
    modules_dir = "modules"
    for file in os.listdir(modules_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = file[:-3]
            try:
                module = importlib.import_module(f"modules.{module_name}")
                if hasattr(module, "TYPE") and hasattr(module, "ACTIONS"):
                    DISPATCH_TABLE[module.TYPE] = module
                    print(f"✅ Registered: {module_name} for type '{module.TYPE}'")
                else:
                    print(f"Module {module_name} loaded but has no ACTIONS dictionary")
            except Exception as e:
                print(f"❌ Failed to load module {module_name}: {e}")
                print(traceback.format_exc())

# --- WebSocket handler ---
async def handler(websocket):
    print("🟢 WebSocket client connected.")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")
                #print(f"📩 Received: {data}")

                if message_type in DISPATCH_TABLE:
                    # DISPATCH_TABLE[message_type].handle(data)
                    module = DISPATCH_TABLE[message_type]
                    action = data.get("action")
                    if hasattr(module, "ACTIONS") and action in module.ACTIONS:
                        module.ACTIONS[action](data)

                else:
                    print(f"⚠️ Unknown action '{action}' for type '{message_type}'")

                # Send to all modules with a 'handle' function
                # for mod in MODULES:
                #     if hasattr(mod, "handle"):
                #         try:
                #             mod.handle(data)
                #         except Exception as e:
                #             print(f"❌ Error in module {mod.__name__}: {e}")
                #             print(traceback.format_exc())

            except json.JSONDecodeError:
                print("⚠️ Invalid JSON received.")
            except Exception as e:
                print(f"⚠️ Error processing message: {e}")
                print(traceback.format_exc())
    except websockets.exceptions.ConnectionClosed:
        print("🔴 WebSocket client disconnected.")

# --- Main ---
async def main():
    load_modules()
    print("🚀 Starting WebSocket ROV control server on port 8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Keep running

# --- Run it ---
if __name__ == "__main__":
    asyncio.run(main())
