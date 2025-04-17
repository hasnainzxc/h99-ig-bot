from bot.config import USERNAME, PASSWORD
from bot.login import login
from bot.hashtag_scraper import scrape_hashtags
from bot.message_sender import send_messages

def main():
    # Log in to Instagram
    session = login(USERNAME, PASSWORD)
    
    if session:
        print("Logged in successfully!")
        
        # Example usage of hashtag scraping
        hashtags = ['examplehashtag1', 'examplehashtag2']
        posts = scrape_hashtags(session, hashtags)
        
        # Example usage of sending messages
        for post in posts:
            user_id = post['user_id']
            message = "Hello from the Instagram bot!"
            send_messages(session, user_id, message)
    else:
        print("Login failed. Please check your credentials.")

if __name__ == "__main__":
    main()