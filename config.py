import os
from dotenv import load_dotenv

# Force override existing environment variables
load_dotenv(override=True)

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ID
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Gemini API Key (BEPUL!)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Payment Details
HUMO_CARD = os.getenv("HUMO_CARD", "9860 1201 1367 9696")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", 25000))
DEFAULT_PREMIUM_DAYS = 30

# Timezone
TIMEZONE = "Asia/Tashkent"

# Database
DB_PATH = "talaba_superbot.db"

# Folders
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
