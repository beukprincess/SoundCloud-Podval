from dotenv import load_dotenv
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import BaseFilter
import yt_dlp
#
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

SC_REGEX = r'(https?://(?:www\.)?soundcloud\.com/[^\s]+)'

def download_soundcloud_track(url: str, output_dir: str) -> str:
    """A function to download a SoundCloud track and convert it to MP3."""
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
    if not message.text:
        return

    urls = re.findall(SC_REGEX, message.text)
    if not urls:
        return

    url = urls[0]
    processing_msg = await message.reply("Downloading track from SoundCloud...")

    output_dir = "./temp_audio"
    os.makedirs(output_dir, exist_ok=True)

    try:
        file_path = await asyncio.to_thread(download_soundcloud_track, url, output_dir)

        audio = FSInputFile(file_path)
        await bot.send_audio(
            chat_id=message.chat.id,
            audio=audio,
            reply_to_message_id=message.message_id
        )

        os.remove(file_path)
        
    except Exception as e:
        await message.reply(f"Error: {e}")
    finally:
        await processing_msg.delete()

async def main():
    print("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
