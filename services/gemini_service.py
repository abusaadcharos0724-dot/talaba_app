import google.generativeai as genai
from config import GEMINI_API_KEY
import logging
import base64

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.error(f"Gemini API Init Error: {e}")

# ===== TEXT GENERATION =====

async def gemini_generate(prompt: str, system_instruction: str = None, max_tokens: int = 500):
    """Generate text using Gemini"""
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash-lite',
            system_instruction=system_instruction
        )
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini Generate Error: {e}")
        return f"Xatolik yuz berdi: {str(e)}"

# ===== CHAT (with history) =====

async def gemini_chat(user_message: str, chat_history: list = None):
    """Chat with context using Gemini"""
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash-lite',
            system_instruction="Sen professional o'qituvchisan. Talabalarga tushunarli va aniq javoblar ber. Qisqa va mazmunli bo'lsin."
        )
        
        # Start chat with history
        chat = model.start_chat(history=[])
        
        # Add history if exists
        if chat_history:
            for msg in chat_history[-10:]:  # Last 5 exchanges
                role = "user" if msg["role"] == "user" else "model"
                chat.history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
        
        # Send message
        response = chat.send_message(user_message)
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini Chat Error: {e}")
        return "Javob berishda xatolik yuz berdi. Qaytadan urinib ko'ring."

# ===== VISION (Image Analysis) =====

async def gemini_vision(image_path: str, prompt: str):
    """Analyze image using Gemini Vision"""
    try:
        # Read image
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini Vision Error: {e}")
        return f"Rasmni tahlil qilishda xatolik: {str(e)}"

# ===== SPECIFIC FUNCTIONS =====

async def gemini_summarize(text: str):
    """Summarize text"""
    prompt = f"Quyidagi matnni qisqacha konspekt qil:\n\n{text[:4000]}"
    system = "Sen o'zbek tilidagi matnlarni qisqacha va mazmunli konspekt qilib beruvchi yordamchisan."
    return await gemini_generate(prompt, system, max_tokens=500)

async def gemini_generate_referat(topic: str):
    """Generate referat"""
    prompt = f"Mavzu: {topic}"
    system = "Sen talabalarga referat yozishda yordam berasan. Matn chuqur va akademik uslubda, o'zbek tilida bo'lsin. Mavzu bo'yicha kamida 5 ta bo'limdan iborat reja va batafsil matn tayyorla."
    return await gemini_generate(prompt, system, max_tokens=3500)

async def gemini_generate_test(topic: str, count: int = 5):
    """Generate test questions"""
    prompt = f"Mavzu: {topic}"
    system = f"Berilgan mavzu bo'yicha aniq {count} ta test (MCQ) yarat. Har bir testda 4 ta variant (A, B, C, D) bo'lsin va oxirida to'g'ri javoblarni ro'yxat ko'rinishida ko'rsat. Til: O'zbekcha."
    return await gemini_generate(prompt, system, max_tokens=2000)

async def gemini_generate_ppt_content(topic: str):
    """Generate presentation content"""
    prompt = f"Mavzu: {topic}"
    system = "Sen professional prezentatsiya tayyorlovchi yordamchisan. Berilgan mavzu bo'yicha 7-10 ta slayddan iborat reja va har bir slayd uchun qisqa, mazmunli matn yozib ber. Javobni QAT'IY ravishda JSON massiv (array) formatida qaytar. Har bir slayd obyektida 'title' va 'content' maydonlari bo'lsin. Markdown belgilari (** yoki *) ishlatma. Faqat toza JSON qaytar: [{\"title\": \"...\", \"content\": \"...\"}]. Til: O'zbekcha."
    return await gemini_generate(prompt, system, max_tokens=3000)

async def gemini_solve_homework(image_path: str):
    """Solve homework from image"""
    prompt = "Bu masalani qadam-baqadam yech va tushuntir. Matematika, fizika yoki kimyo masalasi bo'lishi mumkin. O'zbek tilida javob ber."
    return await gemini_vision(image_path, prompt)

async def gemini_check_essay(essay_text: str):
    """Check essay"""
    prompt = f"Quyidagi inshoni tekshir:\n\n{essay_text[:3000]}"
    system = "Sen professional insho tekshiruvchisan. Berilgan matnni tahlil qilib:\n1. Grammatika xatolarini top\n2. Uslub va ifoda tavsiyalari ber\n3. Umumiy baho ber (5 ball)\n4. Yaxshilash yo'llarini ko'rsat\nO'zbek tilida javob ber."
    return await gemini_generate(prompt, system, max_tokens=800)

async def gemini_generate_flashcards(topic: str, count: int = 10):
    """Generate flashcards"""
    prompt = f"Mavzu: {topic}"
    system = f"Sen flashcard yaratuvchisan. Berilgan mavzu bo'yicha {count} ta flashcard yarat. Har bir flashcard:\nSAVOL: [savol]\nJAVOB: [qisqa javob]\nFormat: O'zbek tilida, aniq va qisqa."
    return await gemini_generate(prompt, system, max_tokens=1000)
