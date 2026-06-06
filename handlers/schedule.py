from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import add_schedule, get_schedule, delete_schedule

router = Router()

class ScheduleStates(StatesGroup):
    waiting_for_schedule_data = State()

DAYS = {
    "1": "Dushanba",
    "2": "Seshanba",
    "3": "Chorshanba",
    "4": "Payshanba",
    "5": "Juma",
    "6": "Shanba",
    "7": "Yakshanba"
}

@router.message(F.text == "🔔 Eslatma")
async def show_schedule_menu(message: types.Message):
    schedule = get_schedule(message.from_user.id)
    
    if not schedule:
        text = "Sizda hali eslatmalar yo'q.\n\n"
    else:
        text = "🔔 **Sizning eslatmalaringiz:**\n\n"
        current_day = ""
        for day, subject, time, loc in schedule:
            day_name = DAYS.get(day, day)
            if day_name != current_day:
                text += f"\n📌 **{day_name}:**\n"
                current_day = day_name
            text += f"🔹 {time} - {subject} ({loc})\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Qo'shish", callback_data="sched_add")
    builder.button(text="🗑 Tozalash", callback_data="sched_clear")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "sched_add")
async def start_add_schedule(callback: types.CallbackQuery, state: FSMContext):
    from .konspekt import get_cancel_kb
    await callback.message.answer(
        "Eslatmani quyidagi formatda yuboring (har birini yangi qatorda):\n"
        "Kun_raqami; Vaqt; Fan nomi; Xona\n\n"
        "**Kun raqamlari:**\n"
        "1-Dushanba, 2-Seshanba, ..., 6-Shanba\n\n"
        "**Misol:**\n"
        "1; 08:30; Matematika; 302-xona",
        parse_mode="Markdown",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(ScheduleStates.waiting_for_schedule_data)
    await callback.answer()

@router.message(ScheduleStates.waiting_for_schedule_data)
async def process_schedule_data(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    lines = message.text.strip().splitlines()
    success_count = 0
    
    for line in lines:
        try:
            parts = line.split(";")
            if len(parts) >= 3:
                day = parts[0].strip()
                time = parts[1].strip()
                subject = parts[2].strip()
                loc = parts[3].strip() if len(parts) > 3 else "Noaniq"
                
                add_schedule(message.from_user.id, day, subject, time, loc)
                success_count += 1
        except Exception:
            continue
            
    if success_count > 0:
        from .common import get_main_menu
        await message.answer(f"✅ {success_count} ta eslatma qo'shildi!", reply_markup=get_main_menu(message.from_user.id))
    else:
        from .common import get_main_menu
        await message.answer("❌ Noto'g'ri format. Iltimos qaytadan urinib ko'ring.", reply_markup=get_main_menu(message.from_user.id))
    
    await state.clear()

@router.callback_query(F.data == "sched_clear")
async def clear_schedule_call(callback: types.CallbackQuery):
    delete_schedule(callback.from_user.id)
    await callback.message.edit_text("✅ Eslatmalar tozalandi.")
    await callback.answer()
