from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Study resources
RESOURCES = {
    "matematika": {
        "title": "📐 Matematika",
        "resources": [
            {"name": "Khan Academy (O'zbek)", "url": "https://uz.khanacademy.org"},
            {"name": "Ziyonet", "url": "https://ziyonet.uz"},
            {"name": "YouTube - Matematika darslari", "url": "https://youtube.com/@matematikauz"},
        ]
    },
    "ingliz_tili": {
        "title": "🇬🇧 Ingliz tili",
        "resources": [
            {"name": "Duolingo", "url": "https://duolingo.com"},
            {"name": "BBC Learning English", "url": "https://bbc.co.uk/learningenglish"},
            {"name": "English Grammar", "url": "https://englishgrammar.org"},
        ]
    },
    "informatika": {
        "title": "💻 Informatika",
        "resources": [
            {"name": "W3Schools", "url": "https://w3schools.com"},
            {"name": "freeCodeCamp", "url": "https://freecodecamp.org"},
            {"name": "Codecademy", "url": "https://codecademy.com"},
        ]
    },
    "fizika": {
        "title": "⚛️ Fizika",
        "resources": [
            {"name": "Physics Classroom", "url": "https://physicsclassroom.com"},
            {"name": "Khan Academy Physics", "url": "https://khanacademy.org/science/physics"},
            {"name": "Ziyonet Fizika", "url": "https://ziyonet.uz/uz/subjects/fizika"},
        ]
    },
    "kimyo": {
        "title": "🧪 Kimyo",
        "resources": [
            {"name": "Khan Academy Chemistry", "url": "https://khanacademy.org/science/chemistry"},
            {"name": "ChemGuide", "url": "https://chemguide.co.uk"},
            {"name": "Ziyonet Kimyo", "url": "https://ziyonet.uz/uz/subjects/kimyo"},
        ]
    }
}

@router.message(F.text == "📚 Bepul manbalar")
async def show_resource_categories(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    for key, data in RESOURCES.items():
        builder.button(text=data["title"], callback_data=f"resource_{key}")
    
    builder.adjust(2)
    
    await message.answer(
        "📚 **Bepul O'quv Manbalar**\n\n"
        "Qaysi fan bo'yicha manba kerak?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("resource_"))
async def show_resources(callback: types.CallbackQuery):
    subject = callback.data.replace("resource_", "")
    data = RESOURCES.get(subject)
    
    if not data:
        await callback.answer("Manba topilmadi")
        return
    
    text = f"**{data['title']}** - Bepul Manbalar\n\n"
    
    for i, resource in enumerate(data["resources"], 1):
        text += f"{i}. [{resource['name']}]({resource['url']})\n"
    
    text += "\n💡 Barcha manbalar bepul va ochiq!"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="back_to_resources")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_resources")
async def back_to_categories(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    
    for key, data in RESOURCES.items():
        builder.button(text=data["title"], callback_data=f"resource_{key}")
    
    builder.adjust(2)
    
    await callback.message.edit_text(
        "📚 **Bepul O'quv Manbalar**\n\n"
        "Qaysi fan bo'yicha manba kerak?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
