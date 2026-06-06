from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import is_premium
from services.ai_service import ai_solve_homework
from config import TEMP_DIR
import datetime
import os

router = Router()

class HomeworkStates(StatesGroup):
    waiting_for_image = State()

# Rate limiting
# Rate limiting
DAILY_LIMIT = 50 # Premium users get high limit

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    from database import get_setting
    today = datetime.date.today().isoformat()
    key = f"usage_hw_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    if count >= DAILY_LIMIT:
        return False, 0
    return True, DAILY_LIMIT - count

def increment_usage(user_id: int):
    from database import get_setting, set_setting
    today = datetime.date.today().isoformat()
    key = f"usage_hw_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    set_setting(key, str(count + 1))

def get_cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "📝 Vazifa Yechuvchi")
async def start_homework_solver(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer(
            "📝 **Vazifa Yechuvchi - Premium Xizmat**\n\n"
            "Bu funksiya faqat Premium foydalanuvchilar uchun.\n\n"
            "Vazifa Yechuvchi:\n"
            "✅ Masala rasmini tahlil qiladi\n"
            "✅ Qadam-baqadam yechim beradi\n"
            "✅ Tushuntirish bilan\n"
            "✅ Matematika, Fizika, Kimyo\n\n"
            "Premium sotib oling!",
            parse_mode="Markdown"
        )
    
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        return await message.answer(
            "⚠️ **Kunlik limit tugadi**\n\n"
            f"Siz bugun {DAILY_LIMIT} ta vazifa yubordingiz.\n"
            "Ertaga yana foydalanishingiz mumkin!",
            parse_mode="Markdown"
        )
    
    await state.set_state(HomeworkStates.waiting_for_image)
    await message.answer(
        "📝 **Vazifa Yechuvchi**\n\n"
        "Vazifa yoki masalaning rasmini yuboring.\n\n"
        f"📊 Bugun qolgan: **Cheksiz**\n\n"
        "💡 Yaxshi natija uchun:\n"
        "- Rasm aniq bo'lsin\n"
        "- Matn o'qilishi oson bo'lsin\n"
        "- Bir vazifa bir rasm",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )

@router.message(HomeworkStates.waiting_for_image, F.text == "❌ Bekor qilish")
async def cancel_homework(message: types.Message, state: FSMContext):
    from ..common import get_main_menu
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

@router.message(HomeworkStates.waiting_for_image, F.photo)
async def handle_homework_image(message: types.Message, state: FSMContext):
    # Rate limit check
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        from ..common import get_main_menu
        await state.clear()
        return await message.answer(
            "⚠️ Kunlik limit tugadi!",
            reply_markup=get_main_menu(message.from_user.id)
        )
    
    # Download image
    photo = message.photo[-1]
    path = os.path.join(TEMP_DIR, f"homework_{message.from_user.id}_{photo.file_id}.jpg")
    await message.bot.download(photo, destination=path)
    
    await message.answer("🔍 Tahlil qilinmoqda... (10-30 soniya)")
    
    try:
        # Solve homework using AI Vision
        solution = await ai_solve_homework(path)
        
        # Increment usage
        increment_usage(message.from_user.id)
        remaining -= 1
        
        from ..common import get_main_menu
        await message.answer(
            f"✅ **Yechim:**\n\n{solution}\n\n"
            f"📊 Bugun qolgan: **Cheksiz**",
            reply_markup=get_main_menu(message.from_user.id),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            "Iltimos, qaytadan urinib ko'ring yoki boshqa rasm yuboring."
        )
    finally:
        if os.path.exists(path):
            os.remove(path)
        await state.clear()

@router.message(HomeworkStates.waiting_for_image)
async def invalid_homework_input(message: types.Message):
    await message.answer(
        "❌ Iltimos, rasm yuboring!\n\n"
        "Vazifa yoki masalaning rasmini yuboring."
    )
