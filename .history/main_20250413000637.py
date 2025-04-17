# main.py

from bot.login import login
from bot.message_sender import MessageHandler
from bot.hashtag_scraper import get_users_from_hashtag

async def main():
    client = login()
    if not client:
        return

    message_handler = MessageHandler(client)
    
    # Option 1: Target specific usernames
    target_users = ["user1", "user2", "user3"]
  
    # Target users from hashtags
    target_hashtags = ["sidehustle", "makemoney", "entrepreneurship"]
    for hashtag in target_hashtags:
        users = await get_users_by_hashtag(client, hashtag)  # Updated function call
        for username in users[:5]:  # Limit to 5 users per hashtag
            await message_handler.handle_conversation(username, hashtag)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())