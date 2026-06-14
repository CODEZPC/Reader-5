from tkinter import *
from urllib.parse import urljoin
import fake_useragent
from tkinter import messagebox
from tkinter import font as tkfont
from threading import Thread
from bs4 import BeautifulSoup
from winotify import Notification, audio
import os, re, sys, time, random, requests, math

tk = Tk()

MAX_THREADS = 0
MAX_THREADS_DEFAULT = 1
MAX_THREADS_MAX = 1
"#3C3F43"
"#90BFF5"


class Crawler:

    def __init__(self):
        """主线程初始化"""
        # 初始化 requests Session 与默认 headers，减少 403 风险
        self.session = requests.Session()
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        try:
            ua = fake_useragent.UserAgent()
            self.ua_string = ua.random
        except Exception:
            self.ua_string = default_ua
        # 一些常见浏览器头部，session 默认使用
        self.session.headers.update(
            {
                "User-Agent": self.ua_string,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8",
                "Referer": "https://www.qidiy.com/",
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip, deflate",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        # 当被目标站点强力拦截时，允许回退到 cloudscraper（如果已安装）
        self.use_cloudscraper_if_needed = True
        self.load_ui_init()

    def change_threads(self, delta):
        global MAX_THREADS
        MAX_THREADS += delta
        if MAX_THREADS == 1:
            self.threads_entry_minus.configure(state=DISABLED)
        else:
            self.threads_entry_minus.configure(state=NORMAL)
        if MAX_THREADS == MAX_THREADS_MAX:
            self.threads_entry_add.configure(state=DISABLED)
        else:
            self.threads_entry_add.configure(state=NORMAL)
        self.threads_entry.configure(text=MAX_THREADS)

    def load_ui_init(self):
        self.font_text = tkfont.Font(family="HYWenHei-85W", size=12)
        self.font_text_small = tkfont.Font(family="HYWenHei-85W", size=10)
        self.font_num = tkfont.Font(family="Jetbrains mono", size=10)
        self.fg = "#90BFF5"
        self.bg = "#3C3F43"  # (60, 63, 67)
        self.bbg = "#36393C"

        tk.configure(bg="#3C3F43")
        tk.title("Novel Crawler")
        tk.geometry("266x576")
        tk.resizable(False, False)

        self.option_frame = Frame(
            tk,
            bg=self.bbg,
            width=226,
            height=536,
        )
        self.option_frame.place(x=20, y=20)
        self.option_frame.pack_propagate(False)

        self.book_number = Label(
            self.option_frame,
            text="*书籍编号*",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.book_number.pack(pady=(20, 3))

        self.book_number_entry = Entry(
            self.option_frame,
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
        )
        self.book_number_entry.pack(pady=0)

        self.book_chapter = Label(
            self.option_frame,
            text="*章节编号*",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.book_chapter.pack(pady=(20, 3))

        self.book_chapter_entry = Entry(
            self.option_frame,
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
        )
        self.book_chapter_entry.pack(pady=0)

        self.chanter_page = Label(
            self.option_frame,
            text="源页码",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.chanter_page.pack(pady=(20, 3))

        self.chanter_page_entry = Entry(
            self.option_frame,
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
        )
        self.chanter_page_entry.pack(pady=0)

        self.threads = Label(
            self.option_frame,
            text="最大线程数",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.threads.pack(pady=(20, 3))

        self.threads_frame = Frame(self.option_frame, bg=self.bg)
        self.threads_frame.pack(pady=0)

        self.threads_entry_minus = Button(
            self.threads_frame,
            text="-",
            font=self.font_num,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
            command=lambda: self.change_threads(-1),
        )
        self.threads_entry_minus.pack(side="left", pady=0)

        self.threads_entry = Label(
            self.threads_frame,
            text=MAX_THREADS,
            font=self.font_num,
            width=5,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
        )
        self.threads_entry.pack(side="left", pady=0)

        self.threads_entry_add = Button(
            self.threads_frame,
            text="+",
            font=self.font_num,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
            command=lambda: self.change_threads(1),
        )
        self.threads_entry_add.pack(side="left", pady=0)

        self.threads_entry_default = Button(
            self.threads_frame,
            text="默认",
            font=self.font_text_small,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
            command=lambda: self.change_threads(MAX_THREADS_DEFAULT - MAX_THREADS)
        )
        self.threads_entry_default.pack(side="left", pady=0)

        self.threads_entry_max = Button(
            self.threads_frame,
            text="最大",
            font=self.font_text_small,
            fg=self.fg,
            bg=self.bg,
            justify="center",
            relief=FLAT,
            command=lambda: self.change_threads(MAX_THREADS_MAX - MAX_THREADS)
        )
        self.threads_entry_max.pack(side="left", pady=0)

        self.change_threads(MAX_THREADS_DEFAULT)

        self.status_progress_title = Label(
            self.option_frame,
            text="进度",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.status_progress_title.pack(pady=(20, 3))

        self.status_progress = Label(
            self.option_frame,
            text="Not Launched",
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bbg,
            justify="center",
            relief=FLAT,
        )
        self.status_progress.pack(pady=0)

        self.status_eta_title = Label(
            self.option_frame,
            text="预计时间",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.status_eta_title.pack(pady=(20, 3))

        self.status_eta = Label(
            self.option_frame,
            text="Not Launched",
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bbg,
            justify="center",
            relief=FLAT,
        )
        self.status_eta.pack(pady=0)

        self.start = Button(
            self.option_frame,
            text="启动",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
            justify="center",
            relief=FLAT,
            command=self.launch_prepare,
        )
        self.start.pack(pady=(40, 0))
    
    def launch_prepare(self):
        self.target_book = self.book_number_entry.get()
        self.target_chapter = self.book_chapter_entry.get()

        try:
            self.target_book = int(self.target_book)
        except ValueError:
            return
        
        try:
            self.target_chapter = int(self.target_chapter)
        except ValueError:
            return
        
        self.ui_launch()

    def load_ui_launch(self):
        pass

    def ui_launch(self, x=266):
        if x >= 1024:
            tk.geometry(f"1024x576")
            self.load_ui_launch()
            return
        tk.geometry(f"{x+8}x576")
        tk.after(5, lambda: self.ui_launch(x + 8))


if __name__ == "__main__":
    app = Crawler()
    tk.mainloop()
