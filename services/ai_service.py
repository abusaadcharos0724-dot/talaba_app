"""
AI Service - Gemini API (BEPUL!)

Bu fayl Gemini API'ni ishlatadi (OpenAI o'rniga)
Afzalliklari:
- 100% BEPUL (1,500 req/kun)
- 2x tezroq
- Vision bor
- Yaxshi sifat
"""

from services.gemini_service import (
    gemini_summarize,
    gemini_generate_referat,
    gemini_generate_test,
    gemini_generate_ppt_content,
    gemini_chat,
    gemini_solve_homework,
    gemini_check_essay,
    gemini_generate_flashcards
)
import logging

logger = logging.getLogger(__name__)

# ===== BASIC FUNCTIONS =====

async def ai_summarize(text: str):
    """Summarize text using Gemini"""
    return await gemini_summarize(text)

async def ai_generate_referat(topic: str):
    """Generate referat using Gemini"""
    return await gemini_generate_referat(topic)

async def ai_generate_test(topic: str, count: int = 5):
    """Generate test using Gemini"""
    return await gemini_generate_test(topic, count)

async def ai_generate_ppt_content(topic: str):
    """Generate presentation content using Gemini"""
    return await gemini_generate_ppt_content(topic)

# ===== PREMIUM FEATURES =====

async def ai_chat_tutor(user_message: str, chat_history: list = None):
    """AI Tutor - Chat with context using Gemini"""
    return await gemini_chat(user_message, chat_history)

async def ai_solve_homework(image_path: str):
    """Homework Solver - Solve problems from image using Gemini Vision"""
    return await gemini_solve_homework(image_path)

async def ai_check_essay(essay_text: str):
    """Essay Checker using Gemini"""
    return await gemini_check_essay(essay_text)

async def ai_generate_flashcards(topic: str, count: int = 10):
    """Generate flashcards using Gemini"""
    return await gemini_generate_flashcards(topic, count)


