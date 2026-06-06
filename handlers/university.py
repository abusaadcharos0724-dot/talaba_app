from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.news_service import fetch_news, UNIVERSITY_SITES

router = Router()

@router.message(F.text == "🏢 Universitet yangiliklari")
async def show_university_selector(message: types.Message):
    builder = InlineKeyboardBuilder()
    for uni in UNIVERSITY_SITES.keys():
        builder.button(text=uni, callback_data=f"uni_news_{uni}")
    builder.adjust(2) # Ikki ustun ko'rinishida (alohida-alohida)
    
    await message.answer(
        "🏫 **Universitetni tanlang:**\n\nYangiliklarini ko'rmoqchi bo'lgan universitetni tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("uni_news_"))
async def show_uni_news(callback: types.CallbackQuery):
    uni_name = callback.data.replace("uni_news_", "")
    await callback.message.edit_text(f"⏳ **{uni_name}** yangiliklari yuklanmoqda...", parse_mode="Markdown")
    
    news = await fetch_news(uni_name)
    
    if not news:
        return await callback.message.edit_text(
            f"❌ **{uni_name}** saytidan yangiliklarni olib bo'lmadi.\nIltimos, keyinroq urinib ko'ring.",
            reply_markup=InlineKeyboardBuilder().button(text="🔙 Orqaga", callback_data="uni_main").as_markup(),
            parse_mode="Markdown"
        )
    
    text = f"📰 **{uni_name} yangiliklari:**\n\n"
    for item in news:
        text += f"• [{item['title']}]({item['link']})\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="uni_main")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data == "uni_main")
async def back_to_uni_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for uni in UNIVERSITY_SITES.keys():
        builder.button(text=uni, callback_data=f"uni_news_{uni}")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "🏫 **Universitetni tanlang:**\n\nYangiliklarini ko'rmoqchi bo'lgan universitetni tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
