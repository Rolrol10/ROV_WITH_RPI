# modules/network_handler.py

import asyncio
import websockets
import json

REMOTE_ROV_WS = "ws://raspberrypi.local:8765"
# REMOTE_ROV_WS = "ws://10.253.0.10:8765"
LOCAL_LISTEN_PORT = 9999

# Global pointer to the current relay instance
relay_instance = None


# ✅ Modern handler for websockets >=11.x (15.x confirmed)
async def handle_gui_or_module(websocket):
    global relay_instance
    if relay_instance:
        await relay_instance.handle_local_client(websocket)
    else:
        print("❌ Relay instance not set — can't forward client connection.")


class NetworkRelay:
    def __init__(self):
        self.local_clients = set()
        self.rov_ws = None

    async def connect_to_rov(self):
        while True:
            try:
                self.rov_ws = await websockets.connect(REMOTE_ROV_WS)
                print(f"🔌 Connected to ROV at {REMOTE_ROV_WS}")
                return
            except Exception as e:
                print(f"⚠️ ROV connection failed: {e} — retrying in 3s")
                await asyncio.sleep(3)

    async def handle_local_client(self, websocket):
        self.local_clients.add(websocket)
        print(f"🖥️ Local client connected ({len(self.local_clients)} total)")

        try:
            async for message in websocket:
                if self.rov_ws:
                    await self.rov_ws.send(message)
        except Exception as e:
            print(f"⚠️ Local client error: {e}")
        finally:
            self.local_clients.discard(websocket)
            print("🖥️ Local client disconnected")

    async def receive_from_rov(self):
        while True:
            try:
                async for message in self.rov_ws:
                    for client in self.local_clients.copy():
                        try:
                            await client.send(message)
                        except Exception as e:
                            print(f"⚠️ Failed to send to client: {e}")
                            self.local_clients.discard(client)
            except websockets.ConnectionClosed:
                print("🔌 ROV disconnected. Reconnecting...")
                await self.connect_to_rov()
            except Exception as e:
                print(f"❌ Unexpected ROV error: {e}")
                await asyncio.sleep(3)

    async def run(self):
        global relay_instance
        relay_instance = self  # expose this instance to the global handler

        await self.connect_to_rov()
        asyncio.create_task(self.receive_from_rov())

        print(f"🧩 Relay listening on ws://localhost:{LOCAL_LISTEN_PORT}")
        # server = await websockets.serve(handle_gui_or_module, "localhost", LOCAL_LISTEN_PORT)
        server = await websockets.serve(
            handle_gui_or_module,
            "localhost",
            LOCAL_LISTEN_PORT,
            ping_interval=30,   # ⏱️ Send ping every 30s
            ping_timeout=20     # ⏳ Wait 20s for pong
        )
        await server.wait_closed()
