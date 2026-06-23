from tkinter import *
from urllib.parse import urljoin
import fake_useragent
from tkinter import messagebox
from tkinter import font as tkfont
from threading import Thread
from bs4 import BeautifulSoup
from winotify import Notification, audio
import os, re, time, random, json, requests, math

from network import get_soup


tk = Tk()

MAX_THREADS = 0
MAX_THREADS_DEFAULT = 1
MAX_THREADS_MAX = 1
URLS = []
CHECKPOINT_FILE = "crawler_checkpoint.json"


class Crawler:
    def __init__(self):
        """主线程初始化"""
        self.session = requests.Session()
        default_ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        try:
            ua = fake_useragent.UserAgent()
            self.ua_string = ua.random
        except Exception:
            self.ua_string = default_ua

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
        self.use_cloudscraper_if_needed = True
        self.continue_patch = 0
        self.load_ui_init()

    def change_threads(self, delta):
        global MAX_THREADS
        MAX_THREADS = max(1, min(MAX_THREADS_MAX, MAX_THREADS + delta))
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
        self.bg = "#3C3F43"
        self.bbg = "#36393C"

        tk.configure(bg=self.bg)
        tk.title("小说爬虫")
        tk.geometry("266x576")
        tk.resizable(False, False)

        self.option_frame = Frame(tk, bg=self.bbg, width=226, height=536)
        self.option_frame.place(x=20, y=20)
        self.option_frame.pack_propagate(False)

        self.book_number = Label(self.option_frame, text="*书籍编号*", font=self.font_text, fg=self.fg, bg=self.bbg)
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

        self.book_chapter = Label(self.option_frame, text="*章节编号*", font=self.font_text, fg=self.fg, bg=self.bbg)
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

        self.chanter_page = Label(self.option_frame, text="源页码", font=self.font_text, fg=self.fg, bg=self.bbg)
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

        self.threads = Label(self.option_frame, text="最大线程数", font=self.font_text, fg=self.fg, bg=self.bbg)
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
            text=str(MAX_THREADS),
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
            command=lambda: self.change_threads(MAX_THREADS_DEFAULT - MAX_THREADS),
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
            command=lambda: self.change_threads(MAX_THREADS_MAX - MAX_THREADS),
        )
        self.threads_entry_max.pack(side="left", pady=0)

        self.change_threads(MAX_THREADS_DEFAULT)

        self.status_progress_title = Label(self.option_frame, text="进度", font=self.font_text, fg=self.fg, bg=self.bbg)
        self.status_progress_title.pack(pady=(20, 3))

        self.status_progress = Label(
            self.option_frame,
            text="未启动",
            font=self.font_num,
            width=20,
            fg=self.fg,
            bg=self.bbg,
            justify="center",
            relief=FLAT,
        )
        self.status_progress.pack(pady=0)

        self.status_eta_title = Label(self.option_frame, text="预计时间", font=self.font_text, fg=self.fg, bg=self.bbg)
        self.status_eta_title.pack(pady=(20, 3))

        self.status_eta = Label(
            self.option_frame,
            text="未启动",
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
        def reset(widget):
            widget.configure(fg=self.fg)
            self.start.configure(state=NORMAL)

        def error(widget):
            widget.configure(fg=self.fg_err)
            self.start.configure(state=DISABLED)
            tk.after(3000, lambda: reset(widget))

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
        self.info_frame = Frame(tk, bg=self.bbg, width=738, height=536)
        self.info_frame.place(x=266, y=20)

        self.status_show = Label(
            self.info_frame,
            text="正在准备爬取……",
            font=self.font_text_large,
            fg=self.fg,
            bg=self.bbg,
        )
        self.status_show.place(x=10, y=10)

        self.detail_show = Label(
            self.info_frame,
            text="",
            font=self.font_text,
            fg=self.fg,
            bg=self.bbg,
            justify="left",
            anchor="nw",
            wraplength=700,
        )
        self.detail_show.place(x=30, y=50)

        thread = Thread(target=self.crawl, args=(self.target_book, self.target_chapter), daemon=True)
        thread.start()

    def ui_launch(self, x=266):
        if x >= 1024:
            tk.geometry("1024x576")
            self.load_ui_launch()
            return
        tk.geometry(f"{x+8}x576")
        tk.after(5, lambda: self.ui_launch(x + 8))

    def status_update(self, title, url, crawled_chapter, used_time, total_charaters):
        self.status_show.configure(text=title)
        detail_lines = []
        current_title = getattr(self, "current_title", "")
        current_url = getattr(self, "current_url", url if url else "")
        current_words = getattr(self, "current_words", 0)
        processed_pages = getattr(self, "processed_pages", 0)
        total_chapters = getattr(self, "total_chapters", 0)
        eta_text = getattr(self, "eta_text", "--:--:--")

        if current_title:
            detail_lines.append(f"章节名称：{current_title}")
        if current_url:
            detail_lines.append(f"当前URL：{current_url}")
        if total_chapters:
            detail_lines.append(f"进度：{processed_pages} / {total_chapters}")
        if current_words:
            detail_lines.append(f"已爬取字数：{current_words:,} 字")
        if eta_text:
            detail_lines.append(f"预计时间：{eta_text}")

        if hasattr(self, "detail_show"):
            self.detail_show.configure(text="\n".join(detail_lines))

    def _checkpoint_path(self):
        return os.path.join(os.path.dirname(__file__), CHECKPOINT_FILE)

    def _load_checkpoint(self):
        path = self._checkpoint_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return None

    def _save_checkpoint(self, *, book, chapter, current_url, current_title, processed_pages):
        checkpoint = {
            "book": book,
            "chapter": chapter,
            "current_url": current_url,
            "current_title": current_title,
            "processed_pages": processed_pages,
            "total_chapters": getattr(self, "total_chapters", 0),
            "current_words": getattr(self, "current_words", 0),
            "elapsed_seconds": max(0, time.time() - getattr(self, "start_time", time.time())),
            "url": getattr(self, "url", current_url),
            "urlb": getattr(self, "urlb", current_url),
            "urlbb": getattr(self, "urlbb", current_url),
            "contents": getattr(self, "contents", []),
            "midbackup": getattr(self, "midbackup", []),
            "backup": getattr(self, "backup", []),
        }
        with open(self._checkpoint_path(), "w", encoding="utf-8") as file:
            json.dump(checkpoint, file, ensure_ascii=False, indent=2)

    def _clear_checkpoint(self):
        path = self._checkpoint_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    def _extract_total_chapters(self, soup):
        options = soup.find_all("option")
        if not options:
            raise ValueError("未找到章节选项")
        numbers = re.findall(r"\d+", str(options[-1]))
        if len(numbers) < 4:
            raise ValueError("章节总数解析失败")
        return int(numbers[3])

    def _extract_chapter_title(self, soup, content_text=""):
        selectors = ["h1", ".chapter-title", ".bookname h1", ".content h1"]
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                title = node.get_text(" ", strip=True)
                if title:
                    return re.sub(r"\s*[-_|].*$", "", title).strip()

        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(" ", strip=True)
            if title:
                title = re.split(r"[-_|]", title)[0].strip()
                if title:
                    return title

        if content_text:
            for line in content_text.splitlines():
                line = line.strip()
                if line:
                    return line
        return "未知章节"

    def crawl(self, book, chapter):
        self.current_title = ""
        self.current_url = ""
        self.current_words = 0
        self.processed_pages = 0
        self.total_chapters = 0
        self.eta_text = "--:--:--"

        if not self.continue_patch:
            self.all = 1
            self.start_time = time.time()
            self.contents = []
            self.midbackup = []
            self.backup = []
            self.url = f"https://www.qidiy.com/book/{book}/{chapter}.html"
            URLS.append(self.url)
            self.urlb = self.url
            self.urlbb = self.urlb
        else:
            checkpoint = self._load_checkpoint()
            if checkpoint and checkpoint.get("book") == book and checkpoint.get("chapter") == chapter:
                self.url = checkpoint.get("current_url", self.urlbb)
                self.contents = checkpoint.get("contents", []).copy()
                self.midbackup = checkpoint.get("midbackup", self.contents.copy())
                self.backup = checkpoint.get("backup", self.contents.copy())
                self.urlb = checkpoint.get("urlb", self.url)
                self.urlbb = checkpoint.get("urlbb", self.urlb)
                self.start_time = time.time() - checkpoint.get("elapsed_seconds", 0)
                self.current_words = checkpoint.get("current_words", 0)
                self.processed_pages = checkpoint.get("processed_pages", 0)
                self.total_chapters = checkpoint.get("total_chapters", 0)
                self.current_title = checkpoint.get("current_title", "")
                self.current_url = self.url
            else:
                self.url = self.urlbb
                self.contents = self.backup.copy()
                self.midbackup = self.contents.copy()

        try:
            self.status_update("预处理……", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")

            pagination_page = get_soup(f"https://www.qidiy.com/book/{book}_99/")
            pagination_page.find("select", {"name": "pageselect"})
            total_chapters = self._extract_total_chapters(pagination_page)
            self.total_chapters = total_chapters

            left_page = 1
            right_page = math.ceil(total_chapters / 20)
            chapter = int(self.url.replace(f"https://www.qidiy.com/book/{book}/", "").replace(".html", ""))

            found_page = False
            try:
                self.status_update(f"尝试右边界……第{right_page}页", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
                finding = get_soup(f"https://www.qidiy.com/book/{book}_{right_page}/").find_all("ul", class_="section-list fix")[1]
                chapter_urls = [
                    int(tag["href"].replace(f"/book/{book}/", "").replace(".html", ""))
                    for tag in finding.find_all("a", href=True)
                ]
                if chapter_urls and chapter_urls[0] <= chapter <= chapter_urls[-1]:
                    start = right_page * 20 - (19 - chapter_urls.index(chapter))
                    found_page = True
                    self.status_update(f"右边界命中：第{right_page}页", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
                else:
                    self.status_update("右边界未命中，开始二分定位", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
            except Exception:
                self.status_update("右边界检查失败，开始二分定位", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")

            if not found_page:
                while left_page <= right_page:
                    middle_page = (left_page + right_page) // 2
                    self.status_update(f"正在定位……第{middle_page}页", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")

                    finding = get_soup(f"https://www.qidiy.com/book/{book}_{middle_page}/").find_all("ul", class_="section-list fix")[1]
                    chapter_urls = []
                    for tag in finding.find_all("a", href=True):
                        href = tag["href"]
                        chapter_urls.append(int(href.replace(f"/book/{book}/", "").replace(".html", "")))
                    time.sleep(1)

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
            self.status_update(f"定位完成，需要爬取{self.all}章节", self.url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
            self.all *= 2
            avg = 0

            while self.url and not self.url.endswith(f"/book/{book}/"):
                speed_time = time.time()

                if self.processed_pages % 2 == 0:
                    self.backup = self.midbackup.copy()
                    self.midbackup = self.contents.copy()
                    self.urlbb = self.urlb
                    self.urlb = self.url

                self.soup = get_soup(self.url)
                self.content_div = self.soup.find("div", {"id": "content"})
                if not self.content_div:
                    messagebox.showerror("错误", "未找到内容")
                    raise ValueError("未找到内容")

                raw_text = self.content_div.get_text()
                self.text = raw_text.replace("　　", "\n")
                self.text = self.text.replace(" ", "")
                self.text = re.sub(r" {2,}", "\n", self.text)
                self.text = self.text.replace("(第1/2页)", "")
                self.text = self.text.replace("(第2/2页)", "")
                self.text = self.text.replace("(第1/1页)", "")
                self.text = self.text.replace("（本章未完，请点击下一页继续阅读）", "")
                self.text = self.text.strip()
                self.text = self.text.replace("\n\n", "\n  ")
                self.text = self.text.replace(" \n", "\n")

                if self.contents and self.url.endswith("/2.html"):
                    self.text = "\n".join(self.text.split("\n")[1:])

                self.contents.append(self.text)
                self.processed_pages += 1
                self.current_words += len(self.text.replace("\n", "").replace(" ", ""))
                self.current_title = self._extract_chapter_title(self.soup, raw_text)
                self.current_url = self.url

                if self.processed_pages % 20 == 0:
                    with open("output.txt", "w", encoding="utf-8") as file:
                        file.write("\n".join(self.backup))
                    self.status_update(f"第{self.processed_pages}页已解析，已保存备份", self.current_url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
                else:
                    self.status_update(f"第{self.processed_pages}页已解析", self.current_url, self.current_title, self.eta_text, f"{self.current_words:,} 字")

                self.url = self.find_next(self.soup, self.url)
                time.sleep(0.8)

                speed_time = time.time() - speed_time
                avg = (avg * (self.processed_pages - 1) + speed_time) / self.processed_pages
                self.all -= 1
                hour = int(self.all * avg // 3600)
                minute = int(self.all * avg // 60) - hour * 60
                second = int(self.all * avg) - hour * 3600 - minute * 60
                self.eta_text = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"
                self.status_eta.configure(text=self.eta_text)
                self.status_eta.update()

                self._save_checkpoint(
                    book=book,
                    chapter=chapter,
                    current_url=self.current_url,
                    current_title=self.current_title,
                    processed_pages=self.processed_pages,
                )

            self.status_update("解析完成，写入文件", self.current_url, self.current_title, self.eta_text, f"{self.current_words:,} 字")

            with open("output.txt", "w", encoding="utf-8") as file:
                file.write("\n".join(self.contents))
            self._clear_checkpoint()

            self.status_update("写入文件完成", self.current_url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
            return
        except Exception as error:
            self.status_update("爬取失败，正在保存已爬取内容……", self.current_url, self.current_title, self.eta_text, f"{self.current_words:,} 字")
            with open("output.txt", "w", encoding="utf-8") as file:
                file.write("\n".join(self.backup))
            self._save_checkpoint(
                book=book,
                chapter=chapter,
                current_url=getattr(self, "current_url", self.url),
                current_title=getattr(self, "current_title", ""),
                processed_pages=self.processed_pages,
            )
            print(error)
            messagebox.showerror("错误", f"爬取失败，已爬取内容已保存，可稍后网络恢复继续爬取\n错误详情：{str(error)}")

            self.start.configure(text="继续", state=NORMAL)
            self.continue_patch = 1
            self.status_eta.configure(text="--:--:--")
            self.eta_text = "--:--:--"
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
