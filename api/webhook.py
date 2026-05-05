import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import logging
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import TELEGRAM_BOT_TOKEN
from services.firestore_storage import FirestoreStorage
from bot_handlers import register_handlers

logging.basicConfig(level=logging.INFO)


async def _process(data: dict):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=FirestoreStorage())
    register_handlers(dp, bot)
    try:
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            asyncio.run(_process(body))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception:
            import traceback
            err = traceback.format_exc().encode()
            logging.error(err)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(err)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

    def log_message(self, format, *args):
        pass
