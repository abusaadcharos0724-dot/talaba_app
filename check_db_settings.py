from database import get_setting
import sqlite3
from config import DB_PATH

def check():
    print("Checking settings...")
    try:
        admin_contact = get_setting("admin_contact")
        mandatory_channel = get_setting("mandatory_channel")
        print(f"Admin Contact: {admin_contact}")
        print(f"Mandatory Channel: {mandatory_channel}")
    except Exception as e:
        print(f"Error reading settings: {e}")

    print("\nFull Settings table:")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        rows = c.fetchall()
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error reading full table: {e}")

if __name__ == "__main__":
    check()
