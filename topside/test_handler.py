# test_relay_only.py

import asyncio
from modules.network_handler import NetworkRelay

async def main():
    relay = NetworkRelay()
    await relay.run()

asyncio.run(main())
