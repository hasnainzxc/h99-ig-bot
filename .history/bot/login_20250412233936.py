from instabot import Bot

class InstagramLogin:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.bot = Bot()

    def login(self):
        try:
            self.bot.login(username=self.username, password=self.password)
            print("Login successful!")
        except Exception as e:
            print(f"Login failed: {e}")

# Example usage:
# if __name__ == "__main__":
#     login_instance = InstagramLogin("your_username", "your_password")
#     login_instance.login()