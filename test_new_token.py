import asyncio
from aiogram import Bot

async def test():
    token = "8978394694:AAHQa3izpeyEgPemmdS6wevQQ4NUwYdZwwg"
    print(f"Testing token: {token}")
    print(f"Token length: {len(token)}")
    
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"✓ Success: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
    finally:
        await bot.session.close()

asyncio.run(test())
