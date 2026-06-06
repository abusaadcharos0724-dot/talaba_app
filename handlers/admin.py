import datetime
import asyncio
import os
from aiogram import types, Router, F, html
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import (
    get_pending_payments, update_payment_status, set_premium, add_book, 
    get_all_users, add_channel, get_all_channels, delete_channel, 
    get_detailed_stats, get_all_tg_ids, add_template, get_all_templates, 
    delete_template, set_setting, get_now, revoke_premium
)
from config import ADMIN_ID

router = Router()

class AdminStates(StatesGroup):
    waiting_for_book_file = State()
    waiting_for_book_type = State()
    waiting_for_book_title = State()
    waiting_for_book_category = State()
    waiting_for_channel_title = State()
    waiting_for_channel_url = State()
    waiting_for_broadcast = State()
    waiting_for_template = State()
    waiting_for_template_name = State()
    waiting_for_template_category = State()
    waiting_for_admin_contact = State()
    waiting_for_mandatory_channel = State()
    waiting_for_new_category_name = State()
    waiting_for_premium_price = State()
    waiting_for_humo_card = State()
    waiting_for_openai_key = State()
    waiting_for_gemini_key = State()

class PaymentStates(StatesGroup):
    waiting_for_proof = State()

@router.message(StateFilter("*"), F.text == "🔑 Boshqaruv Paneli")
async def admin_dashboard(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    text = (
        "🔑 **Boshqaruv Paneli**\n\n"
        "Botni boshqarish uchun kerakli bo'limni tanlang:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats_view")
    builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast_view")
    builder.button(text="💳 To'lovlar", callback_data="admin_payments_view")
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users_view")
    builder.button(text="📚 Kitoblar", callback_data="admin_books_view")
    builder.button(text="➕ Kitob qo'shish", callback_data="admin_add_book_start")
    builder.button(text="🔗 Kanallar", callback_data="admin_channel_view")
    builder.button(text="🎨 Shablonlar", callback_data="admin_template_view")
    builder.button(text="🖼 QR Kodlar", callback_data="admin_qr_view")
    builder.button(text="⚙️ Sozlamalar", callback_data="admin_settings_view")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(F.document, AdminStates.waiting_for_template)
async def handle_template_upload_state(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith((".pptx", ".ppt")):
        return await message.answer("❌ Iltimos, .pptx formatidagi fayl yuklang.")
    
    await state.update_data(file_template_id=message.document.file_id)
    await message.answer("Ushbu shablon uchun nom kiriting (masalan: 'Biznes', 'Akademik'):")
    await state.set_state(AdminStates.waiting_for_template_name)
    
@router.message(AdminStates.waiting_for_template_name)
async def handle_template_name_state(message: types.Message, state: FSMContext):
    await state.update_data(template_name=message.text.strip())
    await message.answer("Ushbu shablon qaysi bo'limga tegishli? (masalan: Biznes, Ta'lim, Tibbiyot):")
    await state.set_state(AdminStates.waiting_for_template_category)

@router.message(AdminStates.waiting_for_template_category)
async def handle_template_category_state(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = data['file_template_id']
    name = data['template_name']
    category = message.text.strip()
    
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    
    os.makedirs("data/templates", exist_ok=True)
    import time
    filename = f"template_{int(time.time())}.pptx"
    destination = os.path.join("data/templates", filename)
    
    await message.bot.download_file(file_path, destination)
    
    add_template(name, category, destination)
    await message.answer(f"✅ Yangi shablon '{name}' '{category}' bo'limiga muvaffaqiyatli qo'shildi!")
    await state.clear()

@router.message(F.document, F.caption == "/set_template", F.chat.id == ADMIN_ID)
async def handle_set_template(message: types.Message):
    # Keep legacy magic command support
    if not message.document.file_name.endswith((".pptx", ".ppt")):
        return await message.answer("❌ Iltimos, .pptx formatidagi fayl yuklang.")
    
    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    
    os.makedirs("data/templates", exist_ok=True)
    destination = "data/templates/default.pptx"
    
    await message.bot.download_file(file_path, destination)
    await message.answer("✅ Yangi shablon muvaffaqiyatli o'rnatildi! Endi prezentatsiyalar ushbu dizayn asosida yaratiladi.")
@router.message(StateFilter("*"), F.text == "/payments", F.chat.id == ADMIN_ID)
async def admin_payments(message: types.Message):
    rows = get_pending_payments()
    if not rows:
        return await message.answer("Kutayotgan to'lovlar yo'q.")
    
    for pid, tg, amt, card, proof, created in rows:
        text = f"ID: {pid}\nUser: {tg}\nSumma: {amt}\nKarta: {card}\nSana: {created}"
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Tasdiqlash", callback_data=f"pay_ok_{pid}_{tg}")
        builder.button(text="❌ Rad etish", callback_data=f"pay_no_{pid}_{tg}")
        
        await message.answer(text, reply_markup=builder.as_markup())
        if proof:
            try:
                await message.answer_photo(proof, caption=f"To'lov isboti (ID: {pid})")
            except Exception:
                await message.answer_document(proof, caption=f"To'lov isboti (ID: {pid})")

@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Siz admin emassiz.")
    
    parts = callback.data.split("_")
    action = parts[1]
    pid = int(parts[2])
    tg_id = int(parts[3])
    
    if action == "ok":
        update_payment_status(pid, "approved")
        set_premium(tg_id)
        await callback.message.edit_text(f"✅ To'lov (ID: {pid}) tasdiqlandi!")
        await callback.bot.send_message(tg_id, "🎉 To'lovingiz tasdiqlandi! Premium statusi faollashtirildi.")
    else:
        update_payment_status(pid, "rejected")
        await callback.message.edit_text(f"❌ To'lov (ID: {pid}) rad etildi.")
        await callback.bot.send_message(tg_id, "❌ Uzr, sizning to'lovingiz rad etildi. Iltimos admin bilan bog'laning.")
    
    await callback.answer()

@router.message(StateFilter("*"), F.text == "👥 Foydalanuvchilar")
@router.callback_query(F.data == "admin_users_view")
async def admin_users_list(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    print(f"DEBUG: admin_users_list called by {user_id}")
    if user_id != ADMIN_ID:
        print(f"DEBUG: Permission denied. User ID {user_id} != Admin ID {ADMIN_ID}")
        return

    # Acknowledge callback immediately
    if isinstance(event, types.CallbackQuery):
        await event.answer("Yuklanmoqda...")

    try:
        users = get_all_users()
        print(f"DEBUG: Found {len(users)} users in database")
        if not users:
            msg = "Bazada foydalanuvchilar yo'q."
            if isinstance(event, types.CallbackQuery):
                await event.message.answer(msg)
            else:
                await event.answer(msg)
            return
        
        # Prepare content
        now = get_now()
        premium_count = 0
        user_lines = []
        
        for u in users:
            tg_id, is_prem, until, created, full_name, username = u
            status = "❌"
            expiry = ""
            if is_prem and until:
                try:
                    until_dt = datetime.datetime.fromisoformat(until)
                    if until_dt > now:
                        status = "🌟"
                        premium_count += 1
                        diff = until_dt - now
                        expiry = f" ({diff.days} d)" if diff.days > 0 else " (today)"
                    else:
                        status = "⌛"
                except:
                    status = "❓"

            name = html.quote(full_name) if full_name else f"User {tg_id}"
            uname = f" (@{username})" if username else ""
            line = f"{status} <a href='tg://user?id={tg_id}'>{name}</a>{uname}{expiry}\n"
            line += f"   └ ID: <code>{tg_id}</code> | /prem_{tg_id} /unprem_{tg_id}"
            user_lines.append(line)

        # Send in batches
        batch_size = 20
        total_msg = f"👥 <b>Foydalanuvchilar ro'yxati</b>\nJami: {len(users)} | Premium: {premium_count}\n\n"
        
        for i in range(0, len(user_lines), batch_size):
            batch_text = "\n\n".join(user_lines[i:i+batch_size])
            msg_to_send = (total_msg if i == 0 else "") + batch_text
            
            if isinstance(event, types.CallbackQuery):
                await event.message.answer(msg_to_send, parse_mode="HTML")
            else:
                await event.answer(msg_to_send, parse_mode="HTML")
        
        print("DEBUG: User list sent successfully")
                
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"DEBUG ERROR: {error_trace}")
        err_msg = f"❌ Tizimda xatolik: {str(e)}"
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(err_msg)
        else:
            await event.answer(err_msg)

@router.message(F.text.startswith("/prem_"), F.chat.id == ADMIN_ID)
async def admin_give_premium(message: types.Message):
    try:
        tg_id = int(message.text.split("_")[1])
        set_premium(tg_id, 30)
        await message.answer(f"✅ Foydalanuvchi {tg_id} ga 30 kunlik Premium berildi.")
    except Exception as e:
        await message.answer(f"Xato: {e}")

@router.message(F.text.startswith("/unprem_"), F.chat.id == ADMIN_ID)
async def admin_revoke_premium(message: types.Message):
    try:
        tg_id = int(message.text.split("_")[1])
        revoke_premium(tg_id)
        await message.answer(f"❌ Foydalanuvchi {tg_id} dan Premium olib qo'yildi.")
    except Exception as e:
        await message.answer(f"Xato: {e}")

@router.message(StateFilter("*"), F.text == "🌟 Premium sotib olish")
async def premium_info(message: types.Message, state: FSMContext):
    from config import PREMIUM_PRICE, HUMO_CARD
    await message.answer(
        f"🌟 **Premium imkoniyatlari:**\n"
        "- Cheksiz AI referatlar\n"
        "- Uzoq matnlarni konspektlash\n"
        "- Reklamasiz foydalanish (kelgusida)\n\n"
        f"Narxi: **{PREMIUM_PRICE} so'm** / 30 kun\n"
        f"Karta: `{HUMO_CARD}`\n\n"
        "💳 **To'lovni amalga oshirgach, chekni (rasm yoki fayl) shu yerning o'zida botga yuboring.**\n"
        "Admin tekshiruvidan so'ng Premium statusi avtomatik faollashadi.",
        parse_mode="Markdown"
    )
    await state.set_state(PaymentStates.waiting_for_proof)
    await state.set_state(PaymentStates.waiting_for_proof)

@router.message(PaymentStates.waiting_for_proof, F.text == "❌ Bekor qilish")
async def cancel_payment(message: types.Message, state: FSMContext):
    from handlers.common import get_main_menu
    await state.clear()
    await message.answer("To'lov bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

@router.message(PaymentStates.waiting_for_proof, F.photo | F.document)
async def handle_payment_proof(message: types.Message, state: FSMContext):
    from database import add_payment
    from config import PREMIUM_PRICE, HUMO_CARD
    
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    
    if file_id:
        add_payment(message.from_user.id, PREMIUM_PRICE, HUMO_CARD, file_id)
        
        # Notify Admin
        user_name = html.quote(message.from_user.full_name)
        user_link = f'<a href="tg://user?id={message.from_user.id}">{user_name}</a>'
        
        admin_text = (
            f"🚀 <b>Yangi to'lov isboti!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user_link}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"💰 <b>Summa:</b> {PREMIUM_PRICE} so'm\n\n"
            f"Tasdiqlash uchun: <b>Boshqaruv Paneli -> To'lovlar</b> bo'limiga o'ting."
        )
        
        try:
            await message.bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except Exception as e:
            import logging
            logging.error(f"Failed to notify admin about payment: {e}")

        await message.answer("✅ **To'lov isboti qabul qilindi!**\n\nAdmin tez orada tekshirib, Premium statusini faollashtiradi. Sabringiz uchun rahmat!", parse_mode="Markdown")
        await state.clear()

# Book Management
@router.message(StateFilter("*"), Command("addbook"), F.chat.id == ADMIN_ID)
async def admin_add_book(message: types.Message, state: FSMContext):
    await message.answer("Kitob faylini yuboring (yoki kanaldan forward qiling):")
    await state.set_state(AdminStates.waiting_for_book_file)

@router.message(AdminStates.waiting_for_book_file, F.document | F.audio | F.video)
async def handle_admin_book_file(message: types.Message, state: FSMContext):
    fid = message.document.file_id if message.document else (message.audio.file_id if message.audio else message.video.file_id)
    await state.update_data(file_id=fid)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 PDF", callback_data="admin_set_type_pdf")
    builder.button(text="🎧 Audio", callback_data="admin_set_type_audio")
    builder.adjust(2)
    
    await message.answer("Kitob turini tanlang:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.waiting_for_book_type)

@router.callback_query(F.data == "admin_add_book_start")
async def start_add_book_flow(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Kitob faylini yuboring (yoki kanaldan forward qiling):")
    await state.set_state(AdminStates.waiting_for_book_file)
    await callback.answer()

@router.callback_query(F.data == "admin_books_view")
async def view_books_categories(callback: types.CallbackQuery):
    from database import get_book_categories
    categories = get_book_categories()
    
    if not categories:
        return await callback.message.edit_text("Hozircha kitoblar yo'q.", reply_markup=None)
        
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"📂 {cat}", callback_data=f"admin_cat_{cat}")
    
    builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
    builder.adjust(2)
    
    await callback.message.edit_text("📚 **Kitoblar bo'limlari:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("admin_cat_"))
async def view_books_in_category(callback: types.CallbackQuery):
    category = callback.data.replace("admin_cat_", "")
    from database import get_books_by_category
    from aiogram import html
    
    books = get_books_by_category(category)
    if not books:
         return await callback.answer("Bu bo'limda kitoblar yo'q.")
    
    # Use HTML to handle special chars like backticks in category names safely
    cat_safe = html.quote(category)
    text = f"📂 <b>{cat_safe}</b> bo'limidagi kitoblar:\n(O'chirish uchun ustiga bosing)\n\n"
    builder = InlineKeyboardBuilder()
    
    for book_id, title, _ in books:
        builder.button(text=f"❌ {title}", callback_data=f"del_book_{book_id}_{category}")
    
    # Add rename button
    builder.button(text="✏️ Bo'lim nomini o'zgartirish", callback_data=f"admin_ren_cat_{category}")
    builder.button(text="🔙 Orqaga", callback_data="admin_books_view")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_ren_cat_"))
async def rename_category_start(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("admin_ren_cat_", "")
    await state.update_data(renaming_category=category)
    await callback.message.answer(f"📂 **{category}** bo'limi uchun yangi nom kiriting:")
    await state.set_state(AdminStates.waiting_for_new_category_name)
    await callback.answer()

@router.message(AdminStates.waiting_for_new_category_name)
async def rename_category_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_name = data.get("renaming_category")
    new_name = message.text.strip()
    
    from database import update_book_category
    update_book_category(old_name, new_name)
    
    await message.answer(f"✅ Bo'lim nomi o'zgartirildi:\n\n'{old_name}' ➡️ '{new_name}'")
    await state.clear()
    
    # Show updated categories list
    from database import get_book_categories
    categories = get_book_categories()
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"📂 {cat}", callback_data=f"admin_cat_{cat}")
    builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
    builder.adjust(2)
    # We send a new message because the previous one was likely the prompt
    await message.answer("📚 **Kitoblar bo'limlari:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("del_book_"))
async def delete_book_handler(callback: types.CallbackQuery):
    from database import delete_book_by_id
    # callback.data format: del_book_{id}_{category}
    # We need to be careful if category contains underscores.
    # Safe way: extract id (fixed position or regex) and the rest is category.
    # "del_book_" is 9 chars.
    payload = callback.data[9:] # {id}_{category}
    parts = payload.split("_", 1) # Split only on the FIRST underscore found in payload
    
    if len(parts) < 2:
        return await callback.answer("Xatolik: Ma'lumot formati buzilgan.")
        
    book_id = int(parts[0])
    category = parts[1]
    
    try:
        delete_book_by_id(book_id)
        await callback.answer("Kitob o'chirildi ✅")
        
        # Refresh list
        # We call the view function again, effectively "redirecting"
        # We need to construct a fake callback or just run the logic.
        # Running logic is cleaner to avoid recursion limit or object creation issues.
        from database import get_books_by_category
        from aiogram import html
        
        books = get_books_by_category(category)
        
        if not books:
            # Category empty, go back to categories
            await view_books_categories(callback)
        else:
            cat_safe = html.quote(category)
            text = f"📂 <b>{cat_safe}</b> bo'limidagi kitoblar:\n(O'chirish uchun ustiga bosing)\n\n"
            builder = InlineKeyboardBuilder()
            for bid, title, _ in books:
                builder.button(text=f"❌ {title}", callback_data=f"del_book_{bid}_{category}")
            
            # Add rename button
            builder.button(text="✏️ Bo'lim nomini o'zgartirish", callback_data=f"admin_ren_cat_{category}")
            builder.button(text="🔙 Orqaga", callback_data="admin_books_view")
            builder.adjust(1)
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)


@router.callback_query(F.data == "admin_dashboard")
async def back_to_dashboard(callback: types.CallbackQuery):
    await callback.message.delete()
    # Or edit text to dashboard
    text = (
        "🔑 **Boshqaruv Paneli**\n\n"
        "Botni boshqarish uchun kerakli bo'limni tanlang:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats_view")
    builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast_view")
    builder.button(text="💳 To'lovlar", callback_data="admin_payments_view")
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users_view")
    builder.button(text="📚 Kitoblar", callback_data="admin_books_view")
    builder.button(text="➕ Kitob qo'shish", callback_data="admin_add_book_start")
    builder.button(text="➕ Kitob qo'shish", callback_data="admin_add_book_start")
    builder.button(text="🔗 Kanallar", callback_data="admin_channel_view")
    builder.button(text="🎨 Shablonlar", callback_data="admin_template_view")
    builder.button(text="🖼 QR Kodlar", callback_data="admin_qr_view")
    builder.button(text="⚙️ Sozlamalar", callback_data="admin_settings_view")
    builder.adjust(2)
    
    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(AdminStates.waiting_for_book_type, F.data.startswith("admin_set_type_"))
async def handle_admin_book_type(callback: types.CallbackQuery, state: FSMContext):
    btype = callback.data.replace("admin_set_type_", "")
    await state.update_data(book_type=btype)
    await callback.message.edit_text(f"Tanlangan tur: {btype.upper()}\n\nEndi kitob nomini kiriting:")
    await state.set_state(AdminStates.waiting_for_book_title)
    await callback.answer()

@router.message(AdminStates.waiting_for_book_title)
async def handle_admin_book_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Bo'lim (kategoriya) nomini kiriting (masalan: Badiiy, Siyosiy, IT):")
    await state.set_state(AdminStates.waiting_for_book_category)

@router.message(AdminStates.waiting_for_book_category)
async def handle_admin_book_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    add_book(data['title'], message.text, data['file_id'], data['book_type'])
    await message.answer(f"✅ Kitob muvaffaqiyatli qo'shildi!\n\n**Turi:** {data['book_type'].upper()}\n**Nomi:** {data['title']}\n**Bo'lim:** {message.text}", parse_mode="Markdown")
    await state.clear()

# Channel Management

# Channel Management
@router.callback_query(F.data == "admin_channel_view")
async def admin_list_channels(callback: types.CallbackQuery):
    channels = get_all_channels()
    if not channels:
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Kanal qo'shish", callback_data="admin_add_channel_start")
        builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
        return await callback.message.edit_text("Hozircha kanallar yo'q.", reply_markup=builder.as_markup())
    
    builder = InlineKeyboardBuilder()
    text = "🔗 **Faol Kanallar:**\n\n(O'chirish uchun kanal nomini bosing)"
    
    for cid, title, url in channels:
        builder.button(text=f"❌ {title}", callback_data=f"del_channel_{cid}")
        
    builder.button(text="➕ Kanal qo'shish", callback_data="admin_add_channel_start")
    builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("del_channel_"))
async def delete_channel_handler(callback: types.CallbackQuery):
    cid = int(callback.data.replace("del_channel_", ""))
    delete_channel(cid)
    
    # Refresh list
    await admin_list_channels(callback)
    await callback.answer("Kanal o'chirildi ✅")

@router.callback_query(F.data == "admin_add_channel_start")
async def start_add_channel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Kanal nomini kiriting (masalan: 🎓 Talaba Uz):")
    await state.set_state(AdminStates.waiting_for_channel_title)
    await callback.answer()

@router.message(AdminStates.waiting_for_channel_title)
async def handle_admin_channel_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Kanal havolasini (URL) yuboring (masalan: https://t.me/talaba_uz):")
    await state.set_state(AdminStates.waiting_for_channel_url)

@router.message(AdminStates.waiting_for_channel_url)
async def handle_admin_channel_url(message: types.Message, state: FSMContext):
    if message.text in ["🔑 Boshqaruv Paneli", "Asosiy menyu", "🏠 Asosiy menyu"]:
        return
        
    url = message.text.strip()
    if not (url.startswith("http") or url.startswith("t.me/") or url.startswith("@")):
        return await message.answer("❌ **Xato!**\n\nIltimos, to'g'ri havola yuboring.\nMasalan: `https://t.me/kanal` yoki `@kanal`", parse_mode="Markdown")
    
    data = await state.get_data()
    add_channel(data['title'], url)
    await message.answer(f"✅ Kanal muvaffaqiyatli qo'shildi!\n\n**Nomi:** {data['title']}\n**URL:** {url}")
    await state.clear()


@router.callback_query(F.data.startswith("del_chan_"))
async def handle_delete_channel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Siz admin emassiz.")
    
    cid = int(callback.data.replace("del_chan_", ""))
    delete_channel(cid)
    await callback.message.delete()
    await callback.answer("Kanal o'chirildi.")

# Broadcast & Stats
@router.message(StateFilter("*"), Command("stats"), F.chat.id == ADMIN_ID)
async def admin_stats(message: types.Message):
    s = get_detailed_stats()
    from database import get_source_stats
    src_stats = get_source_stats()
    
    text = (
        "📊 **Bot Statistikasi:**\n\n"
        f"👥 Jami foydalanuvchilar: {s['total']}\n"
        f"🌟 Premium foydalanuvchilar: {s['premium']}\n"
        f"🆕 Bugun qo'shilganlar: {s['new_today']}\n"
        f"📚 Kutubxonada kitoblar: {s['books']}\n"
        f"⏰ Faol deadline'lar: {s['deadlines']}\n\n"
        "📍 **Manbalar bo'yicha (QR):**\n"
        f"🎓 Universitet: {src_stats.get('uni', 0)}\n"
        f"🚌 Bekatlar: {src_stats.get('bekat', 0)}\n"
        f"🏙 Ko'chada: {src_stats.get('kocha', 0)}\n"
        f"❓ Noma'lum: {s['total'] - sum(src_stats.values())}"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(StateFilter("*"), Command("broadcast"), F.chat.id == ADMIN_ID)
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing (yoki rasm yuboring):")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def handle_admin_broadcast(message: types.Message, state: FSMContext):
    ids = get_all_tg_ids()
    await message.answer(f"⏳ Xabar {len(ids)} ta foydalanuvchiga yuborilmoqda...")
    
    count = 0
    for tid in ids:
        try:
            await message.copy_to(tid)
            count += 1
            # Small delay to avoid flood
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga muvaffaqiyatli yetib bordi.")
    await state.clear()

# Callback handlers for the dashboard
@router.callback_query(F.data == "admin_stats_view")
async def cb_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await admin_stats(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_view")
async def cb_admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await admin_broadcast_start(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "admin_payments_view")
async def cb_admin_payments(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await admin_payments(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_users_view")
async def cb_admin_users(callback: types.CallbackQuery):
    # This is now handled by the unified admin_users_list above
    pass

@router.callback_query(F.data == "admin_book_view")
async def cb_admin_book(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await admin_add_book(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "admin_channel_view")
async def cb_admin_channel(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await admin_add_channel(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "admin_template_view")
async def cb_admin_template_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    
    from database import get_template_categories
    categories = get_template_categories()
    
    text = "🎨 **Shablonlar boshqaruvi**\n\nBo'limni tanlang yoki yangi shablon qo'shing:"
    builder = InlineKeyboardBuilder()
    
    if categories:
        for cat in categories:
            builder.button(text=f"📁 {cat}", callback_data=f"adm_tpl_cat_{cat}")
    
    builder.button(text="➕ Yangi shablon qo'shish", callback_data="admin_add_template")
    builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_tpl_cat_"))
async def admin_templates_in_category(callback: types.CallbackQuery):
    category = callback.data.replace("adm_tpl_cat_", "")
    from database import get_templates_by_category
    templates = get_templates_by_category(category)
    
    text = f"📁 **{category}** bo'limidagi shablonlar:\n\nO'chirish uchun x tugmasini bosing:"
    builder = InlineKeyboardBuilder()
    
    if templates:
        for tid, name, path in templates:
            builder.button(text=f"❌ {name}", callback_data=f"del_temp_{tid}_{category}")
    
    builder.button(text="🔙 Orqaga", callback_data="admin_template_view")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_qr_view")
async def cb_admin_qr_view(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    
    bot_info = await callback.bot.get_me()
    username = bot_info.username
    
    sources = {
        "uni": "🎓 Universitet",
        "bekat": "🚌 Bekatlar",
        "kocha": "🏙 Ko'chada"
    }
    
    await callback.message.answer("🖼 **Sizning kuzatuv (tracking) QR kodlaringiz:**", parse_mode="Markdown")
    
    for code, label in sources.items():
        link = f"https://t.me/{username}?start={code}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={link}"
        await callback.message.answer_photo(
            qr_url,
            caption=f"📍 **Manba:** {label}\n🔗 **Havola:** `{link}`",
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data == "admin_add_template")
async def cb_admin_add_template(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await callback.message.answer("Yangi .pptx shablon faylini yuboring:")
    await state.set_state(AdminStates.waiting_for_template)
    await callback.answer()

@router.callback_query(F.data.startswith("del_temp_"))
async def cb_admin_del_template(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    parts = callback.data.split("_")
    tid = int(parts[2])
    
    delete_template(tid)
    await callback.answer("Shablon o'chirildi.")
    
    if len(parts) > 3:
        # We have a category to return to
         category = parts[3]
         from database import get_templates_by_category
         templates = get_templates_by_category(category)
         if templates:
             # Refresh the category view
             builder = InlineKeyboardBuilder()
             for tid, name, path in templates:
                 builder.button(text=f"❌ {name}", callback_data=f"del_temp_{tid}_{category}")
             builder.button(text="🔙 Orqaga", callback_data="admin_template_view")
             builder.adjust(1)
             return await callback.message.edit_text(f"📁 **{category}** bo'limidagi shablonlar:", reply_markup=builder.as_markup(), parse_mode="Markdown")

    await cb_admin_template_menu(callback)


@router.callback_query(F.data == "admin_set_mandatory")
async def cb_admin_set_mandatory(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return await callback.answer("Siz admin emassiz.")
    await callback.message.answer("Majburiy kanal foydalanuvchi nomini kiriting (masalan: @talaba_uz):")
    await state.set_state(AdminStates.waiting_for_mandatory_channel)
    await callback.answer()

@router.message(AdminStates.waiting_for_mandatory_channel)
async def handle_mandatory_channel_update(message: types.Message, state: FSMContext):
    channel = message.text.strip()
    if not channel.startswith("@"):
        return await message.answer("Xato! Kanal nomi @ belgisidan boshlanishi kerak.")
    
    set_setting("mandatory_channel", channel)
    await message.answer(f"✅ Majburiy kanal muvaffaqiyatli o'zgartirildi: {channel}")
    await state.clear()

# --- Dynamic Settings Management ---

@router.callback_query(F.data == "admin_settings_view")
async def cb_admin_settings(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    from database import get_setting
    from config import PREMIUM_PRICE, HUMO_CARD
    
    # Get current values from DB or defaults from config
    price = get_setting("premium_price", str(PREMIUM_PRICE))
    card = get_setting("humo_card", HUMO_CARD)
    contact = get_setting("admin_contact", "@Abusaadl7")
    channel = get_setting("mandatory_channel", "@talaba_uz")
    
    text = (
        "⚙️ **Bot Sozlamalari**\n\n"
        f"💰 Premium narxi: `{price}` so'm\n"
        f"💳 Karta: `{card}`\n"
        f"📞 Admin: `{contact}`\n"
        f"📢 Majburiy kanal: `{channel}`\n\n"
        "O'zgartirish uchun kerakli tugmani bosing:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Narxni o'zgartirish", callback_data="set_cfg_price")
    builder.button(text="💳 Kartani o'zgartirish", callback_data="set_cfg_card")
    builder.button(text="📞 Kontaktni o'zgartirish", callback_data="set_cfg_contact")
    builder.button(text="📢 Majburiy kanal", callback_data="admin_set_mandatory")
    builder.button(text="🔑 OpenAI Key", callback_data="set_cfg_openai")
    builder.button(text="💎 Gemini Key", callback_data="set_cfg_gemini")
    builder.button(text="🔙 Orqaga", callback_data="admin_dashboard")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_cfg_"))
async def cb_start_set_cfg(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.replace("set_cfg_", "")
    
    if field == "price":
        await callback.message.answer("Yangi Premium narxini kiriting (faqat raqam):")
        await state.set_state(AdminStates.waiting_for_premium_price)
    elif field == "card":
        await callback.message.answer("Yangi karta raqamini kiriting:")
        await state.set_state(AdminStates.waiting_for_humo_card)
    elif field == "contact":
        await callback.message.answer("Yangi admin kontaktini kiriting (masalan: @username):")
        await state.set_state(AdminStates.waiting_for_admin_contact)
    elif field == "openai":
        await callback.message.answer("Yangi OpenAI API Key kiriting:")
        await state.set_state(AdminStates.waiting_for_openai_key)
    elif field == "gemini":
        await callback.message.answer("Yangi Gemini API Key kiriting:")
        await state.set_state(AdminStates.waiting_for_gemini_key)
    
    await callback.answer()

@router.message(AdminStates.waiting_for_premium_price)
async def set_price_handler(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Xato! Faqat raqam kiriting.")
    set_setting("premium_price", message.text)
    await message.answer(f"✅ Premium narxi o'zgartirildi: {message.text} so'm")
    await state.clear()

@router.message(AdminStates.waiting_for_humo_card)
async def set_card_handler(message: types.Message, state: FSMContext):
    set_setting("humo_card", message.text.strip())
    await message.answer(f"✅ Karta raqami o'zgartirildi: {message.text}")
    await state.clear()

@router.message(AdminStates.waiting_for_admin_contact)
async def set_contact_handler(message: types.Message, state: FSMContext):
    set_setting("admin_contact", message.text.strip())
    await message.answer(f"✅ Admin kontakti o'zgartirildi: {message.text}")
    await state.clear()

@router.message(AdminStates.waiting_for_openai_key)
async def set_openai_handler(message: types.Message, state: FSMContext):
    set_setting("openai_api_key", message.text.strip())
    await message.answer("✅ OpenAI API Key o'zgartirildi!")
    await state.clear()

@router.message(AdminStates.waiting_for_gemini_key)
async def set_gemini_handler(message: types.Message, state: FSMContext):
    set_setting("gemini_api_key", message.text.strip())
    await message.answer("✅ Gemini API Key o'zgartirildi!")
    await state.clear()
