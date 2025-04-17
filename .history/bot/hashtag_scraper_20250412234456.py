# bot/hashtag_scraper.py

def get_users_by_hashtag(cl, hashtag, num_posts=10):
    try:
        medias = cl.hashtag_medias_recent(hashtag, amount=num_posts)
        usernames = set()
        for media in medias:
            likers = cl.media_likers(media.pk)
            usernames.update(user.username for user in likers)
        print(f"Found {len(usernames)} users for hashtag #{hashtag}")
        return list(usernames)
    except Exception as e:
        print(f"Error scraping hashtag #{hashtag}: {e}")
        return []
