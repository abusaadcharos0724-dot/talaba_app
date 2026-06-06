from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import is_premium
from services.ai_service import ai_generate_flashcards
import datetime

router = Router()

class FlashcardStates(StatesGroup):
    waiting_for_topic = State()

# Rate limiting
# Rate limiting
DAILY_LIMIT = 100 # Premium users get high limit

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    from database import get_setting
    today = datetime.date.today().isoformat()
    key = f"usage_flash_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    if count >= DAILY_LIMIT:
        return False, 0
    return True, DAILY_LIMIT - count

def increment_usage(user_id: int):
    from database import get_setting, set_setting
    today = datetime.date.today().isoformat()
    key = f"usage_flash_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    set_setting(key, str(count + 1))


def get_cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "🎴 Flashcards")
async def start_flashcards(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer(
            "🎴 **Flashcards - Premium Xizmat**\n\n"
            "Bu funksiya faqat Premium foydalanuvchilar uchun.\n\n"
            "Flashcards:\n"
            "✅ Mavzu bo'yicha avtomatik yaratiladi\n"
            "✅ Savol-javob formatida\n"
            "✅ Yodlash uchun eng yaxshi usul\n"
            "✅ Imtihonga tayyorgarlik\n\n"
            "Premium sotib oling!",
            parse_mode="Markdown"
        )
    
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        return await message.answer(
            "⚠️ **Kunlik limit tugadi**\n\n"
            f"Siz bugun {DAILY_LIMIT} ta flashcard set yaratdingiz.\n"
            "Ertaga yana foydalanishingiz mumkin!",
            parse_mode="Markdown"
        )
    
    await state.set_state(FlashcardStates.waiting_for_topic)
    await message.answer(
        "🎴 **Flashcard Generator**\n\n"
        "Mavzuni kiriting (10 ta flashcard yaratiladi):\n\n"
        f"📊 Bugun qolgan: **Cheksiz**\n\n"
        "💡 Masalan:\n"
        "- Biologiya: Hujayralar\n"
        "- Tarix: O'rta Osiyo tarixi\n"
        "- Ingliz tili: Irregular verbs",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )

@router.message(FlashcardStates.waiting_for_topic, F.text == "❌ Bekor qilish")
async def cancel_flashcards(message: types.Message, state: FSMContext):
    from ..common import get_main_menu
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

@router.message(FlashcardStates.waiting_for_topic)
async def generate_flashcards(message: types.Message, state: FSMContext):
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        from ..common import get_main_menu
        await state.clear()
        return await message.answer(
            "⚠️ Kunlik limit tugadi!",
            reply_markup=get_main_menu(message.from_user.id)
        )
    
    topic = message.text
    await message.answer("⏳ Flashcardlar yaratilmoqda...")
    
    try:
        flashcards = await ai_generate_flashcards(topic, count=10)
        
        increment_usage(message.from_user.id)
        remaining -= 1
        
        from ..common import get_main_menu
        await message.answer(
            f"🎴 **Flashcards - {topic}**\n\n"
            f"{flashcards}\n\n"
            f"📊 Bugun qolgan: **Cheksiz**\n\n"
            f"💡 Har kuni takrorlang!",
            reply_markup=get_main_menu(message.from_user.id),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    finally:
        await state.clear()
