# main.py

from bot.login import login
from bot.message_sender import MessageHandler

async def main():
    client = login()
    if not client:
        return

    message_handler = MessageHandler(client)
    
    # Test with specific username
    username = "hasnainzxc"
    topic = "entrepreneurship"
    await message_handler.handle_conversation(username, topic)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())