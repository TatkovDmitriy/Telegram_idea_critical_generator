import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "TatkovDmitriy/Obsidian")
OBSIDIAN_IDEAS_PATH = os.getenv("OBSIDIAN_IDEAS_PATH", "Lemana_Pro_Project/Lemana_Pro_Project/99_Ideas")

WHISPER_MODEL = "whisper-large-v3-turbo"
LLAMA_MODEL = "llama-3.3-70b-versatile"
