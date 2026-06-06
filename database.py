import sqlite3
import datetime
from typing import Optional, List
from config import DB_PATH, DEFAULT_PREMIUM_DAYS, TIMEZONE
import pytz

def get_now():
    tz = pytz.timezone(TIMEZONE)
    return datetime.datetime.now(tz)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # Settings table
    c.execute("""CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        tg_id INTEGER PRIMARY KEY,
        full_name TEXT,
        username TEXT,
        is_premium INTEGER DEFAULT 0,
        premium_until TEXT,
        referrer_id INTEGER,
        referral_count INTEGER DEFAULT 0,
        source TEXT,
        created TEXT
    )""")
    
    # Migrations for existing users table
    columns = [
        ("full_name", "TEXT"),
        ("username", "TEXT"),
        ("is_premium", "INTEGER DEFAULT 0"),
        ("premium_until", "TEXT"),
        ("referrer_id", "INTEGER"),
        ("referral_count", "INTEGER DEFAULT 0"),
        ("source", "TEXT"),
        ("created", "TEXT")
    ]
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    c.execute("""CREATE TABLE IF NOT EXISTS deadlines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        title TEXT,
        due_date TEXT,
        reminded_24 INTEGER DEFAULT 0,
        reminded_1 INTEGER DEFAULT 0
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        amount INTEGER,
        card TEXT,
        proof_file_id TEXT,
        status TEXT DEFAULT 'pending',
        created TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS tests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        topic TEXT,
        questions TEXT,
        created TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS schedules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        day_of_week TEXT,
        subject TEXT,
        start_time TEXT,
        location TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        file_id TEXT,
        book_type TEXT DEFAULT 'pdf',
        created TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS channels(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        created TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS templates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        file_path TEXT,
        created TEXT
    )""")
    
    # Migration for templates table
    try:
        c.execute("ALTER TABLE templates ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Insert default settings if not exists
    c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('admin_contact', '@Abusaadl7')")
    c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('mandatory_channel', '@talaba_uz')")
    
    conn.commit()
    conn.close()


def ensure_user(tg_id: int, referrer_id: int = None, source: str = None, full_name: str = None, username: str = None) -> bool:
    """Returns True if new user created, False otherwise"""
    conn = get_conn()
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT tg_id FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    
    if row is None:
        # New user: Grant 2 days of free premium
        now = get_now()
        trial_until = now + datetime.timedelta(days=2)
        c.execute("INSERT INTO users(tg_id, is_premium, premium_until, referrer_id, referral_count, created, source, full_name, username) VALUES(?,1,?,?,0,?,?,?,?)", 
                  (tg_id, trial_until.isoformat(), referrer_id, now.isoformat(), source, full_name, username))
        conn.commit()
        conn.close()
        return True
    else:
        # Update details for existing user
        c.execute("UPDATE users SET full_name=?, username=? WHERE tg_id=?", (full_name, username, tg_id))
        conn.commit()
    
    conn.close()
    return False


def increment_referral(referrer_id: int) -> int:
    """Increment referral count and return new total"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET referral_count = COALESCE(referral_count, 0) + 1 WHERE tg_id=?", (referrer_id,))
    conn.commit()
    
    c.execute("SELECT referral_count FROM users WHERE tg_id=?", (referrer_id,))
    row = c.fetchone()
    count = row[0] if row else 0
    conn.close()
    return count

def get_referral_stats(tg_id: int) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT referral_count FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id, is_premium, premium_until, created, full_name, username FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user(tg_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id, is_premium, premium_until FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    conn.close()
    return row

def is_premium(tg_id: int) -> bool:
    user = get_user(tg_id)
    if not user: return False
    prem, until = user[1], user[2]
    if prem and until:
        try:
            return datetime.datetime.fromisoformat(until) > get_now()
        except:
            return False
    return False

def set_premium(tg_id: int, days: int = DEFAULT_PREMIUM_DAYS):
    conn = get_conn()
    c = conn.cursor()
    now = get_now()
    c.execute("SELECT premium_until FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    if row and row[0]:
        try:
            cur = datetime.datetime.fromisoformat(row[0])
        except:
            cur = now
        new_until = (cur if cur > now else now) + datetime.timedelta(days=days)
    else:
        new_until = now + datetime.timedelta(days=days)
    
    c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE tg_id=?", (new_until.isoformat(), tg_id))
    conn.commit()
    conn.close()

def revoke_premium(tg_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=0, premium_until=? WHERE tg_id=?", (get_now().isoformat(), tg_id))
    conn.commit()
    conn.close()

def add_deadline(tg_id: int, title: str, due_iso: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO deadlines(tg_id, title, due_date) VALUES(?,?,?)", (tg_id, title, due_iso))
    conn.commit()
    conn.close()

def get_due_deadlines():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, tg_id, title, due_date, reminded_24, reminded_1 FROM deadlines")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_reminded(did: int, which: str):
    conn = get_conn()
    c = conn.cursor()
    if which == "24":
        c.execute("UPDATE deadlines SET reminded_24=1 WHERE id=?", (did,))
    elif which == "1":
        c.execute("UPDATE deadlines SET reminded_1=1 WHERE id=?", (did,))
    conn.commit()
    conn.close()

def add_payment(tg_id: int, amount: int, card: str, proof_file_id: Optional[str]):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO payments(tg_id, amount, card, proof_file_id, created) VALUES(?,?,?,?,?)",
              (tg_id, amount, card, proof_file_id, get_now().isoformat()))
    conn.commit()
    conn.close()

def get_pending_payments():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, tg_id, amount, card, proof_file_id, created FROM payments WHERE status='pending'")
    rows = c.fetchall()
    conn.close()
    return rows

def update_payment_status(pid: int, status: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE payments SET status=? WHERE id=?", (status, pid))
    conn.commit()
    conn.close()

def get_user_deadlines(tg_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, due_date FROM deadlines WHERE tg_id=? AND due_date > ? ORDER BY due_date ASC", 
              (tg_id, get_now().isoformat()))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_deadline(deadline_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM deadlines WHERE id=?", (deadline_id,))
    conn.commit()
    conn.close()

def add_schedule(tg_id: int, day: str, subject: str, time: str, location: str = ""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO schedules(tg_id, day_of_week, subject, start_time, location) VALUES(?,?,?,?,?)",
              (tg_id, day, subject, time, location))
    conn.commit()
    conn.close()

def get_schedule(tg_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT day_of_week, subject, start_time, location FROM schedules WHERE tg_id=? ORDER BY day_of_week, start_time", (tg_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_schedule(tg_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE tg_id=?", (tg_id,))
    conn.commit()
    conn.close()

def add_book(title: str, category: str, file_id: str, book_type: str = 'pdf'):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO books(title, category, file_id, book_type, created) VALUES(?,?,?,?,?)",
              (title, category, file_id, book_type, get_now().isoformat()))
    conn.commit()
    conn.close()

def get_book_categories(book_type: Optional[str] = None):
    conn = get_conn()
    c = conn.cursor()
    if book_type:
        c.execute("SELECT DISTINCT category FROM books WHERE book_type=?", (book_type,))
    else:
        c.execute("SELECT DISTINCT category FROM books")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def update_book_category(old_name: str, new_name: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE books SET category=? WHERE category=?", (new_name, old_name))
    conn.commit()
    conn.close()

def get_books_by_category(category: str, book_type: Optional[str] = None):
    conn = get_conn()
    c = conn.cursor()
    if book_type:
        c.execute("SELECT id, title, file_id FROM books WHERE category=? AND book_type=? ORDER BY id ASC", (category, book_type))
    else:
        c.execute("SELECT id, title, file_id FROM books WHERE category=? ORDER BY id ASC", (category,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_book_by_id(book_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT title, file_id, category, book_type FROM books WHERE id=?", (book_id,))
    row = c.fetchone()
    conn.close()
    return row

def delete_book_by_id(book_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

def add_channel(title: str, url: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO channels(title, url, created) VALUES(?,?,?)",
              (title, url, get_now().isoformat()))
    conn.commit()
    conn.close()

def get_all_channels():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, url FROM channels ORDER BY created DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_channel(channel_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()

def get_detailed_stats():
    conn = get_conn()
    c = conn.cursor()
    
    # Total users
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # Premium users
    c.execute("SELECT COUNT(*) FROM users WHERE is_premium=1")
    premium_users = c.fetchone()[0]
    
    # Total books
    c.execute("SELECT COUNT(*) FROM books")
    total_books = c.fetchone()[0]
    
    # Total deadlines (active)
    c.execute("SELECT COUNT(*) FROM deadlines WHERE due_date > ?", (get_now().isoformat(),))
    active_deadlines = c.fetchone()[0]
    
    # New users today
    today_start = get_now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    c.execute("SELECT COUNT(*) FROM users WHERE created >= ?", (today_start,))
    new_users_today = c.fetchone()[0]
    
    conn.close()
    return {
        "total": total_users,
        "premium": premium_users,
        "books": total_books,
        "deadlines": active_deadlines,
        "new_today": new_users_today
    }

def get_all_tg_ids():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM users")
    ids = [r[0] for r in c.fetchall()]
    conn.close()
    return ids

def add_template(name: str, category: str, file_path: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO templates(name, category, file_path, created) VALUES(?,?,?,?)",
              (name, category, file_path, get_now().isoformat()))
    conn.commit()
    conn.close()

def get_all_templates():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, category, file_path FROM templates ORDER BY created DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_template_categories():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM templates WHERE category IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]

def get_templates_by_category(category: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, file_path FROM templates WHERE category=? ORDER BY created DESC", (category,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_template(tid: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT file_path FROM templates WHERE id=?", (tid,))
    row = c.fetchone()
    if row and os.path.exists(row[0]):
        try:
            os.remove(row[0])
        except:
            pass
    c.execute("DELETE FROM templates WHERE id=?", (tid,))
    conn.commit()
    conn.close()

def get_template_by_id(tid: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, file_path FROM templates WHERE id=?", (tid,))
    row = c.fetchone()
    conn.close()
    return row

def set_setting(key: str, value: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = None):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else default
    except Exception:
        return default

def get_source_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT source, COUNT(*) FROM users WHERE source IS NOT NULL GROUP BY source")
    rows = c.fetchall()
    conn.close()
    return dict(rows)
