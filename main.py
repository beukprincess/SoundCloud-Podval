import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import BaseFilter
import yt_dlp
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

SC_REGEX = r'(https?://(?:[a-zA-Z0-9-]+\.)?soundcloud\.com/[^\s]+)'

def download_soundcloud_track(url: str, output_dir: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_path = filename.rsplit('.', 1)[0] + '.mp3'
        return mp3_path

@dp.message()
async def handle_message(message: types.Message):
    if message.text:
        logger.info(f"Bot received message: {message.text}")
    else:
        return

    urls = re.findall(SC_REGEX, message.text)
    if not urls:
        logger.info("No SoundCloud links found, ignoring.")
        return

    url = urls[0]
    logger.info(f"URL: {url}. Sending...")
    processing_msg = await message.reply("Downloading from SoundCloud...")

    output_dir = "/app/temp_audio"
    os.makedirs(output_dir, exist_ok=True)

    try:
        file_path = await asyncio.to_thread(download_soundcloud_track, url, output_dir)
        
        logger.info(f"File downloaded: {file_path}. Sending to chat...")
        audio = FSInputFile(file_path)
        await bot.send_audio(
            chat_id=message.chat.id,
            audio=audio,
            reply_to_message_id=message.message_id
        )
        os.remove(file_path)
        logger.info("Audio sent, temporary file removed.")
        
    except Exception as e:
        logger.error(f"Error on startup: {e}")
        await message.reply(f"Error: {e}")
    finally:
        await processing_msg.delete()

async def main():
    logger.info("Bot started!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())