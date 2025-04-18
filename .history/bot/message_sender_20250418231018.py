# bot/message_sender.py

import random
from datetime import datetime
import time
import logging
from bot.utils import random_delay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, client):
        self.client = client
        # self.initial_messages = [
        #     "Hey {first_name}! 👋 Notice you're into {topic}. How's your week shaping up?",
        #     "Hi {first_name}! 👋 Saw your {topic} posts - pretty interesting stuff! How's everything going?",
        #     "Hey there {first_name}! 👋 Love your content about {topic}. How's your day been?"
        # ]
        
        self.follow_up_messages = [
            "That's great to hear! 😊 BTW, I recently found this really cool side-hustle app. Been using it for just 10-15 mins daily and made ${amount} last week. Would you like to know more?",
            "Awesome! 🙌 Hey, random question - I've been testing this new earning app lately. Made ${amount} just last week (10 mins/day). Want me to share more details?",
        ]
        
        self.final_messages = [
            "Cool! Here's the link: {link} 🔥 You can start with the free trial, no card needed. I'd love to share some tips once you try it! Keep me posted? 😊",
            "Perfect! Check it out here: {link} ✨ Start with the free version first. I've got some good strategies to share if you like it. Let me know what you think!"
        ]

    async def get_user_info_with_retry(self, username: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                await random_delay(5 * (attempt + 1), 10 * (attempt + 1))
                user_info = self.client.user_info_by_username(username)
                return user_info
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                continue
        return None

    async def send_direct_message_with_retry(self, user_ids, text, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                await random_delay(5 * (attempt + 1), 10 * (attempt + 1))
                return self.client.direct_send(text=text, user_ids=user_ids)
            except Exception as e:
                logger.warning(f"Message send attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                continue
        return None

    async def send_initial_message(self, username: str, topic: str) -> bool:
        try:
            # Get user info with retries
            user_info = await self.get_user_info_with_retry(username)
            if not user_info:
                logger.error(f"Could not fetch user info for {username}")
                return None

            first_name = user_info.full_name.split()[0] if user_info.full_name else username
            
            # Format message
            message = random.choice(self.initial_messages)
            message = message.format(first_name=first_name, topic=topic)
            
            # Send message with retries
            thread = await self.send_direct_message_with_retry(
                user_ids=[user_info.pk],
                text=message
            )
            
            if thread:
                logger.info(f"Successfully sent initial message to {username}")
                await random_delay(20, 40)
                return thread
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending initial message to {username}: {e}")
            return None

    async def handle_conversation(self, username: str, topic: str):
        try:
            thread = await self.send_initial_message(username, topic)
            if not thread:
                logger.error(f"Failed to start conversation with {username}")
                return False

            # Wait for response
            response = await self.wait_for_response(thread)
            if response:
                # Send follow-up with retries
                amount = random.randint(50, 150)
                follow_up = random.choice(self.follow_up_messages)
                await self.send_direct_message_with_retry(
                    user_ids=[thread.user_id],
                    text=follow_up.format(amount=amount)
                )
                
                response = await self.wait_for_response(thread)
                if response:
                    # Send final message with retries
                    final = random.choice(self.final_messages)
                    await self.send_direct_message_with_retry(
                        user_ids=[thread.user_id],
                        text=final.format(link="https://your-app-link.com")
                    )
                    return True
            
            return False

        except Exception as e:
            logger.error(f"Error in conversation with {username}: {e}")
            return False

    async def wait_for_response(self, thread, timeout_minutes=30):
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            messages = self.client.direct_messages(thread.id)
            if messages and messages[0].user_id != self.client.user_id:
                return True
            await random_delay(30, 60)
        return False
