# bot/hashtag_scraper.py

from typing import List
from bot.utils import random_delay

async def get_users_by_hashtag(client, hashtag: str, max_users: int = 20) -> List[str]:
    """
    Scrapes users who posted with the specified hashtag
    
    Args:
        client: Instagram client instance
        hashtag: Hashtag to search without the # symbol
        max_users: Maximum number of users to return
    
    Returns:
        List of usernames
    """
    try:
        # Get medias by hashtag
        medias = client.hashtag_medias_recent(hashtag, max_users)
        
        # Extract unique usernames
        usernames = []
        for media in medias:
            username = media.user.username
            if username not in usernames:
                usernames.append(username)
            
            if len(usernames) >= max_users:
                break
                
            await random_delay(2, 4)  # Small delay between processing posts
            
        return usernames

    except Exception as e:
        print(f"Error scraping hashtag {hashtag}: {e}")
        return []
