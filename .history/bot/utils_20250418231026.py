# bot/utils.py

import random
import asyncio
import logging

logger = logging.getLogger(__name__)

async def random_delay(min_seconds: int, max_seconds: int):
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting for {delay:.2f} seconds")
    await asyncio.sleep(delay)
