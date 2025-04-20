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
        self.initial_messages = [
            "Hey {first_name}! 👋 Notice you're into {topic}. How's your week shaping up?",
            "Hi {first_name}! 👋 Saw your {topic} posts - pretty interesting stuff! How's everything going?",
            "Hey there {first_name}! 👋 Love your content about {topic}. How's your day been?"
        ]
        
        self.follow_up_messages = [
            "That's great to hear! 😊 BTW, I recently found this really cool side-hustle app. Been using it for just 10-15 mins daily and made ${amount} last week. Would you like to know more?",
            "Awesome! 🙌 Hey, random question - I've been testing this new earning app lately. Made ${amount} just last week (10 mins/day). Want me to share more details?",
        ]
        
        self.final_messages = [
            "Cool! Here's the link: {link} 🔥 You can start with the free trial, no card needed. I'd love to share some tips once you try it! Keep me posted? 😊",
            "Perfect! Check it out here: {link} ✨ Start with the free version first. I've got some good strategies to share if you like it. Let me know what you think!"
        ]
        
        # Track processed messages to avoid duplicate responses
        self.processed_message_ids = {}

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
                response = self.client.direct_send(text=text, user_ids=user_ids)
                logger.info(f"Message sent: '{text[:30]}...' to {user_ids}")
                return response
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
                # Initialize message tracking for this thread
                self.processed_message_ids[thread.id] = set()
                await random_delay(20, 40)
                return thread
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending initial message to {username}: {e}")
            return None

    async def handle_conversation(self, username: str, topic: str):
        try:
            logger.info(f"Starting conversation with {username} about {topic}")
            
            thread = await self.send_initial_message(username, topic)
            if not thread:
                logger.error(f"Failed to start conversation with {username}")
                return False

            logger.info(f"Waiting for initial response from {username}")
            
            # Wait for response to initial message
            response = await self.wait_for_response(thread)
            if response:
                logger.info(f"Received response from {username}, sending follow-up")
                
                # Send follow-up with retries
                amount = random.randint(50, 150)
                follow_up = random.choice(self.follow_up_messages)
                follow_up_formatted = follow_up.format(amount=amount)
                
                await self.send_direct_message_with_retry(
                    user_ids=[thread.user_id],
                    text=follow_up_formatted
                )
                
                logger.info(f"Waiting for response to follow-up from {username}")
                response = await self.wait_for_response(thread)
                if response:
                    logger.info(f"Received second response from {username}, sending final message")
                    
                    # Send final message with retries
                    final = random.choice(self.final_messages)
                    final_formatted = final.format(link="https://your-app-link.com")
                    
                    await self.send_direct_message_with_retry(
                        user_ids=[thread.user_id],
                        text=final_formatted
                    )
                    logger.info(f"Completed full conversation flow with {username}")
                    return True
                else:
                    logger.info(f"No response to follow-up from {username} within timeout")
            else:
                logger.info(f"No initial response from {username} within timeout")
            
            return False

        except Exception as e:
            logger.error(f"Error in conversation with {username}: {e}")
            return False

    async def wait_for_response(self, thread, timeout_minutes=30):
        start_time = datetime.now()
        thread_id = thread.id
        
        # Initialize message tracking if not already done
        if thread_id not in self.processed_message_ids:
            self.processed_message_ids[thread_id] = set()
        
        logger.info(f"Waiting for response in thread {thread_id} for up to {timeout_minutes} minutes")
        
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            try:
                messages = self.client.direct_messages(thread_id)
                
                # Check if we have new messages from the other user
                if messages:
                    for message in messages:
                        # Only process messages from the other user and not previously processed
                        if (message.user_id != self.client.user_id and 
                            message.id not in self.processed_message_ids[thread_id]):
                            
                            logger.info(f"New response detected: '{message.text[:30]}...'")
                            # Mark message as processed
                            self.processed_message_ids[thread_id].add(message.id)
                            return True
                
                # No new messages, wait before checking again
                logger.debug(f"No new messages yet, waiting before checking again")
                await random_delay(30, 60)
                
            except Exception as e:
                logger.warning(f"Error checking for messages: {e}")
                await random_delay(60, 120)  # Longer delay on error
                
        logger.info(f"Timeout reached waiting for response in thread {thread_id}")
        return False
