from aiogram import types, Router, F, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ai_service import ai_generate_referat, ai_generate_test, ai_generate_ppt_content
from database import is_premium, add_deadline, get_due_deadlines
from utils.docx_gen import create_referat_docx
from utils.pptx_gen import create_presentation_pptx
from config import TEMP_DIR
import datetime
import os

router = Router()

class StudentStates(StatesGroup):
    waiting_for_referat_topic = State()
    waiting_for_test_topic = State()
    waiting_for_deadline_title = State()
    waiting_for_deadline_time = State()
    waiting_for_gpa_data = State()
    waiting_for_ppt_topic = State()

# Referat
@router.message(F.text == "🧾 Referat (AI)")
async def get_referat_topic(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer("Referat generatori faqat Premium foydalanuvchilar uchun.")
    
    from .konspekt import get_cancel_kb
    await message.answer("Referat mavzusini yozing:", reply_markup=get_cancel_kb())
    await state.set_state(StudentStates.waiting_for_referat_topic)

@router.message(StudentStates.waiting_for_referat_topic)
async def handle_referat(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    await message.answer("⏳ AI referat yozmoqda (taxminan 1-2 daqiqa)...")
    from .common import get_main_menu
    res = await ai_generate_referat(message.text)
    
    # Generate and send DOCX
    safe_topic = "".join([c for c in message.text if c.isalnum() or c==' ']).strip()[:30]
    filename = f"referat_{message.from_user.id}_{safe_topic}.docx"
    filepath = os.path.join(TEMP_DIR, filename)
    
    try:
        create_referat_docx(message.text, res, filepath)
        await message.answer_document(
            types.FSInputFile(filepath),
            caption=f"📄 **Mavzu:** {message.text}\n\nTayyor referatni yuklab oling!",
            parse_mode="Markdown",
            reply_markup=get_main_menu(message.from_user.id)
        )
    except Exception as e:
        await message.answer(f"Xato yuz berdi: {e}")
        # Fallback to text if docx fails
        for i in range(0, len(res), 4000):
            await message.answer(res[i:i+4000], reply_markup=get_main_menu(message.from_user.id) if i+4000 >= len(res) else None)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            
    await state.clear()

# Test Generator
@router.message(F.text == "📚 Test generator")
async def get_test_topic(message: types.Message, state: FSMContext):
    from .konspekt import get_cancel_kb
    await message.answer("Test mavzusini va savollar sonini yuboring (Masalan: Informatika 10):", reply_markup=get_cancel_kb())
    await state.set_state(StudentStates.waiting_for_test_topic)

@router.message(StudentStates.waiting_for_test_topic)
async def handle_test(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    text = message.text.strip()
    count = 5
    topic = text
    
    # Try different separators
    if ";" in text:
        parts = text.split(";")
        topic = parts[0].strip()
        if parts[1].strip().isdigit():
            count = int(parts[1].strip())
    else:
        parts = text.split()
        if len(parts) > 1 and parts[-1].isdigit():
            count = int(parts.pop())
            topic = " ".join(parts)
    
    await message.answer(f"⏳ <b>{html.quote(topic)}</b> bo'yicha {count} ta test tayyorlanmoqda...", parse_mode="HTML")
    from .common import get_main_menu
    res = await ai_generate_test(topic, count)
    
    # Split response if too long
    for i in range(0, len(res), 4000):
        # AI output typically contains markdown, but since we use HTML mode, we should be careful.
        # Actually, for test generation, the AI usually returns Markdown. 
        # Safest is to disable parsing for the big block or try to convert.
        # Let's use Markdown parsing for the content if it's markdown, but be careful with the initial message.
        # Wait, if AI returns Markdown (**bold**), and we use HTML, it won't render.
        # We should keep Markdown for the AI response part IF we trust the AI output.
        # But previous errors were due to user input/filenames.
        # For this specific block, let's stick to Markdown but ensure previous messages were safe.
        # Actually, let's just use NO parse_mode for the big content block to be safe, 
        # or Markdown if we are confident. AI models adhere to markdown well usually.
        # The crash happens when we mix user input with markdown characters.
        await message.answer(res[i:i+4000], reply_markup=get_main_menu(message.from_user.id) if i+4000 >= len(res) else None)
    await state.clear()

# GPA Hisoblash
@router.message(F.text == "🧮 GPA hisoblash")
async def ask_gpa(message: types.Message, state: FSMContext):
    from .konspekt import get_cancel_kb
    await message.answer(
        "Baholaringizni quyidagi formatda yuboring:\n"
        "Fan_nomi Baho Kredit\n"
        "Masalan:\n"
        "Matematika 90 5\n"
        "Tarix 85 3",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(StudentStates.waiting_for_gpa_data)

@router.message(StudentStates.waiting_for_gpa_data)
async def handle_gpa(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    lines = message.text.strip().splitlines()
    total_points = 0.0
    total_credits = 0.0
    errors = []
    processed_count = 0

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line: continue
        
        parts = line.split()
        if len(parts) < 2:
            errors.append(f"{i}-qator: Ma'lumot yetarli emas (Baho va Kredit bo'lishi shart).")
            continue
            
        try:
            # Parse from right to left
            # Format: Subject Name Score Credit
            # Example: Mathematics 90 5 or History of Art 85 4
            if len(parts) < 2:
                errors.append(f"{i}-qator: Ma'lumot yetarli emas.")
                continue
                
            credit_str = parts[-1].replace(",", ".")
            score_str = parts[-2].replace(",", ".")
            
            credit = float(credit_str)
            score = float(score_str)
            
            if not (0 <= score <= 100):
                errors.append(f"{i}-qator: Baho 0 va 100 oralig'ida bo'lishi kerak.")
                continue
            
            grade = (score/100.0) * 4.0
            total_points += grade * credit
            total_credits += credit
            processed_count += 1
        except ValueError:
             errors.append(f"{i}-qator: Baho yoki Kredit raqam bo'lishi kerak.")

    from .common import get_main_menu
    from aiogram import html
    if errors:
        error_text = "\n".join(errors[:5])
        if len(errors) > 5: error_text += "\n..."
        await message.answer(f"⚠️ <b>Ba'zi qatorlarda xatolik aniqlandi:</b>\n\n{html.quote(error_text)}\n\nIltimos, formatni tekshirib qaytadan urinib ko'ring.", parse_mode="HTML")
        # Don't clear state, let user try again or cancel
    elif processed_count == 0:
        await message.answer("❌ Hech qanday ma'lumot qayta ishlanmadi. Iltimos, namunadagidek yuboring.")
    else:
        gpa = total_points / total_credits
        await message.answer(
            f"✅ <b>GPA hisoblandi!</b>\n\n"
            f"📚 Fanlar soni: {processed_count}\n"
            f"🔢 Jami kreditlar: {total_credits}\n"
            f"📊 Sizning GPA: <b>{gpa:.2f}</b>", 
            parse_mode="HTML", 
            reply_markup=get_main_menu(message.from_user.id)
        )
        await state.clear()

# Deadline
@router.message(F.text == "⏰ Deadline qo'shish")
async def ask_deadline_title(message: types.Message, state: FSMContext):
    from .konspekt import get_cancel_kb
    await message.answer("Vazifa nomini (sarlavhasini) kiriting:", reply_markup=get_cancel_kb())
    await state.set_state(StudentStates.waiting_for_deadline_title)

@router.message(StudentStates.waiting_for_deadline_title)
async def handle_deadline_title(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    await state.update_data(title=message.text)
    from .konspekt import get_cancel_kb
    await message.answer(
        "Muddatni kiriting (Masalan: `30.12.2025 18:00` yoki `18:00` - bugungi kun uchun):",
        parse_mode="Markdown",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(StudentStates.waiting_for_deadline_time)

@router.message(StudentStates.waiting_for_deadline_time)
async def handle_deadline_time(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    text = message.text.strip()
    try:
        now = datetime.datetime.now()
        # Simple parsing logic
        if len(text) <= 5 and ":" in text: # HH:MM format
            tm = datetime.datetime.strptime(text, "%H:%M")
            due = now.replace(hour=tm.hour, minute=tm.minute, second=0, microsecond=0)
            if due < now: # If time passed today, assume tomorrow
                 due += datetime.timedelta(days=1)
        else: # Full date
            # Support DD.MM.YYYY HH:MM or YYYY-MM-DD HH:MM
            for fmt in ["%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M", "%d.%m.%Y"]:
                try:
                    due = datetime.datetime.strptime(text, fmt)
                    break
                except: continue
            else:
                raise ValueError("Format error")

        data = await state.get_data()
        from ..database import add_deadline
        from .common import get_main_menu
        from aiogram import html
        
        # Safe title
        safe_title = html.quote(data.get('title', 'Vazifa'))
        
        add_deadline(message.from_user.id, data['title'], due.isoformat())
        await message.answer(
            f"✅ <b>Sizning deadline'ingiz saqlandi!</b>\n\n"
            f"📌 <b>Vazifa:</b> {safe_title}\n"
            f"⏰ <b>Muddat:</b> {due.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Bot sizga 1 kun va 1 soat qolganda eslatadi.",
            parse_mode="HTML",
            reply_markup=get_main_menu(message.from_user.id)
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Sana formati noto'g'ri. Iltimos, `30.12.2025 18:00` kabi formatda yuboring.", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

@router.message(F.text == "📋 Mening deadline'larim")
async def show_deadlines(message: types.Message):
    from ..database import get_user_deadlines
    rows = get_user_deadlines(message.from_user.id)
    
    if not rows:
        return await message.answer("Sizda hozircha faol deadline'lar yo'q.")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    text = "📋 **Sizning deadline'laringiz:**\n\n"
    builder = InlineKeyboardBuilder()
    
    for rid, title, due in rows:
        dt = datetime.datetime.fromisoformat(due)
        text += f"🔹 **{title}**\n   📅 {dt.strftime('%d.%m.%Y %H:%M')}\n\n"
        builder.button(text=f"🗑 {title[:15]}...", callback_data=f"dl_del_{rid}")
    
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("dl_del_"))
async def process_dl_delete(callback: types.CallbackQuery):
    from ..database import delete_deadline
    dl_id = int(callback.data.replace("dl_del_", ""))
    delete_deadline(dl_id)
    await callback.answer("O'chirildi.")
    await callback.message.edit_text("✅ Tanlangan deadline o'chirildi.")

# Presentation Generator
@router.message(F.text == "📊 Prezentatsiya (AI)")
async def ask_ppt_topic(message: types.Message, state: FSMContext):
    if not is_premium(message.from_user.id):
        return await message.answer("Prezentatsiya generatori faqat Premium foydalanuvchilar uchun.")
    
    from .konspekt import get_cancel_kb
    await message.answer("Slaydlar uchun mavzuni kiriting:", reply_markup=get_cancel_kb())
    await state.set_state(StudentStates.waiting_for_ppt_topic)

@router.message(StudentStates.waiting_for_ppt_topic)
async def handle_ppt_topic(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        from .common import get_main_menu
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
    
    await state.update_data(ppt_topic=message.text)
    
    from database import get_template_categories
    categories = get_template_categories()
    
    if not categories:
        # If no custom categories, show default directly or fallback to "all templates"
        from database import get_all_templates
        templates = get_all_templates()
        if not templates:
            await message.answer("⏳ Prezentatsiya tayyorlanmoqda (taxminan 30 soniya)...")
            return await start_ppt_generation(message, state, None)
            
        builder = InlineKeyboardBuilder()
        for tid, name, cat, path in templates:
            builder.button(text=name, callback_data=f"ppt_tpl_{tid}")
        builder.button(text="Standart (Ko'k)", callback_data="ppt_tpl_default")
        builder.adjust(2)
        await message.answer("Prezentatsiya uchun dizaynni tanlang:", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        for cat in categories:
            builder.button(text=cat, callback_data=f"ppt_cat_{cat}")
        builder.button(text="Standart (Ko'k)", callback_data="ppt_tpl_default")
        builder.adjust(2)
        await message.answer("Prezentatsiya uchun bo'limni tanlang:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("ppt_cat_"))
async def handle_ppt_category_selection(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("ppt_cat_", "")
    from database import get_templates_by_category
    templates = get_templates_by_category(category)
    
    if not templates:
        return await callback.answer("Ushbu bo'limda shablonlar yo'q.")
        
    builder = InlineKeyboardBuilder()
    for tid, name, path in templates:
        builder.button(text=name, callback_data=f"ppt_tpl_{tid}")
    
    builder.button(text="🔙 Orqaga", callback_data="ppt_back_to_cats")
    builder.adjust(2)
    
    await callback.message.edit_text(f"📁 **{category}** bo'limidagi shablonlar:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "ppt_back_to_cats")
async def handle_ppt_back_to_cats(callback: types.CallbackQuery, state: FSMContext):
    from database import get_template_categories
    categories = get_template_categories()
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"ppt_cat_{cat}")
    builder.button(text="Standart (Ko'k)", callback_data="ppt_tpl_default")
    builder.adjust(2)
    await callback.message.edit_text("Prezentatsiya uchun bo'limni tanlang:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("ppt_tpl_"))
async def handle_ppt_template_selection(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    topic = data.get('ppt_topic')
    if not topic:
        return await callback.answer("Xatolik: Mavzu topilmadi.")
    
    tpl_id_str = callback.data.replace("ppt_tpl_", "")
    template_path = None
    
    if tpl_id_str != "default":
        from database import get_template_by_id
        res = get_template_by_id(int(tpl_id_str))
        if res:
            template_path = res[1]
    
    await callback.message.edit_text(f"⏳ <b>{html.quote(topic)}</b> bo'yicha prezentatsiya tayyorlanmoqda...", parse_mode="HTML")
    await start_ppt_generation(callback.message, state, template_path, topic)
    await callback.answer()

async def start_ppt_generation(message: types.Message, state: FSMContext, template_path: str, topic: str = None):
    if not topic:
        data = await state.get_data()
        topic = data.get('ppt_topic')
    
    content = await ai_generate_ppt_content(topic)
    
    filename = f"presentation_{message.chat.id}.pptx"
    filepath = os.path.join(TEMP_DIR, filename)
    
    try:
        from .common import get_main_menu
        create_presentation_pptx(topic, content, filepath, template_path)
        await message.answer_document(
            types.FSInputFile(filepath),
            caption=f"📊 **Mavzu:** {topic}\n\nSizning prezentatsiyangiz tayyor!",
            reply_markup=get_main_menu(message.chat.id)
        )
    except Exception as e:
        await message.answer(f"Xato yuz berdi: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            
    await state.clear()
