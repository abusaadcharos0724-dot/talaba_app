import os
from dotenv import load_dotenv

# Show current working directory
print(f"Current working directory: {os.getcwd()}")

# Load from explicit path
env_path = os.path.join(os.getcwd(), ".env")
print(f"Loading .env from: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")

# Read .env content
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'BOT_TOKEN' in line:
                print(f"In file: {line}")

# Load and check
load_dotenv()
token = os.getenv("BOT_TOKEN")
print(f"Loaded by python: {token}")
