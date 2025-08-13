# modules/network_handler.py
import asyncio
import websockets
import json

REMOTE_ROV_WS = "ws://raspberrypi.local:8765"
# REMOTE_ROV_WS = "ws://10.253.0.10:8765"
LOCAL_LISTEN_PORT = 9999

# Global pointer to the current relay instance
relay_instance = None


# ✅ Modern handler for websockets >=11.x
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
                # Keep pings on the REMOTE link (not on localhost).
                self.rov_ws = await websockets.connect(
                    REMOTE_ROV_WS,
                    ping_interval=20,   # send ping every 20s
                    ping_timeout=60,    # allow 60s for pong
                    open_timeout=10,
                    close_timeout=5,
                    max_queue=None,
                )
                print(f"🔌 Connected to ROV at {REMOTE_ROV_WS}")
                return
            except Exception as e:
                print(f"⚠️ ROV connection failed: {e} — retrying in 3s")
                await asyncio.sleep(3)

    async def handle_local_client(self, websocket):
        self.local_clients.add(websocket)
        print(f"🖥️ Local client connected ({len(self.local_clients)} total)")
        try:
            # Drain messages from the local client and forward to the ROV
            async for message in websocket:
                if self.rov_ws:
                    try:
                        await self.rov_ws.send(message)
                    except Exception as e:
                        print(f"⚠️ Failed to send to ROV: {e}")
        except Exception as e:
            print(f"⚠️ Local client error: {e}")
        finally:
            self.local_clients.discard(websocket)
            print("🖥️ Local client disconnected")

    async def receive_from_rov(self):
        while True:
            try:
                async for message in self.rov_ws:
                    # Fan-out to all currently connected local clients
                    for client in list(self.local_clients):
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
        relay_instance = self

        await self.connect_to_rov()
        asyncio.create_task(self.receive_from_rov())

        print(f"🧩 Relay listening on ws://localhost:{LOCAL_LISTEN_PORT}")
        # 🔕 Disable pings on the LOCAL hop (controller is send-only and doesn’t recv pings).
        server = await websockets.serve(
            handle_gui_or_module,
            "localhost",
            LOCAL_LISTEN_PORT,
            ping_interval=None,   # <— no server-driven pings on localhost
            ping_timeout=None,
            max_queue=None,
            close_timeout=5,
        )
        await server.wait_closed()
