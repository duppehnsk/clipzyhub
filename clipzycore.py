import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from yt_dlp import YoutubeDL
import os

def browse_location():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_var.set(folder_selected)

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            percent = int(downloaded / total * 100)
            progress_var.set(percent)
            progress_bar.update()

def download_video():
    url = url_var.get().strip()
    path = path_var.get()
    quality = quality_var.get()
    cookies_file = cookies_var.get().strip()
    
    if not url or not path:
        messagebox.showerror("Ошибка", "Введите ссылку и выберите папку!")
        return

    # Преобразование коротких ссылок
    if "youtu.be/" in url:
        url = url.replace("youtu.be/", "youtube.com/watch?v=")

    # Настройки yt-dlp
    ydl_opts = {
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',
        'format': 'bestvideo+bestaudio/best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    # Подключение cookies, если файл указан
    if cookies_file and os.path.isfile(cookies_file):
        ydl_opts['cookies'] = cookies_file

    # Фильтр по качеству
    if quality == "Среднее":
        ydl_opts['format'] = 'best[height<=720]+bestaudio/best[height<=720]'
    elif quality == "Низкое":
        ydl_opts['format'] = 'best[height<=480]+bestaudio/best[height<=480]'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        messagebox.showinfo("Успех", "Видео успешно скачано!")
        progress_var.set(0)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скачать видео.\n{e}")
        progress_var.set(0)

# GUI
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("650x300")

url_var = tk.StringVar()
path_var = tk.StringVar()
quality_var = tk.StringVar(value="Высшее")
cookies_var = tk.StringVar()
progress_var = tk.IntVar(value=0)

# Ссылка на видео
tk.Label(root, text="Ссылка на видео:").pack(pady=5)
tk.Entry(root, textvariable=url_var, width=80).pack()

# Папка для сохранения
tk.Label(root, text="Папка для сохранения:").pack(pady=5)
frame_path = tk.Frame(root)
frame_path.pack()
tk.Entry(frame_path, textvariable=path_var, width=55).pack(side=tk.LEFT, padx=(0,5))
tk.Button(frame_path, text="Обзор", command=browse_location).pack(side=tk.LEFT)

# Качество видео
tk.Label(root, text="Качество видео:").pack(pady=5)
tk.OptionMenu(root, quality_var, "Высшее", "Среднее", "Низкое").pack()

# Cookies файл (опционально)
tk.Label(root, text="Файл cookies (если нужно):").pack(pady=5)
tk.Entry(root, textvariable=cookies_var, width=80).pack()

# Прогресс-бар
progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

# Кнопка скачивания
tk.Button(root, text="Скачать видео", command=download_video, bg="green", fg="white").pack(pady=10)

root.mainloop()
