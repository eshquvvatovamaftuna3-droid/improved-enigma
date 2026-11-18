
import os
import asyncio
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.getenv("PORT", "10000"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! 🎬\nInstagram yoki TikTok video havolasini yuboring."
    )


def download_video(url, folder):
    options = {
        "outtmpl": str(Path(folder) / "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "max_filesize": 45 * 1024 * 1024,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))


async def get_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    domain = urlparse(url).netloc.lower().removeprefix("www.")

    if domain not in (
        "instagram.com", "tiktok.com", "vm.tiktok.com", "vt.tiktok.com"
    ):
        await update.message.reply_text(
            "Instagram yoki TikTok havolasini yuboring."
        )
        return

    msg = await update.message.reply_text("⏳ Video yuklanmoqda...")

    try:
        with tempfile.TemporaryDirectory() as folder:
            path = await asyncio.to_thread(download_video, url, folder)
            if not path.exists():
                raise Exception("Video topilmadi")

            with open(path, "rb") as video:
                await update.message.reply_video(video=video)

        await msg.delete()
    except Exception:
        await msg.edit_text(
            "Video yuklanmadi. Boshqa havola bilan urinib ko‘ring."
        )


def main():
    if not BOT_TOKEN or not HOST:
        raise RuntimeError("BOT_TOKEN yoki RENDER_EXTERNAL_HOSTNAME yo‘q")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_video))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{HOST}/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()
        
