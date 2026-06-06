from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import is_premium
from services.ai_service import ai_check_essay
import datetime

router = Router()

class EssayStates(StatesGroup):
    waiting_for_essay = State()

# Rate limiting
# Rate limiting
DAILY_LIMIT = 30 # Premium users get high limit

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    from database import get_setting
    today = datetime.date.today().isoformat()
    key = f"usage_essay_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    if count >= DAILY_LIMIT:
        return False, 0
    return True, DAILY_LIMIT - count

def increment_usage(user_id: int):
    from database import get_setting, set_setting
    today = datetime.date.today().isoformat()
    key = f"usage_essay_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    set_setting(key, str(count + 1))

def get_cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "✍️ Insho Tekshiruvchi")
async def start_essay_checker(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer(
            "✍️ **Insho Tekshiruvchi - Premium Xizmat**\n\n"
            "Bu funksiya faqat Premium foydalanuvchilar uchun.\n\n"
            "Insho Tekshiruvchi:\n"
            "✅ Grammatika xatolarini topadi\n"
            "✅ Uslub tavsiyalari beradi\n"
            "✅ Baho qo'yadi (5 ball)\n"
            "✅ Yaxshilash yo'llarini ko'rsatadi\n\n"
            "Premium sotib oling!",
            parse_mode="Markdown"
        )
    
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        return await message.answer(
            "⚠️ **Kunlik limit tugadi**\n\n"
            f"Siz bugun {DAILY_LIMIT} ta insho tekshirdingiz.\n"
            "Ertaga yana foydalanishingiz mumkin!",
            parse_mode="Markdown"
        )
    
    await state.set_state(EssayStates.waiting_for_essay)
    await message.answer(
        "✍️ **Insho Tekshiruvchi**\n\n"
        "Inshongizni yuboring (matn yoki fayl):\n\n"
        f"📊 Bugun qolgan: **Cheksiz**\n\n"
        "💡 Maksimal: 3000 belgi",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )

@router.message(EssayStates.waiting_for_essay, F.text == "❌ Bekor qilish")
async def cancel_essay(message: types.Message, state: FSMContext):
    from ..common import get_main_menu
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

@router.message(EssayStates.waiting_for_essay)
async def check_essay(message: types.Message, state: FSMContext):
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        from ..common import get_main_menu
        await state.clear()
        return await message.answer(
            "⚠️ Kunlik limit tugadi!",
            reply_markup=get_main_menu(message.from_user.id)
        )
    
    essay_text = message.text
    
    if len(essay_text) < 50:
        return await message.answer(
            "❌ Insho juda qisqa! Kamida 50 belgi bo'lishi kerak."
        )
    
    await message.answer("🔍 Tekshirilmoqda...")
    
    try:
        feedback = await ai_check_essay(essay_text)
        
        increment_usage(message.from_user.id)
        remaining -= 1
        
        from ..common import get_main_menu
        await message.answer(
            f"✍️ **Insho Tahlili:**\n\n"
            f"{feedback}\n\n"
            f"📊 Bugun qolgan: **Cheksiz**",
            reply_markup=get_main_menu(message.from_user.id),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    finally:
        await state.clear()
