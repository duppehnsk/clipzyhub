import os
import instaloader
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TOKEN = "_TGBOTTOKEN_"
DOWNLOAD_DIR = "downloads"
MAX_TELEGRAM_MB = 50  # максимальный размер видео для Telegram

# --- Очистка старых файлов ---
def clean_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        for file in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print("Ошибка при удалении файла:", e)

# --- Прогресс скачивания ---
async def progress_hook(d, status_msg: Update):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        if total_bytes:
            percent = int(downloaded_bytes / total_bytes * 100)
            try:
                if not hasattr(status_msg, "_last_percent") or percent != status_msg._last_percent:
                    status_msg._last_percent = percent
                    await status_msg.edit_text(f"⏳ Скачиваю видео... {percent}%")
            except:
                pass

# --- Скачивание Reels (Instagram) ---
def download_reels(url):
    clean_downloads()
    L = instaloader.Instaloader()
    shortcode = url.split("/")[-2]
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            L.download_post(post, target=DOWNLOAD_DIR)
            for file in os.listdir(DOWNLOAD_DIR):
                if file.endswith(".mp4"):
                    return os.path.join(DOWNLOAD_DIR, file)
    except Exception as e:
        print("Ошибка при скачивании Reels:", e)
    return None

# --- Скачивание Shorts (YouTube) ---
def download_youtube_shorts(url, status_msg=None):
    clean_downloads()
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'progress_hooks': [lambda d: asyncio.create_task(progress_hook(d, status_msg))] if status_msg else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"{DOWNLOAD_DIR}/{info['id']}.mp4"
    except Exception as e:
        print("Ошибка при скачивании Shorts:", e)
        return None

# --- Скачивание TikTok без водяного знака ---
def download_tiktok(url, status_msg=None):
    clean_downloads()
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'skip_download': False,
        'postprocessors': [{
            'key': 'FFmpegVideoRemuxer',
            'preferedformat': 'mp4',
        }],
        'extractor_args': {'tiktok': {'without_watermark': ['True']}},
        'progress_hooks': [lambda d: asyncio.create_task(progress_hook(d, status_msg))] if status_msg else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"{DOWNLOAD_DIR}/{info['id']}.mp4"
    except Exception as e:
        print("Ошибка при скачивании TikTok:", e)
        return None

# --- Команда /start ---
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Привет! 👋 Отправь мне ссылку на Reels (Instagram), Shorts (YouTube) или TikTok — и я скачаю видео без текста и водяных знаков 🔥"
    )

# --- Обработка сообщений ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ Подготавливаю скачивание...")

    video_path = None
    error_message = None

    try:
        if "instagram.com/reel/" in url:
            video_path = download_reels(url)
        elif "youtube.com/shorts/" in url or "youtu.be/" in url:
            video_path = download_youtube_shorts(url, status_msg=status_msg)
        elif "tiktok.com/" in url:
            video_path = download_tiktok(url, status_msg=status_msg)
        else:
            error_message = "❌ Пожалуйста, отправь ссылку на Instagram Reels, YouTube Shorts или TikTok."
    except Exception as e:
        error_message = f"⚠️ Ошибка при обработке: {e}"

    if video_path and os.path.exists(video_path):
        try:
            size_mb = os.path.getsize(video_path) / 1024 / 1024
            if size_mb > MAX_TELEGRAM_MB:
                await status_msg.edit_text(
                    f"⚠️ Видео слишком большое для Telegram ({int(size_mb)} MB). Скачай его напрямую с сервера."
                )
            else:
                await status_msg.edit_text("✅ Видео готово!")
                with open(video_path, "rb") as video:
                    await update.message.reply_video(video=video)
            clean_downloads()
        except Exception as e:
            await update.message.reply_text(f"⚠️ Не удалось отправить видео: {e}")
    else:
        await status_msg.edit_text(error_message or "⚠️ Не удалось скачать видео. Попробуй другую ссылку.")

# --- Основной запуск ---
def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
