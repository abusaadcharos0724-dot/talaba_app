from aiogram import types, Router, F, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

router = Router()

class QuizStates(StatesGroup):
    waiting_for_quiz_answer = State()

# Quiz questions database
QUIZ_QUESTIONS = {
    "matematika": [
        {
            "question": "2 + 2 * 2 = ?",
            "options": ["6", "8", "4", "10"],
            "correct": 0,
            "explanation": "Avval ko'paytirish: 2*2=4, keyin qo'shish: 2+4=6"
        },
        {
            "question": "√16 = ?",
            "options": ["2", "4", "8", "16"],
            "correct": 1,
            "explanation": "4 * 4 = 16, demak √16 = 4"
        },
        {
            "question": "10% dan 200 = ?",
            "options": ["10", "20", "30", "40"],
            "correct": 1,
            "explanation": "200 * 0.1 = 20"
        }
    ],
    "ingliz_tili": [
        {
            "question": "I ___ a student.",
            "options": ["am", "is", "are", "be"],
            "correct": 0,
            "explanation": "'I' bilan 'am' ishlatiladi"
        },
        {
            "question": "'Kitob' inglizcha:",
            "options": ["Book", "Pen", "Table", "Chair"],
            "correct": 0,
            "explanation": "Book = Kitob"
        }
    ],
    "informatika": [
        {
            "question": "HTML nima?",
            "options": ["Dasturlash tili", "Markup tili", "Database", "OS"],
            "correct": 1,
            "explanation": "HTML - HyperText Markup Language"
        },
        {
            "question": "Python'da o'zgaruvchi e'lon qilish:",
            "options": ["var x = 5", "int x = 5", "x = 5", "let x = 5"],
            "correct": 2,
            "explanation": "Python'da to'g'ridan-to'g'ri x = 5 deb yoziladi"
        }
    ]
}

@router.message(F.text == "🎯 Kunlik quiz")
async def daily_quiz(message: types.Message, state: FSMContext):
    # Random category
    category = random.choice(list(QUIZ_QUESTIONS.keys()))
    questions = QUIZ_QUESTIONS[category]
    question_data = random.choice(questions)
    
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(question_data["options"]):
        builder.button(
            text=f"{chr(65+i)}. {option}",
            callback_data=f"quiz_{category}_{i}_{question_data['correct']}"
        )
    builder.adjust(2)
    
    question_text = html.quote(question_data["question"])
    await message.answer(
        f"🎯 <b>Kunlik Quiz</b> - {html.quote(category.replace('_', ' ').title())}\n\n"
        f"❓ {question_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Store question data for later
    await state.update_data(quiz_explanation=question_data["explanation"])

@router.callback_query(F.data.startswith("quiz_"))
async def process_quiz_answer(callback: types.CallbackQuery, state: FSMContext):
    # callback.data format: quiz_{category}_{user_answer}_{correct}
    # Be careful not to catch q_next/q_stop if they start with quiz_ (they don't now, but just prefix check)
    payload = callback.data[5:] # remove "quiz_"
    if payload in ["next", "stop"]: return # Legacy support safety
    
    parts = payload.rsplit("_", 2)
    if len(parts) < 3:
        return await callback.answer("Eski savol. Iltimos, yangisini boshlang.")
        
    category = parts[0]
    user_answer = int(parts[1])
    correct_answer = int(parts[2])
    
    data = await state.get_data()
    explanation = html.quote(data.get("quiz_explanation", "Tushuntirish mavjud emas."))
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Keyingi savol", callback_data="q_next")
    builder.button(text="🔙 Tugatish", callback_data="q_stop")
    builder.adjust(2)
    
    if user_answer == correct_answer:
        await callback.message.edit_text(
            f"✅ <b>To'g'ri javob!</b>\n\n"
            f"💡 Tushuntirish: {explanation}\n\n"
            f"🎉 Ajoyib! Davom etamizmi?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        correct_letter = chr(65 + correct_answer)
        await callback.message.edit_text(
            f"❌ <b>Noto'g'ri javob</b>\n\n"
            f"✅ To'g'ri javob: <b>{correct_letter}</b>\n"
            f"💡 Tushuntirish: {explanation}\n\n"
            f"📚 Bilimingizni oshirishda davom eting!",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "q_next")
async def handle_quiz_next(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await daily_quiz(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "q_stop")
async def handle_quiz_stop(callback: types.CallbackQuery, state: FSMContext):
    from handlers.common import get_main_menu
    await state.clear()
    await callback.message.edit_text("✅ Quiz yakunlandi. Bilim olishdan to'xtamang!", parse_mode="HTML")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()
