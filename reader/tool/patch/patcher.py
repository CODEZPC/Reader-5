from tkinter import *
from urllib.parse import urljoin
import fake_useragent
from tkinter import messagebox
from threading import Thread
from bs4 import BeautifulSoup
from winotify import Notification, audio
import os, re, sys, time, random, requests, math

# TODO BREAKPOINT & CONTINUE PATCH
ptk = Tk()

ICONS_FAILED = [
    r"D:\codefile\File\PIC\已处理\A-01.png",
    r"D:\codefile\File\PIC\已处理\B-01.png",
    r"D:\codefile\File\PIC\已处理\B-02.png",
    r"D:\codefile\File\PIC\已处理\B-03.png",
    r"D:\codefile\File\PIC\已处理\B-04.png",
    r"D:\codefile\File\PIC\已处理\B-05.png",
    r"D:\codefile\File\PIC\已处理\B-06.png",
    r"D:\codefile\File\PIC\已处理\B-07.png",
    r"D:\codefile\File\PIC\已处理\B-10.png",
    r"D:\codefile\File\PIC\已处理\C-06.png",
    r"D:\codefile\File\PIC\已处理\C-07.png",
    r"D:\codefile\File\PIC\已处理\C-08.png",
    r"D:\codefile\File\PIC\已处理\C-09.png",
    r"D:\codefile\File\PIC\已处理\+03.png",
]

ICONS_PROCESSING = [
    r"D:\codefile\File\PIC\已处理\+01.png",
    r"D:\codefile\File\PIC\已处理\+02.png",
    r"D:\codefile\File\PIC\已处理\C-04.png",
    r"D:\codefile\File\PIC\已处理\E-01.png",
    r"D:\codefile\File\PIC\已处理\E-02.png",
    r"D:\codefile\File\PIC\已处理\E-03.png",
]

ICONS_SUCCESS = [
    r"D:\codefile\File\PIC\已处理\+01.png",
    r"D:\codefile\File\PIC\已处理\+02.png",
    r"D:\codefile\File\PIC\已处理\C-04.png",
    r"D:\codefile\File\PIC\已处理\E-01.png",
    r"D:\codefile\File\PIC\已处理\E-02.png",
    r"D:\codefile\File\PIC\已处理\E-03.png",
    r"D:\codefile\File\PIC\已处理\B-08.png",
    r"D:\codefile\File\PIC\已处理\B-09.png",
]

URLS = []


class Patcher:
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
        self.load_ui()

    def load_ui(self):
        """UI加载"""
        ptk.title("Novel Patcher")
        ptk.configure(bg="#23272E")
        self.book = Label(
            ptk,
            text="   Book:",
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
        )
        self.book.grid(row=1, column=1)
        self.chapter = Label(
            ptk,
            text="Chapter:",
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
        )
        self.chapter.grid(row=2, column=1)
        self.book_input = Entry(
            ptk,
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
            relief=RIDGE,
            width=5,
        )
        self.book_input.grid(row=1, column=2)
        self.chapter_input = Entry(
            ptk,
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
            relief=RIDGE,
            width=8,
        )
        self.chapter_input.grid(row=2, column=2)
        self.start = Button(
            ptk,
            text="Start PATCHER",
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
            relief=RIDGE,
            width=14,
            command=lambda: self.spatch(
                self.book_input.get(), self.chapter_input.get()
            ),
        )
        self.start.grid(row=1, column=3, rowspan=2)
        self.eta = Label(
            ptk,
            text="    ETA:",
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
        )
        self.eta.grid(row=3, column=1)
        self.etatime = Label(
            ptk,
            text="--:--:--",
            font=("Jetbrains Mono", 16),
            bg="#23272E",
            fg="#C8C8C8",
        )
        self.etatime.grid(row=3, column=2)
        self.status = Text(
            ptk,
            height=30,
            font=("Jetbrains Mono", 10),
            bg="#23272E",
            fg="#C8C8C8",
            relief=RIDGE,
            width=100,
            state=DISABLED,
        )
        self.status.grid(row=4, column=1, columnspan=3)
        self.status.configure(state=NORMAL)
        self.status.insert(END, "Novel Patcher 1.0\n")
        self.status.insert(END, "Not started yet.\n")
        self.status.configure(state=DISABLED)
        """空白UI"""
        self.empty = Label(
            ptk, text="  ", font=("Jetbrains Mono", 16), bg="#23272E", fg="#C8C8C8"
        ).grid(row=0, column=0, columnspan=999)
        self.empty = Label(
            ptk, text="  ", font=("Jetbrains Mono", 16), bg="#23272E", fg="#C8C8C8"
        ).grid(row=999, column=999, columnspan=999)
        self.empty = Label(
            ptk, text="  ", font=("Jetbrains Mono", 16), bg="#23272E", fg="#C8C8C8"
        ).grid(row=0, column=0, rowspan=999)
        ptk.resizable(False, False)

    def spatch(self, book, chapter, continue_patch=False, processed=0):
        chapter = int(chapter)
        """启动爬取"""
        thread = Thread(
            target=self.patch, args=(book, chapter, continue_patch, processed)
        )
        thread.start()

    def patch(self, book, chapter, continue_patch, processed):

        def log_update(info, clear=False):
            self.status.configure(state=NORMAL)
            if clear:
                self.status.delete("1.0", END)
            self.status.insert(END, info)
            self.status.configure(state=DISABLED)
            self.status.update()
            self.status.see(END)

        def get_soup(url):
            # 使用 session 和稳定的 headers，遇到 403 时尝试 cloudscraper 回退
            headers = {
                "User-Agent": getattr(self, "ua_string", "Mozilla/5.0"),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8",
                "Referer": "https://www.qidiy.com/",
            }
            # 先尝试用 session 获取（可以保留 cookie）
            try:
                # 尝试访问根域以获取可能的 cookie（如果 session 为空）
                try:
                    if not self.session.cookies:
                        self.session.get("https://www.qidiy.com/", timeout=8)
                except Exception:
                    pass
                resp = self.session.get(url, headers=headers, timeout=20)
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                status = None
                try:
                    status = e.response.status_code
                except Exception:
                    try:
                        status = resp.status_code
                    except Exception:
                        status = None
                # 若为 403，且允许 cloudscraper 回退，则尝试使用 cloudscraper
                if status == 403 and self.use_cloudscraper_if_needed:
                    try:
                        import cloudscraper

                        scraper = cloudscraper.create_scraper()
                        resp = scraper.get(url, headers=headers, timeout=20)
                        resp.raise_for_status()
                    except Exception:
                        # 若 cloudscraper 不可用或仍失败，抛出原始错误
                        raise
                else:
                    raise

            # 确保使用合适的编码解析，优先使用 requests 的检测编码，避免出现乱码
            try:
                detected = getattr(resp, "apparent_encoding", None)
                if detected:
                    resp.encoding = detected
                else:
                    resp.encoding = resp.encoding or "utf-8"
            except Exception:
                resp.encoding = resp.encoding or "utf-8"

            return BeautifulSoup(resp.text, "html.parser")

        """主要爬取函数"""

        self.start.configure(state=DISABLED)
        self.chapter_input.configure(state=DISABLED)
        self.book_input.configure(state=DISABLED)

        log_update(f"已启动，解析URL：{chapter}\n")

        """URL解析"""
        """时间戳记录"""
        if not continue_patch:
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
            self.url = self.urlbb
            self.contents = self.backup.copy()
            self.midbackup = self.contents.copy()
            processed = 0
        try:
            """预处理"""

            log_update(f"[{int((time.time() - self.start_time)*1000)}]预处理中……\n")

            select_tag = get_soup(f"https://www.qidiy.com/book/{book}_99/")
            select_tag.find(
                "select", {"name": "pageselect"}
            )
            # 查找所有的 <option> 标签，并获取最后一个
            num = int(re.findall(r"\d+", str(select_tag.find_all("option")[-1]))[3])

            log_update(
                f"[{int((time.time() - self.start_time)*1000)}]本书共{num}章节\n"
            )

            l = 1
            r = math.ceil(num / 20)
            chapter = int(
                self.url.replace(f"https://www.qidiy.com/book/{book}/", "").replace(
                    ".html", ""
                )
            )

            # 先尝试右边界（最后一页），若命中则直接计算 start，否则再用二分查找
            found = False
            try:
                log_update(
                    f"[{int((time.time() - self.start_time)*1000)}]尝试右边界……第{r}页\n"
                )
                finding = get_soup(
                    f"https://www.qidiy.com/book/{book}_{r}/"
                ).find_all("ul", class_="section-list fix")[1]
                urls = [
                    int(tag["href"].replace(f"/book/{book}/", "").replace(".html", ""))
                    for tag in finding.find_all("a", href=True)
                ]
                if urls and urls[0] <= chapter <= urls[-1]:
                    start = r * 20 - (19 - urls.index(chapter))
                    found = True
                    log_update(
                        f"[{int((time.time() - self.start_time)*1000)}]右边界命中：第{r}页，start={start}\n"
                    )
                else:
                    log_update(
                        f"[{int((time.time() - self.start_time)*1000)}]右边界未命中，开始二分定位\n"
                    )
            except Exception:
                log_update(
                    f"[{int((time.time() - self.start_time)*1000)}]右边界检查失败，开始二分定位\n"
                )

            if not found:
                while l <= r:
                    mid = (l + r) // 2
                    log_update(
                        f"[{int((time.time() - self.start_time)*1000)}]正在定位……第{mid}页\n"
                    )

                    finding = get_soup(
                        f"https://www.qidiy.com/book/{book}_{mid}/"
                    ).find_all("ul", class_="section-list fix")[1]
                    urls = []
                    for tag in finding.find_all("a", href=True):
                        href = tag["href"]
                        urls.append(
                            int(href.replace(f"/book/{book}/", "").replace(".html", ""))
                        )
                    
                    time.sleep(1)

                    # 正确更新左右边界，避免 mid 不变导致的死循环
                    if chapter < urls[0]:
                        r = mid - 1
                        continue
                    elif chapter > urls[-1]:
                        l = mid + 1
                        continue
                    else:
                        start = mid * 20 - (19 - urls.index(chapter))
                        break

            self.all = num - start + 1
            log_update(
                f"[{int((time.time() - self.start_time)*1000)}]定位完成，需要爬取{self.all}章节\n"
            )
            self.all *= 2
            avg = 0

            """爬取"""
            while self.url and not self.url.endswith(f"/book/{book}/"):

                speed_time = time.time()

                if processed % 2 == 0:
                    self.backup = self.midbackup.copy()
                    self.midbackup = self.contents.copy()
                    self.urlbb = self.urlb
                    self.urlb = self.url

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
                processed += 1

                if processed % 20 == 0:
                    with open(f"output.txt", "w", encoding="utf-8") as f:
                        f.write("\n".join(self.backup))
                    log_update(
                        f"[{int((time.time() - self.start_time)*1000)}]第{processed}页已解析，已保存备份，当前URL：{self.url}\n",
                    )
                    icon = random.choice(ICONS_PROCESSING)
                    toast = Notification(
                        app_id="Novel Crawler",
                        title="爬取已备份",
                        msg=f"爬取中，已爬取{processed}页，已保存备份",
                        icon=icon,
                        duration="short",
                    )
                    toast.set_audio(audio.Default, loop=False)
                    toast.show()
                else:
                    log_update(
                        f"[{int((time.time() - self.start_time)*1000)}]第{processed}页已解析，当前URL：{self.url}\n",
                    )

                self.url = self.find_next(self.soup, self.url)

                time.sleep(1.2)

                speed_time = time.time() - speed_time
                avg = (avg * (processed - 1) + speed_time) / processed
                self.all -= 1
                hour = int(self.all * avg // 3600)
                minute = int(self.all * avg // 60) - hour * 60
                second = int(self.all * avg) - hour * 3600 - minute * 60
                self.etatime.configure(
                    text=f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"
                )
                self.etatime.update()

            log_update(
                f"[{int((time.time() - self.start_time)*1000)}]解析完成，开始写入文件……\n"
            )

            """写入文件"""
            with open(f"output.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.contents))

            log_update(
                f"[{int((time.time() - self.start_time)*1000)}]写入完成，任务完成。\n"
            )

            icon = random.choice(ICONS_SUCCESS)
            toast = Notification(
                app_id="Novel Crawler",
                title="爬取已完成",
                msg=f"爬取完成！保存文件于output.txt",
                icon=icon,
                duration="long",
            )
            toast.add_actions(
                label="查看",
                launch=r"file:///D:\codefile\File\FBOOK\reader\3.0\tool\patch",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            return
        except Exception as e:
            log_update(
                f"[{int((time.time() - self.start_time)*1000)}]爬取失败，正在保存已爬取内容……\n",
            )
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.backup))
            print(e)
            messagebox.showerror("错误", f"爬取失败，已爬取内容已保存，可稍后网络恢复继续爬取\n错误详情：{str(e)}")

            self.start.configure(
                text="CONTINUE",
                command=lambda: self.spatch(
                    self.book_input.get(), self.chapter_input.get(), continue_patch=True
                ),
                state=NORMAL,
            )
            self.start.update()
            self.etatime.configure(text="--:--:--")
            self.etatime.update()

            icon = random.choice(ICONS_FAILED)

            toast = Notification(
                app_id="Novel Crawler",
                title="爬取失败！",
                msg="爬取失败，已爬取内容已保存，可稍后网络恢复继续爬取",
                icon=icon,
                duration="long",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()

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
    Patcher()
    mainloop()
