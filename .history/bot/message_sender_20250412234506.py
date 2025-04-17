# bot/message_sender.py

import random
import time

def send_message(cl, usernames, message_template):
    for username in usernames:
        try:
            user_id = cl.user_id_from_username(username)
            message = message_template.format(name=username)
            cl.direct_send(message, user_ids=[user_id])
            print(f"Message sent to {username}")
            time.sleep(random.randint(10, 30))  # Random delay to mimic human behavior
        except Exception as e:
            print(f"Failed to message {username}: {e}")
