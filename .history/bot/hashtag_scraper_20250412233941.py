import requests
from bs4 import BeautifulSoup

class HashtagScraper:
    def __init__(self, session):
        self.session = session

    def scrape_hashtag(self, hashtag, max_posts=10):
        url = f'https://www.instagram.com/explore/tags/{hashtag}/'
        response = self.session.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve posts for hashtag: {hashtag}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        posts = []

        # Find all post links in the page
        for link in soup.find_all('a'):
            if '/p/' in link.get('href'):
                posts.append(link.get('href'))

            if len(posts) >= max_posts:
                break

        return posts

    def fetch_post_data(self, post_url):
        response = self.session.get(f'https://www.instagram.com{post_url}')
        
        if response.status_code != 200:
            print(f"Failed to retrieve post data for URL: {post_url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract relevant data from the post (e.g., image URL, caption)
        # This part can be customized based on the required data
        post_data = {
            'url': post_url,
            'image_url': soup.find('meta', property='og:image')['content'],
            'caption': soup.find('meta', property='og:description')['content']
        }

        return post_data