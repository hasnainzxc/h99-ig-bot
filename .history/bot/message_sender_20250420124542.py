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
        self.retry_count = 5  # Increased retries
        self.base_delay = 15  # Increased base delay
        self.request_count = 0
        self.last_request_time = time.time()
        self.max_requests_per_hour = 50  # Reduced to be more conservative
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

    async def send_message(self, user_id, text):
        try:
            # Validate inputs
            if not user_id or not text:
                logger.error("Invalid user_id or text for message")
                return None
                
            result = await self.handle_api_request(
                lambda: self.client.direct_send(text=text, user_ids=[user_id]),
                'direct_send'
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
                lambda: self.client.direct_messages(thread_id),
                'direct_messages'
            )
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return None

    async def get_user_info(self, username):
        try:
            # Try different methods to get user info
            methods = [
                lambda: self.client.user_info_v1(username),
                lambda: self.client.user_info_by_username_v1(username),
                lambda: self.client.user_info_by_username(username)
            ]
            
            for method in methods:
                try:
                    result = await self.handle_api_request(method, 'user_info')
                    if result:
                        return result
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"All methods failed to get user info: {e}")
            return None

    async def wait_for_reply(self, thread_id, timeout_minutes=30):
        logger.info(f"Waiting for reply (timeout: {timeout_minutes} minutes)")
        start_time = datetime.now()
        check_interval = 45  # Start with 45 seconds
        max_interval = 600   # Max 10 minutes between checks
        
        message_cache = {}  # Cache to store last seen messages
        
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            try:
                messages = await self.handle_api_request(
                    lambda: self.client.direct_messages(thread_id),
                    'direct_messages'
                )
                
                if messages:
                    # Compare with cached messages to detect new ones
                    for message in messages:
                        if (message.user_id != self.client.user_id and 
                            message.id not in self.processed_messages and
                            message.id not in message_cache):
                            
                            self.processed_messages.add(message.id)
                            message_cache[message.id] = message
                            logger.info(f"Got reply: '{message.text[:30]}...'")
                            return True
                
                await random_delay(check_interval, check_interval * 1.2)
                check_interval = min(check_interval * 1.2, max_interval)
                
            except Exception as e:
                logger.warning(f"Error checking replies: {e}")
                check_interval = min(check_interval * 1.5, max_interval)
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
