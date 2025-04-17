# main.py

from bot.login import login
from bot.hashtag_scraper import get_users_by_hashtag
from bot.message_sender import send_message

HASHTAG = "investing"
NUM_POSTS = 10
MESSAGE_TEMPLATE = "Hey {name}! 👋 Saw your interest in investing. How’s your week going?"

def main():
    cl = login()
    if not cl:
        print("Bot failed to log in.")
        return
    
    usernames = get_users_by_hashtag(cl, HASHTAG, NUM_POSTS)
    
    if usernames:
        send_message(cl, usernames, MESSAGE_TEMPLATE)
    else:
        print("No users found.")

if __name__ == "__main__":
    main()
