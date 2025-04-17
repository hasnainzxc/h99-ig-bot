# bot/login.py

from instagrapi import Client
from bot.config import username, password

def login():
    cl = Client()
    try:
        cl.login(username, password)
        print("Logged in successfully!")
        return cl
    except Exception as e:
        print(f"Login failed: {e}")
        return None
