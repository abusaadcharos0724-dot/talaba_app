import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db, get_due_deadlines, mark_reminded, get_now
from handlers import common

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reminders_loop(bot: Bot):
    while True:
        try:
            now = get_now()
            rows = get_due_deadlines()
            for did, tg, title, due_iso, r24, r1 in rows:
                try:
                    due_dt = datetime.datetime.fromisoformat(due_iso)
                except Exception:
                    continue
                
                sec = (due_dt - now).total_seconds()
                
                # 24 hour reminder
                if 0 < sec <= 24*3600 and r24 == 0:
                    try:
                        await bot.send_message(tg, f"⏰ **Eslatma (24 soat qoldi):**\n'{title}' muddati: {due_dt.strftime('%Y-%m-%d %H:%M')}", parse_mode="Markdown")
                        mark_reminded(did, "24")
                    except Exception as e:
                        logger.warning(f"Reminder error (24h) for {tg}: {e}")
                
                # 1 hour reminder
                if 0 < sec <= 3600 and r1 == 0:
                    try:
                        await bot.send_message(tg, f"⏰ **Eslatma (1 soat qoldi!):**\n'{title}' muddati: {due_dt.strftime('%Y-%m-%d %H:%M')}", parse_mode="Markdown")
                        mark_reminded(did, "1")
                    except Exception as e:
                        logger.warning(f"Reminder error (1h) for {tg}: {e}")
            
            await asyncio.sleep(60) # Check every minute
        except Exception as e:
            logger.error(f"Reminders loop error: {e}")
            await asyncio.sleep(60)

async def main():
    init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Include simplified routers
    dp.include_router(common.router)
    
    # Start reminders
    asyncio.create_task(reminders_loop(bot))
    
    logger.info("Talaba Bot (Web App Gateway) ishga tushirildi.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
