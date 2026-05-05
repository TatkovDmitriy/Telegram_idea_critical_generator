import subprocess
import time
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LAUNCHER] %(message)s",
    datefmt="%H:%M:%S",
)

BOT_SCRIPT = Path(__file__).parent / "bot.py"
PYTHON = sys.executable
RESTART_DELAY = 10


def run():
    attempt = 0
    while True:
        attempt += 1
        logging.info(f"Запуск бота (попытка #{attempt})...")
        try:
            result = subprocess.run([PYTHON, str(BOT_SCRIPT)])
            exit_code = result.returncode
        except KeyboardInterrupt:
            logging.info("Остановлено вручную.")
            break
        except Exception as e:
            logging.error(f"Ошибка запуска: {e}")
            exit_code = -1

        if exit_code == 0:
            logging.info("Бот завершился штатно. Остановка лаунчера.")
            break

        logging.warning(f"Бот упал с кодом {exit_code}. Перезапуск через {RESTART_DELAY} сек...")
        time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    run()
