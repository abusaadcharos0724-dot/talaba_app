import os
import datetime
import json
import logging
import shutil
import httpx
from typing import Optional, List
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram import Bot

# Import bot configurations and database functions
from config import BOT_TOKEN, ADMIN_ID, TEMP_DIR, PREMIUM_PRICE, HUMO_CARD
from database import (
    init_db, get_user, is_premium, set_premium, revoke_premium,
    add_deadline, get_user_deadlines, delete_deadline,
    get_book_categories, get_books_by_category, get_book_by_id, add_book, delete_book_by_id,
    get_all_channels, add_channel, delete_channel,
    get_template_categories, get_templates_by_category, add_template, delete_template, get_template_by_id, get_all_templates,
    get_setting, set_setting, get_detailed_stats, get_source_stats, get_all_tg_ids, get_all_users,
    get_pending_payments, update_payment_status, ensure_user, add_payment
)

# Import AI services
from services.ai_service import (
    ai_generate_referat, ai_generate_ppt_content, ai_solve_homework,
    ai_check_essay, ai_chat_tutor, ai_generate_flashcards
)
from utils.docx_gen import create_referat_docx
from utils.pptx_gen import create_presentation_pptx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs("data/templates", exist_ok=True)

app = FastAPI(title="Talaba Bot Web Panel")

# Mount static files
os.makedirs("static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Helper to remove files after streaming
def cleanup_file(path: str):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logger.error(f"Error removing temp file {path}: {e}")

# Helper to upload file to Telegram using HTTP client
async def upload_document_to_telegram(file_bytes: bytes, filename: str) -> str:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    async with httpx.AsyncClient() as client:
        files = {"document": (filename, file_bytes)}
        data = {"chat_id": ADMIN_ID}
        r = await client.post(url, files=files, data=data)
        if r.status_code == 200:
            res = r.json()
            if res.get("ok"):
                return res["result"]["document"]["file_id"]
    raise Exception("Telegram API upload failed")

# ================= AUTHENTICATION HELPERS =================

def get_admin_password():
    return get_setting("web_admin_password", os.getenv("WEB_ADMIN_PASSWORD", "admin123"))

def is_admin_logged_in(request: Request) -> bool:
    # Check cookie
    admin_session = request.cookies.get("admin_session")
    if admin_session == get_admin_password():
        return True
    
    # Check query param (for Telegram Web App admin bypass)
    tg_id = request.query_params.get("tg_id")
    if tg_id and tg_id.isdigit() and int(tg_id) == ADMIN_ID:
        return True
        
    return False

# ================= WEB APP ROUTERS =================

@app.get("/", response_class=HTMLResponse)
async def serve_webapp(request: Request, tg_id: Optional[str] = None):
    # Determine User ID
    user_id = 999999999  # Fallback Demo User ID
    if tg_id and tg_id.isdigit():
        user_id = int(tg_id)
    else:
        # Check cookie
        cookie_tg = request.cookies.get("tg_id")
        if cookie_tg and cookie_tg.isdigit():
            user_id = int(cookie_tg)
            
    # Ensure user is registered in DB
    ensure_user(
        tg_id=user_id,
        referrer_id=None,
        source="web",
        full_name="Web Foydalanuvchi" if user_id == 999999999 else f"Foydalanuvchi {user_id}",
        username="web_user"
    )
    
    # If the user is the Admin, they can view the Admin dashboard directly if they navigate to /admin.
    # Otherwise, load the main app.
    response = templates.TemplateResponse(request, "app.html", {
        "user_id": user_id,
        "is_prem": is_premium(user_id)
    })
    
    # Set cookie for persistence
    response.set_cookie("tg_id", str(user_id), max_age=30*24*3600)
    return response

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = None):
    if is_admin_logged_in(request):
        return RedirectResponse(url="/admin")
    return templates.TemplateResponse(request, "login.html", {"error": error})

@app.post("/admin/login")
async def admin_login(request: Request, password: str = Form(...)):
    if password == get_admin_password():
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie("admin_session", password, max_age=24*3600)
        return response
    return RedirectResponse(url="/admin/login?error=Noto'g'ri+kod", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin_dashboard(request: Request):
    if not is_admin_logged_in(request):
        return RedirectResponse(url="/admin/login")
        
    stats = get_detailed_stats()
    sources = get_source_stats()
    
    return templates.TemplateResponse(request, "admin.html", {
        "stats": stats,
        "sources": sources,
        "admin_contact": get_setting("admin_contact", "@Abusaadl7"),
        "mandatory_channel": get_setting("mandatory_channel", "@talaba_uz"),
        "premium_price": get_setting("premium_price", str(PREMIUM_PRICE)),
        "humo_card": get_setting("humo_card", HUMO_CARD),
        "webapp_url": get_setting("webapp_url", "http://127.0.0.1:8000/")
    })

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login")
    response.delete_cookie("admin_session")
    return response

# ================= STUDENT API ENDPOINTS =================

@app.get("/api/user-info")
async def api_user_info(tg_id: int):
    user_data = get_user(tg_id)
    if not user_data:
        return {"error": "User not found"}
        
    prem = is_premium(tg_id)
    status_str = "💎 Premium" if prem else "🆓 Bepul"
    expiry = user_data[2] if user_data[2] else "Faol emas"
    
    # Format expiry prettily if active
    if prem and expiry != "Faol emas":
        try:
            dt = datetime.datetime.fromisoformat(expiry)
            expiry = dt.strftime("%d.%m.%Y %H:%M")
        except:
            pass
            
    referrals = get_setting(f"referrals_{tg_id}", "0") # Fallback to settings check or custom query
    # Get actual referral count from SQLite users table
    from database import get_referral_stats
    ref_count = get_referral_stats(tg_id)
    
    bot_info = "Coddyuzbot"
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        bot_info = me.username
        await bot.session.close()
    except:
        pass
        
    referral_link = f"https://t.me/{bot_info}?start={tg_id}"
    
    return {
        "tg_id": tg_id,
        "status": status_str,
        "is_premium": prem,
        "expiry": expiry,
        "referral_count": ref_count,
        "referral_link": referral_link,
        "price": get_setting("premium_price", str(PREMIUM_PRICE)),
        "card": get_setting("humo_card", HUMO_CARD)
    }

@app.post("/api/referat")
async def api_generate_referat_endpoint(background_tasks: BackgroundTasks, tg_id: int = Form(...), topic: str = Form(...)):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="Faqat premium foydalanuvchilar referat yarata oladilar.")
        
    content = await ai_generate_referat(topic)
    safe_topic = "".join([c for c in topic if c.isalnum() or c==' ']).strip()[:30]
    filename = f"referat_{tg_id}_{safe_topic}.docx"
    filepath = os.path.join(TEMP_DIR, filename)
    
    create_referat_docx(topic, content, filepath)
    
    background_tasks.add_task(cleanup_file, filepath)
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=filename)

@app.post("/api/presentation")
async def api_generate_presentation_endpoint(background_tasks: BackgroundTasks, tg_id: int = Form(...), topic: str = Form(...), template_id: str = Form("default")):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="Faqat premium foydalanuvchilar prezentatsiya yarata oladilar.")
        
    content = await ai_generate_ppt_content(topic)
    
    template_path = None
    if template_id != "default" and template_id.isdigit():
        res = get_template_by_id(int(template_id))
        if res:
            template_path = res[1]
            
    filename = f"prezentatsiya_{tg_id}.pptx"
    filepath = os.path.join(TEMP_DIR, filename)
    
    create_presentation_pptx(topic, content, filepath, template_path)
    
    background_tasks.add_task(cleanup_file, filepath)
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=filename)

@app.post("/api/homework")
async def api_solve_homework_endpoint(background_tasks: BackgroundTasks, tg_id: int = Form(...), file: UploadFile = File(...)):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="Vazifa yechuvchi faqat premium foydalanuvchilar uchun.")
        
    temp_path = os.path.join(TEMP_DIR, f"hw_{tg_id}_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        solution = await ai_solve_homework(temp_path)
    except Exception as e:
        solution = f"Yechishda xatolik yuz berdi: {e}"
    finally:
        background_tasks.add_task(cleanup_file, temp_path)
        
    return {"solution": solution}

@app.post("/api/essay")
async def api_check_essay_endpoint(tg_id: int = Form(...), essay_text: str = Form(...)):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="Insho tekshiruvchi faqat premium foydalanuvchilar uchun.")
        
    result = await ai_check_essay(essay_text)
    return {"analysis": result}

@app.post("/api/tutor")
async def api_tutor_endpoint(tg_id: int = Form(...), message: str = Form(...), history: str = Form("[]")):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="AI Tutor faqat premium foydalanuvchilar uchun.")
        
    try:
        chat_history = json.loads(history)
    except:
        chat_history = []
        
    response = await ai_chat_tutor(message, chat_history)
    return {"response": response}

@app.post("/api/flashcards")
async def api_flashcards_endpoint(tg_id: int = Form(...), topic: str = Form(...)):
    if not is_premium(tg_id):
        raise HTTPException(status_code=403, detail="Flashcard yaratish faqat premium foydalanuvchilar uchun.")
        
    cards = await ai_generate_flashcards(topic)
    return {"flashcards": cards}

@app.get("/api/deadlines")
async def api_get_deadlines(tg_id: int):
    rows = get_user_deadlines(tg_id)
    res = []
    for rid, title, due in rows:
        try:
            dt = datetime.datetime.fromisoformat(due)
            due_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            due_str = due
        res.append({"id": rid, "title": title, "due_date": due_str})
    return res

@app.post("/api/deadlines")
async def api_add_deadline(tg_id: int = Form(...), title: str = Form(...), due_date: str = Form(...)):
    try:
        # Expect DD.MM.YYYY HH:MM
        due_dt = datetime.datetime.strptime(due_date, "%d.%m.%Y %H:%M")
    except Exception as e:
        # Fallback to simple ISO parser
        try:
            due_dt = datetime.datetime.fromisoformat(due_date)
        except:
            return JSONResponse(status_code=400, content={"error": "Sana formati noto'g'ri. Masalan: 30.12.2025 18:00"})
            
    add_deadline(tg_id, title, due_dt.isoformat())
    return {"success": True}

@app.delete("/api/deadlines/{deadline_id}")
async def api_delete_deadline(deadline_id: int):
    delete_deadline(deadline_id)
    return {"success": True}

@app.get("/api/library")
async def api_get_library():
    categories = get_book_categories()
    res = {}
    for cat in categories:
        books = get_books_by_category(cat)
        res[cat] = [{"id": r[0], "title": r[1]} for r in books]
    return res

@app.get("/api/library/download/{book_id}")
async def api_download_book(book_id: int, background_tasks: BackgroundTasks):
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Kitob topilmadi.")
        
    title, file_id, category, book_type = book
    
    bot = Bot(token=BOT_TOKEN)
    try:
        tg_file = await bot.get_file(file_id)
        temp_path = os.path.join(TEMP_DIR, f"book_{book_id}.{book_type}")
        await bot.download_file(tg_file.file_path, destination=temp_path)
        
        background_tasks.add_task(cleanup_file, temp_path)
        
        # Clean title for filename
        clean_title = "".join([c for c in title if c.isalnum() or c in [' ', '_', '-']]).strip()
        return FileResponse(temp_path, media_type="application/octet-stream", filename=f"{clean_title}.{book_type}")
    except Exception as e:
        logger.error(f"Download book error: {e}")
        raise HTTPException(status_code=500, detail="Telegramdan kitobni yuklab olishda xatolik.")
    finally:
        await bot.session.close()

@app.post("/api/pay-proof")
async def api_submit_payment_proof(tg_id: int = Form(...), proof: UploadFile = File(...)):
    # Save receipt to temp
    filename = f"proof_{tg_id}_{proof.filename}"
    filepath = os.path.join(TEMP_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(proof.file, buffer)
        
    bot = Bot(token=BOT_TOKEN)
    try:
        # Upload receipt to Telegram
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        file_id = await upload_document_to_telegram(file_bytes, filename)
        
        # Add payment to SQLite db
        price = int(get_setting("premium_price", str(PREMIUM_PRICE)))
        card = get_setting("humo_card", HUMO_CARD)
        add_payment(tg_id, price, card, file_id)
        
        # Notify Admin on Telegram
        admin_contact = get_setting("admin_contact", "@Abusaadl7")
        admin_text = (
            f"🚀 <b>Yangi to'lov isboti!</b> (Web App)\n\n"
            f"👤 Foydalanuvchi ID: <code>{tg_id}</code>\n"
            f"💰 Summa: {price} so'm\n"
            f"💳 Karta: {card}\n\n"
            f"Tekshirish va tasdiqlash uchun Web Admin Panelga o'ting."
        )
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
            await bot.send_document(ADMIN_ID, file_id, caption="To'lov cheki")
        except:
            pass
            
    except Exception as e:
        logger.error(f"Payment proof upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Fayl yuklashda xatolik: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        await bot.session.close()
        
    return {"success": True}

# ================= ADMIN API ENDPOINTS =================

@app.get("/api/admin/users")
async def api_admin_users(request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    users = get_all_users()
    res = []
    now = get_now()
    for u in users:
        tg_id, is_prem, until, created, full_name, username = u
        status = "FREE"
        if is_prem and until:
            try:
                until_dt = datetime.datetime.fromisoformat(until)
                if until_dt > now:
                    status = f"PREMIUM ({until_dt.strftime('%d.%m.%Y')})"
                else:
                    status = "EXPIRED"
            except:
                status = "PREMIUM"
                
        res.append({
            "tg_id": tg_id,
            "full_name": full_name or f"User {tg_id}",
            "username": username or "",
            "status": status,
            "created": created[:16] if created else ""
        })
    return res

@app.post("/api/admin/give-premium")
async def api_admin_give_premium(request: Request, tg_id: int = Form(...), days: int = Form(30)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    set_premium(tg_id, days)
    
    # Try to notify user
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(tg_id, f"🎉 <b>Tabriklaymiz!</b>\n\nAdmin sizga <b>{days} kunlik Premium</b> taqdim etdi! Barcha premium imkoniyatlardan foydalanishingiz mumkin.", parse_mode="HTML")
    except:
        pass
    finally:
        await bot.session.close()
        
    return {"success": True}

@app.post("/api/admin/revoke-premium")
async def api_admin_revoke_premium(request: Request, tg_id: int = Form(...)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    revoke_premium(tg_id)
    return {"success": True}

@app.get("/api/admin/payments")
async def api_admin_get_payments(request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    rows = get_pending_payments()
    res = []
    for pid, tg, amt, card, proof, created in rows:
        res.append({
            "id": pid,
            "tg_id": tg,
            "amount": amt,
            "card": card,
            "proof_file_id": proof,
            "created": created[:16] if created else ""
        })
    return res

@app.get("/api/admin/payments/view-proof/{file_id}")
async def api_admin_view_payment_proof(file_id: str, background_tasks: BackgroundTasks):
    bot = Bot(token=BOT_TOKEN)
    try:
        tg_file = await bot.get_file(file_id)
        temp_path = os.path.join(TEMP_DIR, f"proof_{file_id}.jpg")
        await bot.download_file(tg_file.file_path, destination=temp_path)
        background_tasks.add_task(cleanup_file, temp_path)
        return FileResponse(temp_path, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Error fetching payment proof: {e}")
        raise HTTPException(status_code=500, detail="Faylni Telegramdan yuklashda xatolik.")
    finally:
        await bot.session.close()

@app.post("/api/admin/approve-payment/{pid}")
async def api_admin_approve_payment(pid: int, request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    # Get payment to get user ID
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM payments WHERE id=?", (pid,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")
        
    tg_id = row[0]
    update_payment_status(pid, "approved")
    set_premium(tg_id)
    
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(tg_id, "🎉 <b>To'lovingiz tasdiqlandi!</b>\n\nPremium statusi muvaffaqiyatli faollashtirildi. Ilovani ochib barcha Premium funksiyalardan foydalanishingiz mumkin!", parse_mode="HTML")
    except:
        pass
    finally:
        await bot.session.close()
        
    return {"success": True}

@app.post("/api/admin/reject-payment/{pid}")
async def api_admin_reject_payment(pid: int, request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    # Get payment to get user ID
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM payments WHERE id=?", (pid,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")
        
    tg_id = row[0]
    update_payment_status(pid, "rejected")
    
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(tg_id, "❌ <b>Siz yuborgan to'lov cheki rad etildi.</b>\n\nAgar bu xatolik bo'lsa, iltimos admin bilan bog'laning.", parse_mode="HTML")
    except:
        pass
    finally:
        await bot.session.close()
        
    return {"success": True}

@app.get("/api/admin/templates")
async def api_admin_templates(request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    rows = get_all_templates()
    return [{"id": r[0], "name": r[1], "category": r[2]} for r in rows]

@app.post("/api/admin/add-template")
async def api_admin_add_template(request: Request, name: str = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    import time
    filename = f"template_{int(time.time())}.pptx"
    destination = os.path.join("data/templates", filename)
    
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    add_template(name, category, destination)
    return {"success": True}

@app.delete("/api/admin/templates/{tid}")
async def api_admin_delete_template(tid: int, request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    delete_template(tid)
    return {"success": True}

@app.get("/api/admin/channels")
async def api_admin_channels(request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    channels = get_all_channels()
    return [{"id": r[0], "title": r[1], "url": r[2]} for r in channels]

@app.post("/api/admin/add-channel")
async def api_admin_add_channel(request: Request, title: str = Form(...), url: str = Form(...)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    add_channel(title, url)
    return {"success": True}

@app.delete("/api/admin/channels/{cid}")
async def api_admin_delete_channel(cid: int, request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    delete_channel(cid)
    return {"success": True}

@app.post("/api/admin/add-book")
async def api_admin_add_book(request: Request, title: str = Form(...), category: str = Form(...), btype: str = Form("pdf"), file: UploadFile = File(...)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    # Save upload to temp
    temp_path = os.path.join(TEMP_DIR, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Upload book file to Telegram and retrieve file_id
        with open(temp_path, "rb") as f:
            file_bytes = f.read()
        file_id = await upload_document_to_telegram(file_bytes, file.filename)
        
        # Save to database
        add_book(title, category, file_id, btype)
    except Exception as e:
        logger.error(f"Error adding book: {e}")
        raise HTTPException(status_code=500, detail=f"Kitobni qo'shishda xatolik yuz berdi: {e}")
    finally:
        cleanup_file(temp_path)
        
    return {"success": True}

@app.delete("/api/admin/books/{bid}")
async def api_admin_delete_book(bid: int, request: Request):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    delete_book_by_id(bid)
    return {"success": True}

@app.post("/api/admin/settings")
async def api_admin_save_settings(
    request: Request,
    price: str = Form(...),
    card: str = Form(...),
    contact: str = Form(...),
    channel: str = Form(...),
    webapp_url: str = Form(...),
    admin_password: str = Form(...)
):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    set_setting("premium_price", price)
    set_setting("humo_card", card)
    set_setting("admin_contact", contact)
    set_setting("mandatory_channel", channel)
    set_setting("webapp_url", webapp_url)
    
    if admin_password.strip():
        set_setting("web_admin_password", admin_password.strip())
        
    return {"success": True}

# Background worker for broadcast
async def run_broadcast_job(text: str, pin: bool = False):
    ids = get_all_tg_ids()
    bot = Bot(token=BOT_TOKEN)
    logger.info(f"Starting broadcast to {len(ids)} users.")
    count = 0
    for tid in ids:
        try:
            msg = await bot.send_message(tid, text, parse_mode="HTML")
            if pin:
                await bot.pin_chat_message(tid, msg.message_id)
            count += 1
            await asyncio.sleep(0.05) # anti-flood delay
        except Exception as e:
            logger.debug(f"Broadcast failed for {tid}: {e}")
            
    logger.info(f"Broadcast completed. Successfully sent to {count}/{len(ids)} users.")
    await bot.session.close()

@app.post("/api/admin/broadcast")
async def api_admin_broadcast(request: Request, background_tasks: BackgroundTasks, text: str = Form(...), pin: bool = Form(False)):
    if not is_admin_logged_in(request):
        raise HTTPException(status_code=401, detail="Ruxsat berilmagan.")
        
    background_tasks.add_task(run_broadcast_job, text, pin)
    return {"success": True, "message": "Xabar yuborish fonda ishga tushirildi."}
