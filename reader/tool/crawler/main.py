from tkinter import *
from urllib.parse import urljoin
import fake_useragent
from tkinter import messagebox
from tkinter import font as tkfont
from threading import Thread
from bs4 import BeautifulSoup
from winotify import Notification, audio
import os, re, sys, time, random, requests, math

from network import get_soup

tk = Tk()

MAX_THREADS = 0
MAX_THREADS_DEFAULT = 1
MAX_THREADS_MAX = 1
URLS = []
"#3C3F43"
"#90BFF5"


class Crawler:

    def __init__(self):
        """主线程初始化"""
        self.load_ui_init()
        self.continue_patch = 0

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
        self.font_text_large = tkfont.Font(family="HYWenHei-85W", size=15)
        self.font_num = tkfont.Font(family="Jetbrains mono", size=10)
        self.fg = "#90BFF5"
        self.fg_err = "#F59090"
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
            disabledbackground=self.bg,
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
            disabledbackground=self.bg,
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
            disabledbackground=self.bg,
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

        def reset(object):
            object.configure(fg=self.fg)
            self.start.configure(state=NORMAL)

        def error(object):
            object.configure(fg=self.fg_err)
            self.start.configure(state=DISABLED)
            tk.after(3000, lambda: reset(object))

        self.target_book = self.book_number_entry.get()
        self.target_chapter = self.book_chapter_entry.get()

        try:
            self.target_book = int(self.target_book)
        except ValueError:
            error(self.book_number_entry)
            return
        
        try:
            self.target_chapter = int(self.target_chapter)
        except ValueError:
            error(self.book_chapter_entry)
            return
        
        self.start.configure(state=DISABLED)
        self.book_chapter_entry.configure(state=DISABLED)
        self.book_number_entry.configure(state=DISABLED)
        self.threads_entry.configure(state=DISABLED)
        self.threads_entry_add.configure(state=DISABLED)
        self.threads_entry_default.configure(state=DISABLED)
        self.threads_entry_max.configure(state=DISABLED)
        self.threads_entry_minus.configure(state=DISABLED)
        self.chanter_page_entry.configure(state=DISABLED)
        
        self.ui_launch()

    def load_ui_launch(self):
        self.info_frame = Frame(
            tk,
            bg=self.bbg,
            width=738,
            height=536,
        )
        self.info_frame.place(x=266, y=20)
        
        self.status_show = Label(
            self.info_frame,
            text="正在准备爬取……",
            font=self.font_text_large,
            fg=self.fg,
            bg=self.bbg,
        )
        self.status_show.place(x=10,y=10)

        self.detail_show = Label(
            self.info_frame,
            text="",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
        )
        self.detail_show.place(x=30,y=50)

        thread = Thread(
            target=self.crawl, args=(self.target_book, self.target_chapter)
        )
        thread.start()

    def ui_launch(self, x=266):
        if x >= 1024:
            tk.geometry(f"1024x576")
            self.load_ui_launch()
            return
        tk.geometry(f"{x+8}x576")
        tk.after(5, lambda: self.ui_launch(x + 8))

    def status_update(self, title, url, crawled_chapter, used_time, total_charaters):
        self.status_show.configure(text=title)
    
    def crawl(self, book, chapter):

        if not self.continue_patch:
            self.all = 1  # 剩余需要爬取的章节数，用于估算 ETA
            self.start_time = time.time()  # 本次任务开始时间
            self.contents = []  # 当前已抓取的章节内容
            self.midbackup = []  # 中间备份内容，用于断点恢复
            self.backup = []  # 上一次稳定备份内容
            self.url = f"https://www.qidiy.com/book/{book}/{chapter}.html"  # 当前章节 URL
            URLS.append(self.url)
            self.urlb = self.url  # 上一个章节 URL
            self.urlbb = self.urlb  # 上上个章节 URL
        else:
            self.url = self.urlbb  # 断点续爬时从最后稳定位置继续
            self.contents = self.backup.copy()  # 恢复上次保存的内容
            self.midbackup = self.contents.copy()  # 同步当前中间备份
        processed_pages = 0

        try:
            """预处理"""
            self.status_update("预处理……", 0, 0, 0, 0)

            pagination_page = get_soup(f"https://www.qidiy.com/book/{book}_99/")  # 章节分页页
            pagination_page.find(
                "select", {"name": "pageselect"}
            )
            # 查找所有的 <option> 标签，并获取最后一个
            total_chapters = int(re.findall(r"\d+", str(pagination_page.find_all("option")[-1]))[3])

            left_page = 1  # 二分查找左边界
            right_page = math.ceil(total_chapters / 20)  # 二分查找右边界
            chapter = int(
                self.url.replace(f"https://www.qidiy.com/book/{book}/", "").replace(
                    ".html", ""
                )
            )

            # 先尝试右边界（最后一页），若命中则直接计算 start，否则再用二分查找
            found_page = False
            try:
                self.status_update(f"尝试右边界……第{right_page}页", 0, 0, 0, 0)
                finding = get_soup(
                    f"https://www.qidiy.com/book/{book}_{right_page}/"
                ).find_all("ul", class_="section-list fix")[1]
                chapter_urls = [  # 当前分页里的章节编号列表
                    int(tag["href"].replace(f"/book/{book}/", "").replace(".html", ""))
                    for tag in finding.find_all("a", href=True)
                ]
                if chapter_urls and chapter_urls[0] <= chapter <= chapter_urls[-1]:
                    start = right_page * 20 - (19 - chapter_urls.index(chapter))
                    found_page = True
                    self.status_update(f"右边界命中：第{right_page}页", 0, 0, 0, 0)
                else:
                    self.status_update("右边界未命中，开始二分定位", 0, 0, 0, 0)
            except Exception:
                self.status_update("右边界检查失败，开始二分定位", 0, 0, 0, 0)

            if not found_page:
                while left_page <= right_page:
                    middle_page = (left_page + right_page) // 2  # 当前二分页码
                    self.status_update(f"正在定位……第{middle_page}页", 0, 0, 0, 0)

                    finding = get_soup(
                        f"https://www.qidiy.com/book/{book}_{middle_page}/"
                    ).find_all("ul", class_="section-list fix")[1]
                    chapter_urls = []
                    for tag in finding.find_all("a", href=True):
                        href = tag["href"]
                        chapter_urls.append(
                            int(href.replace(f"/book/{book}/", "").replace(".html", ""))
                        )
                    time.sleep(1)

                    # 正确更新左右边界，避免 mid 不变导致的死循环
                    if chapter < chapter_urls[0]:
                        right_page = middle_page - 1
                        continue
                    elif chapter > chapter_urls[-1]:
                        left_page = middle_page + 1
                        continue
                    else:
                        start = middle_page * 20 - (19 - chapter_urls.index(chapter))
                        break

            self.all = total_chapters - start + 1
            self.status_update(f"定位完成，需要爬取{self.all}章节", 0, 0, 0, 0)
            self.all *= 2
            avg = 0  # 单章节平均耗时，用于估算剩余时间

            """爬取"""
            while self.url and not self.url.endswith(f"/book/{book}/"):
                speed_time = time.time()
                if processed_pages % 2 == 0:
                    self.backup = self.midbackup.copy()  # 保存稳定备份
                    self.midbackup = self.contents.copy()  # 更新中间备份
                    self.urlbb = self.urlb  # 更新上上个 URL
                    self.urlb = self.url  # 更新上一个 URL

                """请求头"""
                self.soup = get_soup(self.url)
                self.content_div = self.soup.find("div", {"id": "content"})
                if not self.content_div:
                    messagebox.showerror("错误", "未找到内容")
                    raise ValueError("未找到内容")

                """内容解析整理"""
                self.text = self.content_div.get_text()
                self.text = self.text.replace("　　", "\n")
                self.text = self.text.replace(" ", "")
                self.text = re.sub(r" {2,}", "\n", self.text)
                self.text = self.text.replace("(第1/2页)", "")
                self.text = self.text.replace("(第2/2页)", "")
                self.text = self.text.replace("(第1/1页)", "")
                self.text = self.text.replace("（本章未完，请点击下一页继续阅读）", "")
                self.text = self.text.strip()
                self.text = self.text.replace("\n\n", "\n  ")
                self.text = self.text.replace(" \n", "\n")

                """重复标题移除"""
                if self.contents and self.url.endswith("/2.html"):
                    self.text = "\n".join(self.text.split("\n")[1:])
                self.contents.append(self.text)
                processed_pages += 1

                if processed_pages % 20 == 0:
                    with open(f"output.txt", "w", encoding="utf-8") as f:
                        f.write("\n".join(self.backup))
                    self.status_update(f"第{processed_pages}页已解析，已保存备份", self.url, 0, 0, 0)
                else:
                    self.status_update(f"第{processed_pages}页已解析", self.url, 0, 0, 0)
                self.url = self.find_next(self.soup, self.url)
                time.sleep(0.8)

                speed_time = time.time() - speed_time
                avg = (avg * (processed_pages - 1) + speed_time) / processed_pages
                self.all -= 1
                hour = int(self.all * avg // 3600)
                minute = int(self.all * avg // 60) - hour * 60
                second = int(self.all * avg) - hour * 3600 - minute * 60
                self.status_eta.configure(
                    text=f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"
                )
                self.status_eta.update()

            self.status_update(f"解析完成，写入文件", 0, 0, 0, 0)

            """写入文件"""
            with open(f"output.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.contents))

            self.status_update(f"写入文件完成", 0, 0, 0, 0)
            return
        except Exception as e:
            self.status_update(f"爬取失败，正在保存已爬取内容……", 0, 0, 0, 0)
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.backup))
            print(e)
            messagebox.showerror("错误", f"爬取失败，已爬取内容已保存，可稍后网络恢复继续爬取\n错误详情：{str(e)}")

            self.start.configure(text="继续", state=NORMAL)
            self.continue_patch = 1
            self.status_eta.configure(text="--:--:--")
            self.status_eta.update()

            return

    def find_next(self, soup, url):
        """查找下一页链接"""
        next_link = soup.find("a", string="下一页")
        if next_link and "href" in next_link.attrs:
            return urljoin(url, next_link["href"])
        next_chapter = soup.find("a", string="下一章")
        if next_chapter and "href" in next_chapter.attrs:
            return urljoin(url, next_chapter["href"])
        return None


if __name__ == "__main__":
    app = Crawler()
    tk.mainloop()
