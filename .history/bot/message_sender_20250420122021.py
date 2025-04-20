# bot/message_sender.py

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
        self.base_delay = 5
        
        # Simplified message templates
        self.messages = {
            'initial': "Hey {first_name}! 👋 I noticed you're into {topic}. How's your week going?",
            'follow_up': "That's great! 😊 I've been testing this app that lets you earn ${amount} with just 10 mins/day. Want to know more?",
            'final': "Perfect! Here's the link: {link} 🔥 Start with the free trial - no card needed. Let me know if you try it!"
        }

    async def handle_api_request(self, func, *args, **kwargs):
        """Generic handler for API requests with exponential backoff"""
        for attempt in range(self.retry_count):
            try:
                await random_delay(self.base_delay * (2 ** attempt), 
                                 self.base_delay * (2 ** attempt) * 2)
                return await func(*args, **kwargs)
            except Exception as e:
                if "500" in str(e) or "JSONDecodeError" in str(e):
                    if attempt < self.retry_count - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                        continue
                logger.error(f"All attempts failed for {func.__name__}: {e}")
                raise
        return None

    async def send_message(self, user_id, text):
        return await self.handle_api_request(
            lambda: self.client.direct_send(text=text, user_ids=[user_id])
        )

    async def get_messages(self, thread_id):
        return await self.handle_api_request(
            lambda: self.client.direct_messages(thread_id)
        )

    async def get_user_info(self, username):
        return await self.handle_api_request(
            lambda: self.client.user_info_by_username(username)
        )

    async def wait_for_reply(self, thread_id, timeout_minutes=30):
        logger.info(f"Waiting for reply (timeout: {timeout_minutes} minutes)")
        start_time = datetime.now()
        
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
                
                await random_delay(30, 60)
                
            except Exception as e:
                logger.warning(f"Error checking replies: {e}")
                await random_delay(60, 120)
        
        return False

    async def handle_conversation(self, username: str, topic: str):
        try:
            # Get user info with retry mechanism
            user_info = await self.get_user_info(username)
            if not user_info:
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
