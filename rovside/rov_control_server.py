# --- Auto-venv bootstrap: venv lives one folder up from this script ---
# --- Auto-venv bootstrap: venv lives one folder up from this script ---
import os, sys, subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
VENV = ROOT / ".venv"

def venv_python():
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

def in_venv():
    return (hasattr(sys, "real_prefix")
            or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
            or os.environ.get("VIRTUAL_ENV"))

if not in_venv():
    if not VENV.exists():
        print(f"📦 Creating virtual environment in {VENV} …")
        import venv; venv.EnvBuilder(with_pip=True).create(str(VENV))
        subprocess.check_call([str(venv_python()), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])
        # Try common requirements at project root
        reqs = next((p for p in (ROOT/"requirements.txt", ROOT/"rovside/requirements.txt") if p.exists()), None)
        if reqs:
            print(f"📦 Installing from {reqs} …")
            subprocess.check_call([str(venv_python()), "-m", "pip", "install", "-r", str(reqs)])
        else:
            print("⚠️ No requirements.txt found at the root; skipping dependency install.")
    # Ensure relative paths (like ./modules) resolve next to this file
    os.chdir(str(SCRIPT_DIR))
    print("🔁 Re-launching inside virtual environment …\n")
    py = str(venv_python())
    os.execv(py, [py] + sys.argv)

# After relaunch: make sure script folder is importable when started from parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Script starts from here

import asyncio
import websockets
import json
import importlib
import os
import traceback

# Store loaded modules and dispatchers
DISPATCH_TABLE = {}
CLIENTS = set()  # Active WebSocket clients

# --- Function to send to all connected clients ---
async def broadcast_to_clients(message):
    to_remove = []
    for client in CLIENTS:
        try:
            await client.send(message)
        except:
            to_remove.append(client)
    for client in to_remove:
        CLIENTS.discard(client)

# --- Load all Python modules in ./modules ---
def load_modules():
    modules_dir = SCRIPT_DIR / "modules"
    if not modules_dir.exists():
        print(f"❌ No 'modules' folder found at {modules_dir}")
        return

    for file in modules_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue
        module_name = file.stem
        try:
            # Load module by absolute path so it works regardless of CWD
            spec = importlib.util.spec_from_file_location(f"modules.{module_name}", str(file))
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)

            if hasattr(module, "TYPE") and hasattr(module, "ACTIONS"):
                DISPATCH_TABLE[module.TYPE] = module
                print(f"✅ Registered: {module_name} for type '{module.TYPE}'")

                # If module supports background telemetry or async updates
                if hasattr(module, "start_background_loop"):
                    asyncio.create_task(module.start_background_loop(broadcast_to_clients))
            else:
                print(f"⚠️ Module {module_name} loaded but missing TYPE or ACTIONS")
        except Exception as e:
            print(f"❌ Failed to load module {module_name}: {e}")
            print(traceback.format_exc())


# --- WebSocket handler ---
async def handler(websocket):
    print("🟢 WebSocket client connected.")
    CLIENTS.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")
                action = data.get("action")

                if message_type in DISPATCH_TABLE:
                    module = DISPATCH_TABLE[message_type]
                    if hasattr(module, "ACTIONS") and action in module.ACTIONS:
                        func = module.ACTIONS[action]
                        if asyncio.iscoroutinefunction(func):
                            await func(data, websocket)
                        else:
                            func(data)
                    else:
                        print(f"⚠️ Unknown action '{action}' for type '{message_type}'")
                else:
                    print(f"⚠️ Unknown message type: {message_type}")

            except json.JSONDecodeError:
                print("⚠️ Invalid JSON received.")
            except Exception as e:
                print(f"⚠️ Error processing message: {e}")
                print(traceback.format_exc())
    except websockets.exceptions.ConnectionClosed:
        print("🔴 WebSocket client disconnected.")
    finally:
        CLIENTS.discard(websocket)

# --- Main ---
async def main():
    load_modules()
    print("🚀 Starting WebSocket ROV control server on port 8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Keep running forever

# --- Run it ---
if __name__ == "__main__":
    asyncio.run(main())
