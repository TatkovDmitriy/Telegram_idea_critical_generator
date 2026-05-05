import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN
from bot_handlers import register_handlers

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
