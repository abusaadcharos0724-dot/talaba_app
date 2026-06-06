from aiogram import types, Router, F, html
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from database import ensure_user, is_premium, increment_referral, set_premium, get_setting, get_user, get_now
from config import ADMIN_ID
from utils.check_sub import is_subscribed
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime

router = Router()

def get_webapp_keyboard(user_id: int):
    # Fetch webapp URL from settings, default to localhost
    webapp_url = get_setting("webapp_url", "http://127.0.0.1:8000/")
    
    # Append user context to the URL if needed (can be used for fallback authentication)
    # Outside Telegram, we can pass user_id as a parameter
    url_with_param = webapp_url
    if "?" in webapp_url:
        url_with_param += f"&tg_id={user_id}"
    else:
        url_with_param += f"?tg_id={user_id}"
        
    builder = InlineKeyboardBuilder()
    
    # WebApp button (only HTTPS is allowed for WebApp, else use regular url button)
    if url_with_param.startswith("https://"):
        builder.button(
            text="🚀 Ilovani ochish", 
            web_app=types.WebAppInfo(url=url_with_param)
        )
    else:
        builder.button(
            text="🚀 Brauzerda ochish", 
            url=url_with_param
        )
    
    # If admin, show admin panel link too
    if user_id == ADMIN_ID:
        admin_url = f"{webapp_url}admin"
        if admin_url.startswith("https://"):
            builder.button(
                text="🔑 Admin Panelni ochish",
                web_app=types.WebAppInfo(url=admin_url)
            )
        else:
            builder.button(
                text="🔑 Admin Panelni ochish",
                url=admin_url
            )
        
    builder.adjust(1)
    return builder.as_markup()

@router.message(StateFilter("*"), CommandStart())
async def cmd_start(message: types.Message):
    args = message.text.split()
    referrer_id = None
    source = None
    
    if len(args) > 1:
        arg = args[1]
        if arg.isdigit():
            referrer_id = int(arg)
            if referrer_id == message.from_user.id:
                referrer_id = None
        elif arg in ["uni", "bekat", "kocha"]:
            source = arg

    is_new_user = ensure_user(
        message.from_user.id, 
        referrer_id, 
        source, 
        message.from_user.full_name, 
        message.from_user.username
    )
    
    if is_new_user and referrer_id:
        new_count = increment_referral(referrer_id)
        if new_count > 0 and new_count % 10 == 0:
            set_premium(referrer_id, 30)
            try:
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 **Tabriklaymiz!**\n\nSiz 10-do'stingizni taklif qildingiz.\nMukofot tariqasida sizga **1 oy (30 kun) Premium** berildi! ✅"
                )
            except Exception:
                pass
        else:
            try:
                await message.bot.send_message(
                    referrer_id,
                    f"👏 Sizning havolangiz orqali yangi foydalanuvchi qo'shildi!\nJami takliflar: {new_count} ta.\nKeyingi mukofotgacha: {10 - (new_count % 10)} ta qoldi."
                )
            except Exception:
                pass
    
    # Mandatory Subscription Check
    MANDATORY_CHANNEL = get_setting("mandatory_channel", "@talaba_uz")
    
    try:
        if not await is_subscribed(message.bot, message.from_user.id, MANDATORY_CHANNEL):
            builder = InlineKeyboardBuilder()
            builder.button(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{MANDATORY_CHANNEL.replace('@', '')}")
            builder.button(text="✅ Tekshirish", callback_data="check_sub")
            builder.adjust(1)
            
            return await message.answer(
                "⚠️ <b>Diqqat!</b>\n\nBotdan foydalanish uchun rasmiy kanalimizga a'zo bo'lishingiz shart. "
                "Kanalga a'zo bo'lib, 'Tekshirish' tugmasini bosing:",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    except PermissionError:
        return await message.answer(
            "❌ <b>Xatolik!</b>\n\nBot kanal a'zolarini tekshira olmayapti. "
            "Iltimos, botni kanalga <b>Administrator</b> qilib tayinlang!",
            parse_mode="HTML"
        )

    is_prem = is_premium(message.from_user.id)
    premium_status = "💎 Premium" if is_prem else "🆓 Bepul"
    
    welcome_text = f"Assalomu alaykum, {html.quote(message.from_user.full_name)}!\n\n"
    welcome_text += f"Status: <b>{premium_status}</b>\n"
    
    if is_new_user:
        welcome_text += "🎉 <b>Xushxabar!</b> Sizga barcha Premium funksiyalardan foydalanish uchun <b>2 kunlik bepul sinov muddati</b> berildi!\n\n"
    
    welcome_text += "Talaba Service ilovasiga xush kelibsiz. Ilovani ochish uchun quyidagi tugmani bosing:"

    await message.answer(
        welcome_text,
        reply_markup=get_webapp_keyboard(message.from_user.id),
        parse_mode="HTML"
    )

@router.callback_query(StateFilter("*"), F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    MANDATORY_CHANNEL = get_setting("mandatory_channel", "@talaba_uz")
    try:
        subscribed = await is_subscribed(callback.bot, callback.from_user.id, MANDATORY_CHANNEL)
        if subscribed:
            await callback.answer("✅ Rahmat! Endi ilovadan foydalanishingiz mumkin.", show_alert=True)
            await callback.message.delete()
            
            premium_status = "💎 Premium" if is_premium(callback.from_user.id) else "🆓 Bepul"
            await callback.message.answer(
                f"Assalomu alaykum, {html.quote(callback.from_user.full_name)}!\n\n"
                f"Status: <b>{premium_status}</b>\n\n"
                "Ilovani ochish uchun quyidagi tugmani bosing:",
                reply_markup=get_webapp_keyboard(callback.from_user.id),
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
    except PermissionError:
        await callback.message.answer(
            "❌ <b>Xatolik!</b>\n\nBot kanal a'zolarini tekshira olmayapti. "
            "Iltimos, botni kanalga <b>Administrator</b> qilib tayinlang!",
            parse_mode="HTML"
        )
        await callback.answer()

@router.message(StateFilter("*"), Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("Bot ishlamoqda! ✅ (Web App Mode)")
