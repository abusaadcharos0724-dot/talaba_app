from aiogram import types, Router, F
from aiogram.filters import Command
from database import get_referral_stats

router = Router()

@router.message(F.text == "🗣 Do'stlarni taklif qilish")
@router.message(Command("referral"))
async def show_referral_info(message: types.Message):
    user_id = message.from_user.id
    # Get bot username for link
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    count = get_referral_stats(user_id)
    
    # Reward Logic: 10 referrals = 1 month
    next_reward_target = ((count // 10) + 1) * 10
    needed = next_reward_target - count
    
    msg = (
        f"📢 **Do'stlarni taklif qilish**\n\n"
        f"Do'stlaringizga ushbu havolani yuboring va **Premium** yutib oling!\n\n"
        f"🔗 **Sizning havolangiz:**\n`{referral_link}`\n\n"
        f"📊 **Statistika:**\n"
        f"👥 Taklif qilinganlar: **{count}** ta\n\n"
        f"🎁 **Mukofot:**\n"
        f"Har **10 ta** do'stingiz uchun **1 oy Premium** bepul!\n\n"
        f"🚀 Keyingi mukofotgacha: **{needed}** ta odam qoldi."
    )
    
    await message.answer(msg, parse_mode="Markdown")
