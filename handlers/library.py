from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_book_categories, get_books_by_category, get_book_by_id

router = Router()

@router.message(F.text == "📚 Onlayn kutubxona")
async def show_library_types(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 PDF kutubxona", callback_data="lib_type_pdf")
    builder.button(text="🎧 Audio kutubxona", callback_data="lib_type_audio")
    builder.adjust(1)
    
    await message.answer("📚 **Kutubxona bo'limini tanlang:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("lib_type_"))
async def show_library_categories(callback: types.CallbackQuery):
    btype = callback.data.replace("lib_type_", "")
    categories = get_book_categories(btype)
    
    if not categories:
        return await callback.answer("Bu bo'limda hozircha kitoblar yo'q.", show_alert=True)
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"lib_cat_{btype}_{cat}")
    builder.button(text="🔙 Orqaga", callback_data="lib_main")
    builder.adjust(2)
    
    type_name = "PDF" if btype == "pdf" else "Audio"
    await callback.message.edit_text(f"📚 **{type_name} kutubxonasi bo'limlari:**\n\nKerakli bo'limni tanlang:", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("lib_cat_"))
async def show_books_in_category(callback: types.CallbackQuery):
    # format: lib_cat_{type}_{category}
    # "lib_cat_" is 8 chars
    payload = callback.data[8:] # {type}_{category}
    parts = payload.split("_", 1) # Split type and category
    
    btype = parts[0]
    cat = parts[1]
    
    from aiogram import html
    cat_safe = html.quote(cat)
    
    books = get_books_by_category(cat, btype)
    
    if not books:
        return await callback.answer("Bu bo'limda kitoblar yo'q.", show_alert=True)
    
    builder = InlineKeyboardBuilder()
    for i, (bid, title, fid) in enumerate(books):
        # First 10 (0-9) are free, others get premium icon
        display_title = title if i < 10 else f"💎 {title}"
        builder.button(text=display_title, callback_data=f"lib_file_{bid}")
    
    builder.button(text="🔙 Orqaga", callback_data=f"lib_type_{btype}")
    builder.adjust(1)
    
    await callback.message.edit_text(f"📖 <b>{cat_safe}</b> bo'limidagi kitoblar:", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "lib_main")
async def back_to_types(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 PDF kutubxona", callback_data="lib_type_pdf")
    builder.button(text="🎧 Audio kutubxona", callback_data="lib_type_audio")
    builder.adjust(1)
    await callback.message.edit_text("📚 **Kutubxona bo'limini tanlang:**", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("lib_file_"))
async def send_book_file(callback: types.CallbackQuery):
    from database import is_premium
    bid = int(callback.data.replace("lib_file_", ""))
    book = get_book_by_id(bid)
    
    if not book:
        return await callback.answer("Kitob topilmadi.", show_alert=True)
    
    title, fid, cat, btype = book
    
    # Check if user needs premium for this book
    # Fetch all books in category to find this book's rank
    all_books = get_books_by_category(cat, btype)
    book_index = -1
    for i, (item_id, _, _) in enumerate(all_books):
        if item_id == bid:
            book_index = i
            break
            
    if book_index >= 10 and not is_premium(callback.from_user.id):
        return await callback.message.answer(
            "💎 **Premium Kitob**\n\n"
            "Ushbu kitob faqat Premium foydalanuvchilar uchun.\n"
            "Har bir bo'limda birinchi 10 ta kitob bepul.\n\n"
            "Cheksiz foydalanish uchun Premium sotib oling!",
            reply_markup=InlineKeyboardBuilder().button(text="🌟 Premium sotib olish", callback_data="lib_buy_premium").as_markup()
        )

    try:
        if btype == 'pdf':
            await callback.message.answer_document(fid, caption=f"📖 **{title}**")
        else:
            await callback.message.answer_audio(fid, caption=f"🎧 **{title}**")
    except Exception:
        await callback.message.answer_document(fid, caption=f"📚 **{title}**")
        
    await callback.answer("Kitob yuborildi.")

@router.callback_query(F.data == "lib_buy_premium")
async def lib_buy_premium(callback: types.CallbackQuery):
    from handlers.common import start_premium
    await start_premium(callback.message)
    await callback.answer()
