from aiogram import types, Router, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ai_service import ai_summarize
from services.file_parser import extract_from_docx, extract_from_pdf, extract_from_image
from database import is_premium
from config import TEMP_DIR
import os

router = Router()

class KonspektStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_photo = State()

def get_cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


# Removed direct button handlers for Fayl/Foto Konspekt as they are now global and automatic


@router.message(F.text == "🔙 Orqaga")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    from .common import get_main_menu
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id))

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: types.Message, state: FSMContext):
    from .common import get_main_menu
    await state.clear()
    await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

@router.message(StateFilter(None), F.document)
async def handle_global_document(message: types.Message, state: FSMContext):
    doc = message.document
    fn = doc.file_name.lower()
    
    if not (fn.endswith(".pdf") or fn.endswith(".docx")):
        return await message.answer("Men faqat .pdf va .docx formatdagi fayllarni o'qiy olaman.")
        
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Konspekt qilish", callback_data=f"doc_konspekt_{doc.file_id}")
    builder.button(text="🇺🇿 Tarjima qilish", callback_data=f"doc_translate_{doc.file_id}")
    builder.adjust(1)
    
    await message.answer("Fayl qabul qilindi. Nima qilamiz?", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("doc_konspekt_"))
async def process_doc_konspekt(callback: types.CallbackQuery):
    file_id = callback.data.replace("doc_konspekt_", "")
    await callback.message.edit_text("Fayl o'qilmoqda...")
    
    # Get document info
    # Since we only have file_id, we need to get the file object from bot
    file = await callback.bot.get_file(file_id)
    path = os.path.join(TEMP_DIR, f"{file_id}.tmp")
    await callback.bot.download_file(file.file_path, destination=path)
    
    # Simple extension guess based on content or we can assume it's valid from previous filter
    # Actually, without filename we try PDF first, then DOCX
    text = ""
    try:
        text = extract_from_pdf(path)
    except:
        try:
            text = extract_from_docx(path)
        except:
            pass
            
    if os.path.exists(path): os.remove(path)
    
    if not text.strip():
        return await callback.message.edit_text("Faylni o'qishda muammo bo'ldi yoki fayl bo'sh.")
        
    await callback.message.edit_text("⏳ Tahlil qilinmoqda...")
    res = await ai_summarize(text)
    await callback.message.edit_text(f"📄 **Fayldan konspekt:**\n\n{res}", parse_mode="Markdown")

@router.callback_query(F.data.startswith("doc_translate_"))
async def process_doc_translate(callback: types.CallbackQuery):
    await callback.answer("Tarjima qilish funksiyasi tez orada qo'shiladi! 🚀", show_alert=True)

@router.message(StateFilter(None), F.photo)
async def handle_global_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Konspekt (Matn o'qish)", callback_data=f"photo_konspekt_{photo.file_id}")
    builder.button(text="📝 Vazifani yechish", callback_data=f"photo_solve_{photo.file_id}")
    builder.adjust(1)
    
    await message.answer("Rasm qabul qilindi. Qanday yordam bera olaman?", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("photo_konspekt_"))
async def process_photo_konspekt(callback: types.CallbackQuery):
    file_id = callback.data.replace("photo_konspekt_", "")
    await callback.message.edit_text("Rasm yuklab olinmoqda...")
    
    file = await callback.bot.get_file(file_id)
    path = os.path.join(TEMP_DIR, f"{file_id}.jpg")
    await callback.bot.download_file(file.file_path, destination=path)
    
    await callback.message.edit_text("⏳ AI orqali matn o'qilib konspekt qilinmoqda...")
    from services.gemini_service import gemini_vision
    res = await gemini_vision(path, "Ushbu rasmdagi matnni o'qib chiq va uni chiroyli, mazmunli konspekt (summary) ko'rinishida yozib ber. O'zbek tilida.")
    
    if os.path.exists(path): os.remove(path)
    await callback.message.edit_text(f"📄 **Rasmdan konspekt:**\n\n{res}", parse_mode="Markdown")

@router.callback_query(F.data.startswith("photo_solve_"))
async def process_photo_solve(callback: types.CallbackQuery):
    file_id = callback.data.replace("photo_solve_", "")
    await callback.message.edit_text("Vazifa tahlil qilinmoqda...")
    
    file = await callback.bot.get_file(file_id)
    path = os.path.join(TEMP_DIR, f"{file_id}.jpg")
    await callback.bot.download_file(file.file_path, destination=path)
    
    await callback.message.edit_text("⏳ AI masalani yechmoqda...")
    from services.ai_service import ai_solve_homework
    res = await ai_solve_homework(path)
    
    if os.path.exists(path): os.remove(path)
    await callback.message.edit_text(f"✅ **Yechim:**\n\n{res}", parse_mode="Markdown")

