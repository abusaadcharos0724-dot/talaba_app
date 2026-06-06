import logging
logger = logging.getLogger(__name__)

from aiogram import Bot

async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        logger.info(f"Sub check for {user_id} in {channel_id}: {member.status}")
        return member.status in ["member", "administrator", "creator", "restricted"]
    except Exception as e:
        error_msg = str(e).lower()
        if "member list is inaccessible" in error_msg:
            logger.error(f"FATAL: Bot is not an admin in {channel_id}! Cannot check subscription.")
            raise PermissionError("Bot is not an admin in the channel")
        
        logger.error(f"Sub check error for {user_id} in {channel_id}: {e}")
        return False
