from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database import is_premium
from services.ai_service import ai_chat_tutor
import datetime

router = Router()

class AITutorStates(StatesGroup):
    chatting = State()

# Rate limiting
# Rate limiting
DAILY_LIMIT = 200 # Premium users get high limit

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    from database import get_setting
    today = datetime.date.today().isoformat()
    key = f"usage_tutor_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    if count >= DAILY_LIMIT:
        return False, 0
    return True, DAILY_LIMIT - count

def increment_usage(user_id: int):
    from database import get_setting, set_setting
    today = datetime.date.today().isoformat()
    key = f"usage_tutor_{user_id}_{today}"
    count = int(get_setting(key, "0"))
    set_setting(key, str(count + 1))

def get_tutor_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🗑 Suhbatni tozalash"))
    builder.row(types.KeyboardButton(text="🔙 Orqaga"))
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "🤖 AI Tutor")
async def start_ai_tutor(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer(
            "🤖 **AI Tutor - Premium Xizmat**\n\n"
            "Bu funksiya faqat Premium foydalanuvchilar uchun.\n\n"
            "AI Tutor sizga:\n"
            "✅ Istalgan savolga javob beradi\n"
            "✅ Mavzularni tushuntiradi\n"
            "✅ Masalalar yechishda yordam beradi\n"
            "✅ Suhbat tarixini eslab qoladi\n\n"
            "Premium sotib oling va AI Tutor'dan foydalaning!",
            parse_mode="Markdown"
        )
    
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        return await message.answer(
            "⚠️ **Kunlik limit tugadi**\n\n"
            f"Siz bugun {DAILY_LIMIT} ta xabar yubordingiz.\n"
            "Ertaga yana {DAILY_LIMIT} ta xabar yuborishingiz mumkin!",
            parse_mode="Markdown"
        )
    
    await state.set_state(AITutorStates.chatting)
    await state.update_data(chat_history=[])
    
    await message.answer(
        "🤖 **AI Tutor faollashtirildi!**\n\n"
        "Men sizning shaxsiy o'qituvchingizman. Istalgan savolni bering!\n\n"
        f"📊 Bugun qolgan xabarlar: **Cheksiz**\n\n"
        "💡 Masalan:\n"
        "- Kvant fizikasini tushuntiring\n"
        "- Pythonda list va tuple farqi nima?\n"
        "- Bu masalani yeching: 2x + 5 = 15",
        reply_markup=get_tutor_menu(),
        parse_mode="Markdown"
    )

@router.message(AITutorStates.chatting, F.text == "🗑 Suhbatni tozalash")
async def clear_chat(message: types.Message, state: FSMContext):
    await state.update_data(chat_history=[])
    await message.answer(
        "✅ Suhbat tarixi tozalandi!\n\n"
        "Yangi mavzudan boshlashingiz mumkin.",
        parse_mode="Markdown"
    )

@router.message(AITutorStates.chatting, F.text == "🔙 Orqaga")
async def exit_tutor(message: types.Message, state: FSMContext):
    from ..common import get_main_menu
    await state.clear()
    await message.answer(
        "👋 AI Tutor yopildi. Keyingi safar ko'rishguncha!",
        reply_markup=get_main_menu(message.from_user.id)
    )

@router.message(AITutorStates.chatting)
async def handle_tutor_message(message: types.Message, state: FSMContext):
    # Rate limit check
    can_use, remaining = check_rate_limit(message.from_user.id)
    if not can_use:
        return await message.answer(
            "⚠️ **Kunlik limit tugadi**\n\n"
            f"Siz bugun {DAILY_LIMIT} ta xabar yubordingiz.\n"
            "Ertaga yana foydalanishingiz mumkin!",
            parse_mode="Markdown"
        )
    
    # Get chat history
    data = await state.get_data()
    chat_history = data.get("chat_history", [])
    
    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Get AI response
    user_message = message.text
    response = await ai_chat_tutor(user_message, chat_history)
    
    # Update chat history (keep last 5 messages for context)
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": response})
    chat_history = chat_history[-10:]  # Keep last 5 exchanges (10 messages)
    
    await state.update_data(chat_history=chat_history)
    
    # Increment usage
    increment_usage(message.from_user.id)
    remaining -= 1
    
    # Send response
    await message.answer(
        f"{response}\n\n"
        f"📊 Bugun qolgan: **Cheksiz**",
        parse_mode="Markdown"
    )
