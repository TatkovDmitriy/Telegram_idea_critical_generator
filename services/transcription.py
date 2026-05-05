import os
from groq import Groq
from config import GROQ_API_KEY, WHISPER_MODEL

client = Groq(api_key=GROQ_API_KEY)


async def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), f.read()),
            model=WHISPER_MODEL,
            language="ru",
            response_format="text",
        )
    return transcription
