import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import time
import json
import os

logger = logging.getLogger(__name__)

class SeleniumHandler:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.cookies_file = 'instagram_cookies.json'

    def _init_driver(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = uc.Chrome(options=options)
        
    def _save_cookies(self):
        if self.driver:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)

    def _load_cookies(self):
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
        return False

    async def login(self):
        try:
            if not self.driver:
                self._init_driver()
            
            self.driver.get('https://www.instagram.com/accounts/login/')
            
            if not self._load_cookies():
                # Wait for login form
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_input = self.driver.find_element(By.NAME, "password")
                
                username_input.send_keys(self.username)
                password_input.send_keys(self.password)
                password_input.submit()
                
                # Wait for login to complete
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
                )
                
                self._save_cookies()
            
            return True
            
        except Exception as e:
            logger.error(f"Selenium login failed: {e}")
            return False

    async def send_dm(self, username, message):
        try:
            # Navigate to DM page
            self.driver.get(f'https://www.instagram.com/direct/new/')
            
            # Wait for and click recipient input
            recipient_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='queryBox']"))
            )
            recipient_input.send_keys(username)
            
            # Wait for and click recipient suggestion
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='option']"))
            ).click()
            
            # Click Next
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            next_button.click()
            
            # Wait for message input and send message
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Message...']"))
            )
            message_input.send_keys(message)
            message_input.submit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DM via Selenium: {e}")
            return False

    async def check_for_replies(self, username):
        try:
            self.driver.get(f'https://www.instagram.com/direct/inbox/')
            
            # Wait for messages to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='list']"))
            )
            
            # Find the chat with the user
            chats = self.driver.find_elements(By.CSS_SELECTOR, "div[role='list'] > div")
            
            for chat in chats:
                if username in chat.text:
                    # Check if there's an unread message indicator
                    unread = chat.find_elements(By.CSS_SELECTOR, "div[class*='unread']")
                    if unread:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check replies via Selenium: {e}")
            return False

    async def check_user_exists(self, username):
        """Check if an Instagram user exists"""
        try:
            if not self.driver:
                await self.login()
            
            self.driver.get(f'https://www.instagram.com/{username}/')
            
            try:
                # Wait for either the profile page to load or the "User not found" error
                WebDriverWait(self.driver, 10).until(
                    lambda driver: any([
                        driver.find_elements(By.CSS_SELECTOR, "article[role='presentation']"),  # Profile exists
                        driver.find_elements(By.CSS_SELECTOR, "h2:contains('Sorry, this page isn't available.')")  # User not found
                    ])
                )
                
                # Check if profile exists
                return bool(self.driver.find_elements(By.CSS_SELECTOR, "article[role='presentation']"))
                
            except TimeoutException:
                logger.warning(f"Timeout while checking user {username}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None