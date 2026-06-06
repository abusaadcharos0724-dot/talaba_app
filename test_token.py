from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN loaded: {token}")
print(f"Token length: {len(token) if token else 0}")
