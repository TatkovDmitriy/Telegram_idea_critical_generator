import logging
import os
import re
import aiofiles
import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TELEGRAM_BOT_TOKEN
from services.transcription import transcribe_audio
from services.ai_service import get_challenge_response, parse_rice_block
from services.obsidian_publisher import publish_to_obsidian

TEMP_DIR = "/tmp/temp_audio" if os.path.exists("/tmp") else "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


class IdeaFlow(StatesGroup):
    collecting = State()


def register_handlers(dp: Dispatcher, bot: Bot):

    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Привет! Я помогу оценить твою идею по методике RICE.\n\n"
            "Отправь мне идею голосовым сообщением или текстом — и мы начнём."
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Сессия сброшена. Отправь новую идею когда будешь готов.")

    @dp.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Начинаем заново. Отправь свою идею.")

    @dp.message(F.voice)
    async def handle_voice(message: Message, state: FSMContext):
        await message.answer("Слушаю голосовое... транскрибирую.")
        file_path = await _download_voice(bot, message)
        try:
            text = await transcribe_audio(file_path)
            os.remove(file_path)
        except Exception as e:
            await message.answer(f"Не удалось распознать голос: {e}")
            return
        await message.answer(f"Распознал: _{text}_", parse_mode="Markdown")
        await _process_idea_input(message, state, text)

    @dp.message(F.text, ~F.text.startswith("/"))
    async def handle_text(message: Message, state: FSMContext):
        await _process_idea_input(message, state, message.text)


async def _download_voice(bot: Bot, message: Message) -> str:
    file = await bot.get_file(message.voice.file_id)
    file_path = f"{TEMP_DIR}/{message.voice.file_id}.ogg"
    url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await resp.read())
    return file_path


async def _process_idea_input(message: Message, state: FSMContext, user_text: str):
    data = await state.get_data()
    history = data.get("history", [])
    raw_idea = data.get("raw_idea", "")

    if not raw_idea:
        raw_idea = user_text

    history.append({"role": "user", "content": user_text})
    await message.answer("Анализирую...")

    try:
        response = get_challenge_response(history)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            wait_match = re.search(r"try again in ([\dh m s]+)", error_str, re.IGNORECASE)
            wait_time = wait_match.group(1).strip() if wait_match else "некоторое время"
            await message.answer(
                f"⏳ *Лимит запросов исчерпан*\n\n"
                f"Groq бесплатный тариф: 100,000 токенов в день. На сегодня лимит закончился.\n\n"
                f"Попробуй снова через: *{wait_time}*",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"⚠️ Ошибка: {e}")
        return

    history.append({"role": "assistant", "content": response})
    await state.update_data(history=history, raw_idea=raw_idea)

    rice = parse_rice_block(response)

    if rice:
        clean_response = response[:response.index("---RICE_START---")].strip()
        if clean_response:
            await message.answer(clean_response)

        await message.answer(
            f"✅ *RICE оценка готова!*\n\n"
            f"*{rice.get('НАЗВАНИЕ', '—')}*\n\n"
            f"📊 Охват: {rice.get('ОХВАТ', '—')}\n"
            f"⚡ Влияние: {rice.get('ВЛИЯНИЕ', '—')}\n"
            f"🎯 Уверенность: {rice.get('УВЕРЕННОСТЬ', '—')}\n"
            f"⏱ Затраты: {rice.get('ЗАТРАТЫ', '—')}\n\n"
            f"🏆 *RICE Score: {rice.get('RICE_SCORE', '—')}*\n\n"
            f"💡 {rice.get('ВЫВОД', '—')}\n\n"
            f"Сохраняю в Obsidian...",
            parse_mode="Markdown"
        )

        try:
            filename = publish_to_obsidian(rice, raw_idea)

            уточнения_raw = rice.get("УТОЧНЕНИЯ", "нет")
            уточнения_list = (
                [q.strip() for q in уточнения_raw.split("|") if q.strip()]
                if уточнения_raw.lower() != "нет"
                else []
            )

            saved_msg = f"📁 Сохранено в Obsidian: `{filename}`"
            if уточнения_list:
                questions_text = "\n".join(f"• {q}" for q in уточнения_list)
                saved_msg += (
                    f"\n\n❓ *Остались открытые вопросы:*\n{questions_text}"
                )
            saved_msg += "\n\nОтправь /new чтобы оценить следующую идею."
            await message.answer(saved_msg, parse_mode="Markdown")

        except Exception as e:
            await message.answer(f"⚠️ RICE посчитан, но сохранить в Obsidian не удалось: {e}")

        await state.clear()
    else:
        await message.answer(response)
