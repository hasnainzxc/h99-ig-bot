import random
import logging
from datetime import datetime
import time
from bot.utils import random_delay
from bot.selenium_handler import SeleniumHandler
from bot.config import username, password  # Changed to lowercase

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, client):
        self.client = client
        self.selenium_handler = None  # Lazy init
        self.processed_messages = set()
        self.retry_count = 3  # Reduced retries before fallback
        self.base_delay = 15
        self.request_count = 0
        self.last_request_time = time.time()
        self.max_requests_per_hour = 50
        self.cooldown_period = 3600
        
        # Add request tracking per endpoint
        self.endpoint_counters = {
            'user_info': {'count': 0, 'last_time': time.time()},
            'direct_send': {'count': 0, 'last_time': time.time()},
            'direct_messages': {'count': 0, 'last_time': time.time()}
        }
        
        # Simplified message templates
        self.messages = {
            'initial': "Hey {first_name}! 👋 I noticed you're into {topic}. How's your week going?",
            'follow_up': "That's great! 😊 I've been testing this app that lets you earn ${amount} with just 10 mins/day. Want to know more?",
            'final': "Perfect! Here's the link: {link} 🔥 Start with the free trial - no card needed. Let me know if you try it!"
        }

    async def _init_selenium_if_needed(self):
        if not self.selenium_handler:
            self.selenium_handler = SeleniumHandler(username, password)  # Changed to lowercase
            await self.selenium_handler.login()

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

    def _check_endpoint_limit(self, endpoint, max_requests=20):
        """Check rate limits per endpoint"""
        current_time = time.time()
        counter = self.endpoint_counters[endpoint]
        time_passed = current_time - counter['last_time']
        
        if time_passed >= self.cooldown_period:
            counter['count'] = 0
            counter['last_time'] = current_time
            return True
            
        if counter['count'] >= max_requests:
            sleep_time = self.cooldown_period - time_passed
            if sleep_time > 0:
                logger.warning(f"{endpoint} limit reached, cooling down for {sleep_time/60:.1f} minutes")
                time.sleep(sleep_time)
                counter['count'] = 0
                counter['last_time'] = time.time()
        
        counter['count'] += 1
        return True

    async def handle_api_request(self, func, endpoint, *args, **kwargs):
        """Improved API request handler with endpoint-specific limits"""
        for attempt in range(self.retry_count):
            try:
                # Check both global and endpoint-specific rate limits
                self._check_rate_limit()
                self._check_endpoint_limit(endpoint)
                
                delay = self.base_delay * (1.5 ** attempt)  # Less aggressive backoff
                await random_delay(delay, delay * 1.2)
                
                # Try v1 API first for certain endpoints
                if endpoint == 'user_info':
                    try:
                        result = self.client.user_info_v1(args[0])
                    except:
                        result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                self.request_count += 1
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if any(err in error_msg for err in ['500', 'jsondecodeerror']):
                    logger.warning(f"API error ({endpoint}), attempt {attempt + 1}/{self.retry_count}")
                    await random_delay(delay * 2, delay * 2.5)
                elif '429' in error_msg or 'too many requests' in error_msg:
                    logger.warning(f"Rate limit hit for {endpoint}, cooling down...")
                    await random_delay(600, 900)  # 10-15 minute cooldown
                    self._reset_limits(endpoint)
                else:
                    if attempt == self.retry_count - 1:
                        logger.error(f"Final attempt failed for {endpoint}: {e}")
                        raise
                    
                await random_delay(delay, delay * 1.5)
                continue
                
        return None

    def _reset_limits(self, endpoint=None):
        """Reset rate limits for specific or all endpoints"""
        current_time = time.time()
        if endpoint:
            self.endpoint_counters[endpoint] = {'count': 0, 'last_time': current_time}
        else:
            for ep in self.endpoint_counters:
                self.endpoint_counters[ep] = {'count': 0, 'last_time': current_time}
        self.request_count = 0
        self.last_request_time = current_time

    async def send_message(self, user_id, text, username):
        # Try API first
        try:
            result = await self.handle_api_request(
                lambda: self.client.direct_send(text=text, user_ids=[user_id]),
                'direct_send'
            )
            
            if result:
                logger.info(f"Message sent successfully via API: '{text[:30]}...'")
                return result
                
        except Exception as e:
            logger.warning(f"API message send failed: {e}")

        # Fallback to Selenium
        logger.info("Falling back to Selenium for message sending")
        try:
            await self._init_selenium_if_needed()
            if await self.selenium_handler.send_dm(username, text):
                logger.info(f"Message sent successfully via Selenium: '{text[:30]}...'")
                return True
        except Exception as e:
            logger.error(f"Selenium fallback failed: {e}")
            
        return None

    async def get_messages(self, thread_id):
        try:
            # Validate thread_id
            if not thread_id:
                logger.error("Invalid thread_id")
                return None
                
            return await self.handle_api_request(
                lambda: self.client.direct_messages(thread_id),
                'direct_messages'
            )
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return None

    async def get_user_info(self, username):
        try:
            # Try public API first
            try:
                result = await self.handle_api_request(
                    lambda: self.client.user_info_by_username(username),
                    'user_info'
                )
                if result:
                    return result
            except Exception as e:
                error_msg = str(e).lower()
                if '404' in error_msg or 'not exist' in error_msg:
                    logger.info(f"User {username} does not exist")
                    return None
                logger.warning(f"Public API failed: {e}")

            # Try user ID lookup only if it wasn't a 404
            try:
                user_id = await self.handle_api_request(
                    lambda: self.client.user_id_from_username(username),
                    'user_info'
                )
                if user_id:
                    result = await self.handle_api_request(
                        lambda: self.client.user_info(user_id),
                        'user_info'
                    )
                    if result:
                        return result
            except Exception as e:
                error_msg = str(e).lower()
                if '404' in error_msg or 'not exist' in error_msg:
                    logger.info(f"User {username} does not exist")
                    return None
                logger.warning(f"User ID lookup failed: {e}")

            # Fall back to Selenium for user info only if previous errors weren't 404s
            logger.info("Falling back to Selenium for user info")
            await self._init_selenium_if_needed()
            if await self.selenium_handler.check_user_exists(username):
                return type('User', (), {
                    'pk': 0,  # Placeholder ID
                    'username': username,
                    'full_name': username,
                })
            
            return None
            
        except Exception as e:
            logger.error(f"All methods failed to get user info: {e}")
            return None

    async def wait_for_reply(self, thread_id, username, timeout_minutes=30):
        logger.info(f"Waiting for reply from {username} (timeout: {timeout_minutes} minutes)")
        start_time = datetime.now()
        check_interval = 45
        max_interval = 600
        max_retries = 3
        
        message_cache = set()  # Changed to set for simpler duplicate checking
        using_selenium = False
        
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            try:
                if not using_selenium:
                    # Try API with retries
                    for attempt in range(max_retries):
                        try:
                            messages = await self.handle_api_request(
                                lambda: self.client.direct_messages(thread_id),
                                'direct_messages'
                            )
                            
                            if messages:
                                # Process messages newest to oldest
                                for message in reversed(messages):
                                    message_id = str(message.id)  # Convert to string for consistency
                                    if (message.user_id != self.client.user_id and 
                                        message_id not in message_cache and
                                        message_id not in self.processed_messages):
                                        
                                        logger.info(f"Got reply via API from {username}: '{message.text[:30]}...'")
                                        message_cache.add(message_id)
                                        self.processed_messages.add(message_id)
                                        return True
                            break  # Success, exit retry loop
                            
                        except Exception as e:
                            if attempt == max_retries - 1:
                                logger.warning(f"API check failed after {max_retries} attempts, switching to Selenium")
                                using_selenium = True
                            else:
                                await random_delay(check_interval * (attempt + 1), check_interval * (attempt + 1.5))
                                continue
                
                if using_selenium:
                    # Selenium fallback
                    await self._init_selenium_if_needed()
                    if await self.selenium_handler.check_for_replies(username):
                        logger.info(f"Got reply from {username} via Selenium")
                        return True
                
                # Adaptive delay between checks
                await random_delay(check_interval, check_interval * 1.2)
                check_interval = min(check_interval * 1.2, max_interval)
                
            except Exception as e:
                logger.warning(f"Error checking replies: {e}")
                if not using_selenium:
                    logger.info("Error with API, switching to Selenium for reply checking")
                    using_selenium = True
                check_interval = min(check_interval * 1.5, max_interval)
                await random_delay(check_interval, check_interval * 1.5)
        
        logger.info(f"No reply received from {username} within {timeout_minutes} minutes timeout")
        return False

    async def handle_conversation(self, username: str, topic: str):
        try:
            # Get user info
            user_info = await self.get_user_info(username)
            if not user_info:
                logger.error(f"Could not get user info for {username}")
                return False
                
            first_name = user_info.full_name.split()[0] if user_info.full_name else username
            
            # Send initial message
            initial_msg = self.messages['initial'].format(first_name=first_name, topic=topic)
            thread = await self.send_message(user_info.pk, initial_msg, username)
            if not thread:
                return False

            # Extract thread ID properly, handling different response structures
            thread_id = None
            if hasattr(thread, 'thread_id'):
                thread_id = thread.thread_id
            elif hasattr(thread, 'id'):
                thread_id = thread.id
            else:
                # If thread is a dict or has different structure
                thread_id = str(thread).split('/')[-1] if str(thread).find('/') != -1 else str(thread)
            
            logger.info(f"Created thread {thread_id} with {username}")
            
            # Wait for reply with increased timeout
            if await self.wait_for_reply(thread_id, username, timeout_minutes=45):
                # Add delay before follow-up to appear more natural
                await random_delay(10, 20)
                amount = random.randint(50, 150)
                follow_up = self.messages['follow_up'].format(amount=amount)
                await self.send_message(user_info.pk, follow_up, username)
                
                if await self.wait_for_reply(thread_id, username, timeout_minutes=45):
                    await random_delay(10, 20)
                    final = self.messages['final'].format(link="https://your-app-link.com")
                    await self.send_message(user_info.pk, final, username)
                    return True
            
            return False

        except Exception as e:
            logger.error(f"Error in conversation with {username}: {e}")
            return False

    def __del__(self):
        if self.selenium_handler:
            self.selenium_handler.close()
