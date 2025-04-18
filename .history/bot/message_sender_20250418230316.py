# bot/message_sender.py

import random
from datetime import datetime
from bot.utils import random_delay

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

    async def send_initial_message(self, username: str, topic: str) -> bool:
        try:
            # Get user info
            user_info = self.client.user_info_by_username(username)
            first_name = user_info.full_name.split()[0] if user_info.full_name else username
            
            # Format message
            message = random.choice(self.initial_messages)
            message = message.format(first_name=first_name, topic=topic)
            
            # Send message using correct method
            thread = self.client.direct_send(
                text=message,
                user_ids=[user_info.pk]
            )
            
            await random_delay(20, 40)  # Wait for natural response time
            return thread
            
        except Exception as e:
            print(f"Error sending initial message to {username}: {e}")
            return None

    async def handle_conversation(self, username: str, topic: str):
        thread = await self.send_initial_message(username, topic)
        if not thread:
            return False

        # Wait for response
        response = await self.wait_for_response(thread)
        if response:
            # Send follow-up message
            amount = random.randint(50, 150)
            follow_up = random.choice(self.follow_up_messages)
            self.client.direct_send(
                text=follow_up.format(amount=amount),
                user_ids=[thread.user_id]
            )
            
            # Wait for second response
            response = await self.wait_for_response(thread)
            if response:
                # Send final message with link
                final = random.choice(self.final_messages)
                self.client.direct_send(
                    text=final.format(link="http:localhost:34500"),
                    user_ids=[thread.user_id]
                )

    async def wait_for_response(self, thread, timeout_minutes=30):
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < (timeout_minutes * 60):
            messages = self.client.direct_messages(thread.id)
            if messages and messages[0].user_id != self.client.user_id:
                return True
            await random_delay(30, 60)
        return False
