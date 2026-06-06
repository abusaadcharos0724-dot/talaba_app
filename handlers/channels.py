from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_all_channels

router = Router()

@router.message(F.text == "📢 Foydali kanallar")
async def show_channels(message: types.Message):
    channels = get_all_channels()
    
    if not channels:
        return await message.answer("📢 **Talabalar uchun foydali kanallar:**\n\nHozircha kanallar qo'shilmagan.")

    builder = InlineKeyboardBuilder()
    
    for _, title, link in channels:
        builder.row(types.InlineKeyboardButton(text=title, url=link))
    
    await message.answer(
        "📢 **Talabalar uchun foydali kanallar:**\n\n"
        "Kerakli kanalni tanlang va obuna bo'ling:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
