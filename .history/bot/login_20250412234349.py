# bot/login.py

from instagrapi import Client
from bot.config import USERNAME, PASSWORD

def login():
    cl = Client()
    try:
        cl.login(USERNAME, PASSWORD)
        print("Logged in successfully!")
        return cl
    except Exception as e:
        print(f"Login failed: {e}")
        return None
