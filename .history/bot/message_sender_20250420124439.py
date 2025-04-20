
import random
import logging
from datetime import datetime
import time
from bot.utils import random_delay

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, client):
        self.client = client
        self.processed_messages = set()
        self.retry_count = 3
        self.base_delay = 10  # Increased base delay
        self.request_count = 0
        self.last_request_time = time.time()
        self.max_requests_per_hour = 150  # Instagram's rough limit
        self.cooldown_period = 3600  # 1 hour in seconds
        
        # Simplified message templates
        self.messages = {
            'initial': "Hey {first_name}! 👋 I noticed you're into {topic}. How's your week going?",
            'follow_up': "That's great! 😊 I've been testing this app that lets you earn ${amount} with just 10 mins/day. Want to know more?",
            'final': "Perfect! Here's the link: {link} 🔥 Start with the free trial - no card needed. Let me know if you try it!"
        }

    def _check_rate_limit(self):
        """Check if we're within rate limits and handle cooldown"""
        current_time = time.time()
        time_passed = current_time - self.last_request_time
        
        # Reset counters if an hour has passed
        if time_passed >= self.cooldown_period:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check if we're approaching the limit
        if self.request_count >= self.max_requests_per_hour:
            sleep_time = self.cooldown_period - time_passed
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, cooling down for {sleep_time/60:.1f} minutes")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()

    async def handle_api_request(self, func, *args, **kwargs):
        """Generic handler for API requests with rate limiting"""
        for attempt in range(self.retry_count):
            try:
                # Check rate limits before making request
                self._check_rate_limit()
                
                # Add progressive delay between retries
                delay = self.base_delay * (2 ** attempt)
                await random_delay(delay, delay * 1.5)
                
                result = func(*args, **kwargs)
                self.request_count += 1
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle different types of errors
                if "500" in error_msg:
                    logger.warning("Instagram server error, retrying after longer delay...")
                    await random_delay(delay * 2, delay * 3)
                elif "429" in error_msg or "too many requests" in error_msg:
                    logger.warning("Rate limit hit, cooling down...")
                    await random_delay(300, 600)  # 5-10 minute cooldown
                    self.request_count = self.max_requests_per_hour  # Force cooldown
                elif "jsondecodeerror" in error_msg:
                    logger.warning("JSON decode error, retrying with exponential backoff...")
                    await random_delay(delay * 1.5, delay * 2)
                else:
                    logger.error(f"Unexpected error: {e}")
                    if attempt == self.retry_count - 1:
                        raise
                    
                if attempt < self.retry_count - 1:
                    continue
                    
                logger.error(f"All attempts failed for API request after {self.retry_count} retries")
                return None
                
        return None

    async def send_message(self, user_id, text):
        try:
            # Validate inputs
            if not user_id or not text:
                logger.error("Invalid user_id or text for message")
                return None
                
            result = await self.handle_api_request(
                lambda: self.client.direct_send(text=text, user_ids=[user_id])
            )
            
            if result:
                logger.info(f"Message sent successfully: '{text[:30]}...'")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    async def get_messages(self, thread_id):
        try:
            # Validate thread_id
            if not thread_id:
                logger.error("Invalid thread_id")
                return None
                
            return await self.handle_api_request(
                lambda: self.client.direct_messages(thread_id)
            )
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return None

    async def get_user_info(self, username):
        try:
            return self.client.user_info_by_username(username)
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def wait_for_reply(self, thread_id, timeout_minutes=30):
        logger.info(f"Waiting for reply (timeout: {timeout_minutes} minutes)")
        start_time = datetime.now()
        check_interval = 30  # Start with 30 seconds
        max_interval = 300   # Max 5 minutes between checks
        
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            try:
                messages = await self.get_messages(thread_id)
                
                if messages:
                    for message in messages:
                        if (message.user_id != self.client.user_id and 
                            message.id not in self.processed_messages):
                            self.processed_messages.add(message.id)
                            logger.info(f"Got reply: '{message.text[:30]}...'")
                            return True
                
                # Implement progressive backoff for checking messages
                await random_delay(check_interval, check_interval * 1.5)
                check_interval = min(check_interval * 1.5, max_interval)
                
            except Exception as e:
                logger.warning(f"Error checking replies: {e}")
                check_interval = min(check_interval * 2, max_interval)
                await random_delay(check_interval, check_interval * 1.5)
        
        logger.info("No reply received within timeout")
        return False

    async def handle_conversation(self, username: str, topic: str):
        try:
            # Get user info without await
            user_info = self.client.user_info_by_username(username)
            if not user_info:
                logger.error(f"Could not get user info for {username}")
                return False
                
            first_name = user_info.full_name.split()[0] if user_info.full_name else username
            
            # Send initial message
            initial_msg = self.messages['initial'].format(first_name=first_name, topic=topic)
            thread = await self.send_message(user_info.pk, initial_msg)
            if not thread:
                return False
            
            # Wait for reply with increased timeout
            if await self.wait_for_reply(thread.id, timeout_minutes=45):
                amount = random.randint(50, 150)
                follow_up = self.messages['follow_up'].format(amount=amount)
                await self.send_message(user_info.pk, follow_up)
                
                if await self.wait_for_reply(thread.id, timeout_minutes=45):
                    final = self.messages['final'].format(link="https://your-app-link.com")
                    await self.send_message(user_info.pk, final)
                    return True
            
            return False

        except Exception as e:
            logger.error(f"Error in conversation with {username}: {e}")
            return False
