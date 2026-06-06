import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gemini_service import gemini_generate_ppt_content
from utils.pptx_gen import create_presentation_pptx

async def test():
    print("Gemini API orqali kontent olinmoqda...")
    topic = "Sun'iy intellekt va uning kelajagi"
    content = await gemini_generate_ppt_content(topic)
    print("Olingan kontent:")
    print("-" * 40)
    print(content)
    print("-" * 40)
    
    print("Prezentatsiya fayli yaratilmoqda...")
    output_path = "temp/test_presentation.pptx"
    os.makedirs("temp", exist_ok=True)
    
    try:
        create_presentation_pptx(topic, content, output_path)
        print(f"Muvaffaqiyatli yaratildi: {output_path}")
        print(f"Fayl hajmi: {os.path.getsize(output_path)} bayt")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(test())
