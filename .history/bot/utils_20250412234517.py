# bot/utils.py

import time

def random_delay(min_time=5, max_time=15):
    import random
    delay = random.randint(min_time, max_time)
    time.sleep(delay)
