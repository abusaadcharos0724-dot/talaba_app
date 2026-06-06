from aiogram import types, Router, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

def get_grants_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🌍 Xalqaro grantlar"))
    builder.row(types.KeyboardButton(text="🇺🇿 Davlat stipendiyalari"))
    builder.row(types.KeyboardButton(text="📄 Hujjatlar namunalari"))
    builder.row(types.KeyboardButton(text="🔙 Asosiy menyuga qaytish"))
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "🏆 Grantlar")
async def grants_main(message: types.Message):
    await message.answer(
        "🏆 **Grantlar va Stipendiyalar bo'limi**\n\n"
        "Bu yerda siz o'zingizga mos grantlarni topishingiz va hujjat topshirish bo'yicha namunalar bilan tanishishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_grants_menu(),
        parse_mode="Markdown"
    )

@router.message(F.text == "🌍 Xalqaro grantlar")
async def international_grants(message: types.Message):
    text = (
        "🌍 **Mashhur Xalqaro Grantlar:**\n\n"
        "1. **Chevening (Buyuk Britaniya)**\n"
        "Magistratura uchun to'liq grant. Kontrakt, yashash va samolyot biletlarini qoplaydi.\n"
        "🔗 [Batafsil](https://www.chevening.org/)\n\n"
        "2. **Fullbright (AQSH)**\n"
        "Magistratura va tadqiqotchilar uchun eng nufuzli grantlardan biri.\n"
        "🔗 [Batafsil](https://uz.usembassy.gov/education-culture/exchange-programs/)\n\n"
        "3. **DAAD (Germaniya)**\n"
        "Germaniyada o'qish va tadqiqot olib borish uchun juda ko'p turdagi grantlar.\n"
        "🔗 [Batafsil](https://www.daad.de/en/)\n\n"
        "4. **Stipendium Hungaricum (Vengriya)**\n"
        "Bakalavr, magistratura va doktorantura uchun to'liq grant.\n"
        "🔗 [Batafsil](https://stipendiumhungaricum.hu/)\n\n"
        "5. **GKS (Janubiy Koreya)**\n"
        "Koreya hukumatining to'liq granti.\n"
        "🔗 [Batafsil](https://www.studyinkorea.go.kr/)\n"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

@router.message(F.text == "🇺🇿 Davlat stipendiyalari")
async def national_grants(message: types.Message):
    text = (
        "🇺🇿 **O'zbekiston Davlat Stipendiyalari:**\n\n"
        "1. **Prezident stipendiyasi**\n"
        "Barcha fanlardan a'lo baholarga o'qiydigan va ilmiy ishlari bor talabalar uchun.\n\n"
        "2. **Nomdor davlat stipendiyalari**\n"
        "- Islom Karimov (umumiy)\n"
        "- Navoiy (Gumanitar fanlar)\n"
        "- Beruniy (Aniq fanlar)\n"
        "- Ibn Sino (Tibbiyot)\n"
        "- Ulug'bek (Informatika va texnologiyalar)\n\n"
        "3. **El-yurt umidi jamg'armasi**\n"
        "Xorijdagi nufuzli universitetlarda o'qish xarajatlarini qoplab beradi.\n"
        "🔗 [Batafsil](https://eyuf.uz/)"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📄 Hujjatlar namunalari")
async def document_samples(message: types.Message):
    text = (
        "📄 **Grantlar uchun kerakli hujjatlar namunasi:**\n\n"
        "1. **Motivation Letter (Motivatsion xat)**\n"
        "Nima uchun ushbu grantga munosib ekanligingiz haqida yoziladi.\n"
        "💡 *Maslahat:* Shaxsiy yutuqlaringiz va maqsadlaringizni aniq yoritib bering.\n\n"
        "2. **Academic CV (Rezume)**\n"
        "Akademik CV oddiy ishga kirish CV'sidan farq qiladi. Unda ilmiy yutuqlar, konferensiyalar va sertifikatlarga urg'u beriladi.\n\n"
        "3. **Recommendation Letter (Tavsiyanoma)**\n"
        "O'qituvchingiz yoki ish beruvchingizdan olinadigan tavsifnoma."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🔙 Asosiy menuga qaytish")
async def back_to_main(message: types.Message):
    from handlers.common import get_main_menu
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id))
