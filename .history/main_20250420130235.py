# main.py

from bot.login import login
from bot.message_sender import MessageHandler
import asyncio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    try:
        client = login()
        if not client:
            logger.error("Login failed")
            return

        message_handler = MessageHandler(client)
        username = "hasnainzxc"  # Replace with target username
        topic = "entrepreneurship"
        
        logger.info(f"Starting conversation with {username}")
        result = await message_handler.handle_conversation(username, topic)
        
        if result:
            logger.info(f"Successfully completed conversation with {username}")
        else:
            logger.warning(f"Conversation with {username} did not complete successfully")

    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        # Ensure Selenium driver is closed
        if 'message_handler' in locals():
            message_handler.__del__()

if __name__ == "__main__":
    asyncio.run(main())