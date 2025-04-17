# bot/utils.py

import random
import asyncio

async def random_delay(min_seconds: int, max_seconds: int):
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)
