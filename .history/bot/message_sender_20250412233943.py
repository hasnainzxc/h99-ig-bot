from instabot import Bot

class MessageSender:
    def __init__(self, username, password):
        self.bot = Bot()
        self.bot.login(username=username, password=password)

    def send_message(self, user_id, message):
        try:
            self.bot.send_message(message, [user_id])
            print(f"Message sent to {user_id}: {message}")
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

    def send_bulk_messages(self, user_ids, message):
        for user_id in user_ids:
            self.send_message(user_id, message)