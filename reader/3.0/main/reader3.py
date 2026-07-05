"""
READER 3
"""
"----------导入区----------"

from bs4 import BeautifulSoup
from threading import Thread
from tkinter import *
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from urllib.parse import urljoin
import glob
import logging
import math
import os
import random
import re
import requests
import struct
import shutil
import sys
import tempfile
import threading
import time
import fake_useragent

"----------日志配置区----------"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("reader.log", encoding="utf-8"), logging.StreamHandler()],
)

"----------全局变量区----------"

tk = Tk()
"tkinter窗口初始化(Reader 对象)"

DEFAULT = {
    "LINES_PER_PAGE": 26,  # 每页行数 31
    "CHARATERS_PER_LINE": 120,  # 每行字数 120
    "WINDOW_WIDTH": 1280,  # 窗口宽 1280
    "WINDOW_HEIGHT": 720,  # 窗口高 720
    "MENU_WIDTH": 100,  # 菜单宽 100
    "MENU_HEIGHT": 25,  # 菜单高 25
    "HINT_LENGTH": 77,  # 提示栏长 77
}
"部分默认配置"

CONFIG = {
    "LINES_PER_PAGE": 26,
    "CHARATERS_PER_LINE": 120,
    "WINDOW_WIDTH": 1280,
    "WINDOW_HEIGHT": 720,
    "MENU_WIDTH": 100,
    "MENU_HEIGHT": 25,
    "JUMP_WINDOW_WIDTH": 150,  # 跳转窗口宽 150
    "JUMP_WINDOW_HEIGHT": 40,  # 跳转窗口高 40
    "SELECT_WINDOW_WIDTH": 265,  # 选择窗口宽 265
    "SELECT_WINDOW_HEIGHT": 640,  # 选择窗口高 640
    "ENCODEINGS": ["gbk", "utf-8-sig", "utf-8"],  # 编码 GBK/UTF-8
    "HINT_L": "|",  # 提示左
    "HINT_R": "|",  # 提示右
    "HINT_P": "█",  # 提示全
    "HINT_Px": ["\u3000", "▏", "▎", "▍", "▌", "▋", "▊", "▉"],  # 提示半
    "HINT_LENGTH": 77,  # 提示栏长
    # ===以下为系统配置获取=== #
    "INFO_SCREEN_WIDTH": tk.winfo_screenwidth(),  # 屏幕宽
    "INFO_SCREEN_HEIGHT": tk.winfo_screenheight(),  # 屏幕高
    # ===以下为菜单显示=== #
    "EMPTY_TEXT": "--- no file open ---\n[ESC]",  # 空文件提示
    "MENU_OPTIONS": [
        "返回阅读",
        "打开文件",
        "转到页码",
        "重载",
        "内置书籍",
        "生成目录",
        "设置全屏",
        "切换颜色",
        # "导出",  # 此选项为开发者模式专用
        # "自定义指令",  # 此选项为开发者模式专用
        "关于",
        "赞助",
        "重启",
        "退出",
    ],  # 菜单选项
    "MENU_TITLE": "Menu",  # 菜单标题
    # ===以下为颜色配置=== #
    "COLOR_TITLE": ["#767F89", "#767F89", "#767F89"],
    "COLOR_CONTEXT": ["#90BFF5","#C8C8C8", "#23272E"],
    "COLOR_BACKGROUND": ["#23272E","#23272E", "#DEDEDE"],
    "THEME": 0,
}
"全局配置"

"----------全局函数区----------"

def merge_and_unpack(prefix: str = ".\\pack\\resources.bin", output_file: str = None):
    """
    合并分卷文件并执行解包操作（可选输出为bin）

    :param prefix: 分卷文件前缀（默认 resources.bin）
    :param output_file: 可选，指定合并后的文件路径，应为bin后缀
    :return: unpack() 函数的结果
    :raise -1: 未找到资源包
    """
    """
    parts: 分卷文件列表
    delete_temp: 是否删除临时文件
    temp_file: 临时文件对象
    """
    # 查找所有匹配的分卷文件（按数字排序）
    logging.info(f"搜索分卷文件: {prefix}*")
    parts = sorted(glob.glob(f"{prefix}[0-9][0-9][0-9]"), key=lambda x: int(x[-3:]))
    # 未找到资源包
    if not parts:
        logging.error("未找到资源包")
        return -1
    # 创建临时文件或使用指定输出路径
    delete_temp = False
    if not output_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        output_file = temp_file.name
        temp_file.close()
        delete_temp = True
    try:
        # 合并分卷文件
        with open(output_file, "wb") as out_f:
            for part in parts:
                with open(part, "rb") as in_f:
                    while chunk := in_f.read(8192):
                        out_f.write(chunk)
        # 执行解包操作
        return unpack(output_file)
    finally:
        # 清理临时文件
        if delete_temp and os.path.exists(output_file):
            os.unlink(output_file)


def unpack(input_bin):
    """
    解包

    :param input_bin: 包文件
    :type input_bin: binfile
    :return: 解压后文件
    """
    """
    result_dict: 解压结果字典
    file_count: 文件数量
    path_len: 路径长度
    rel_path: 相对路径
    file_size: 文件大小
    file_data: 文件内容
    """
    # 读取二进制文件
    result_dict = {}
    with open(input_bin, "rb") as bin_file:
        try:
            # 读取文件数量
            file_count = struct.unpack("I", bin_file.read(4))[0]
            for _ in range(file_count):
                # 读取路径长度和路径内容
                path_len = struct.unpack("I", bin_file.read(4))[0]
                rel_path = bin_file.read(path_len).decode("utf-8-sig")
                # 读取文件大小和内容
                file_size = struct.unpack("I", bin_file.read(4))[0]
                file_data = bin_file.read(file_size)
                # 添加到结果字典
                result_dict[rel_path] = file_data
        except struct.error as e:
            logging.error(f"解析二进制文件时出错: {str(e)}")
            logging.error("文件可能已损坏或格式不正确")
        except Exception as e:
            logging.error(f"读取文件时出错: {str(e)}")
    logging.info(f"解压完成，共 {len(result_dict)} 个文件")
    return result_dict


def unpack_resources(
    bin_prefix=".\\pack\\resources.bin", output_dir="extracted", keep_temp=False
):
    """
    解包并输出文件

    :param bin_prefix: 资源包前缀（默认 resources.bin）
    :param output_dir: 输出目录（默认 extracted）
    :param keep_temp: 是否保留临时文件（默认 False）
    :return: None
    """
    logging.info(f"解包资源包: {bin_prefix} -> {output_dir}")
    unpacker = BinUnpacker(bin_prefix, output_dir)
    try:
        # 判断是否是分卷文件
        if glob.glob(f"{bin_prefix}*") and not os.path.exists(bin_prefix):
            unpacker.merge_chunks()
            unpacker.unpack()
        else:
            # 如果是单个文件直接解包
            unpacker.unpack(bin_prefix)
        if not keep_temp:
            unpacker.cleanup()
    except Exception as e:
        logging.error(f"解包输出错误: {e}")
        if not keep_temp:
            unpacker.cleanup()


class Reader:
    def __init__(self):
        """
        启动函数

        定义主要变量
        """
        logging.info("==========READER LAUNCHED==========")
        self.conditions = {
            "reading": False,  # 阅读状态
            "loading": False,  # 加载状态
            "now": 0,  # 当前页
            "full": 0,  # 总页数
            "resource_active": True,  # 资源文件可用性
            "fullscreen": False,  # 全屏状态
            "load_speed": 0,  # 加载速度
        }
        self.change_fast = 0  # 切换速度
        self.change_time = 0  # 页码切换时间
        self.file_path = None  # 文件路径
        self.builtin = False  # 是否为内置书籍
        self.chapter_page = []  # 章节页码
        self.chapter_name = []  # 章节名称
        self.chapter_now = 0  # 当前章节
        self.dev = 0  # 开发者模式
        self.func = [
            lambda: self.close_menu(None),
            self.open_filet,
            self.turn_to_page,
            lambda: self.open_filet(
                file_path=self.file_path, built=self.builtin, reload=True
            ),
            self.builtin_select,
            self.generate_contents,
            self.change_full_screen,
            self.change_color,
            self.about,
            lambda: os.system("start https://github.com/CODEZPC/CODEZPC/blob/main/README.md"),
            self.restart,
            self.quit,
        ]  # 菜单功能
        self.load_ui()

    def about(self):
        """
        关于
        """
        self.book = [
            "CODEZPC's READER\n",
            "  Version: 4.2\n",
            "  Author: CODEZPC\n",
            "  Sponsor: https://github.com/CODEZPC/CODEZPC/blob/main/README.md\n",
        ]
        self.conditions["full"] = 1
        self.conditions["now"] = 1
        self.conditions["reading"] = True
        self.update_page(1, check_chapter=2)
        self.close_menu(None)

    def builtin_select(self):
        """
        内置书籍选择
        """
        if not self.conditions["resource_active"]:
            messagebox.showwarning(
                "警告", "未找到资源文件，请重新下载，否则无法使用内置书籍。"
            )
            return
        self.select = Toplevel(tk)
        self.select.focus_force()
        self.select.geometry(
            f"""{CONFIG["SELECT_WINDOW_WIDTH"]}x{CONFIG["SELECT_WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["SELECT_WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["SELECT_WINDOW_HEIGHT"]) / 2)}"""
        )  # 居中
        self.select.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]])
        empty = Label(
            self.select, text="", font=("Jetbrains Mono", 5), fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]], bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]]
        )
        empty.pack()
        dashboard = Listbox(
            self.select,
            font=("Jetbrains Mono", 10),
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            selectmode=BROWSE,
            width=30,
            height=33,
            relief=FLAT,
        )
        dashboard.pack()
        showlist = eval(self.builtin_books["show"].decode("utf-8-sig"))
        reallist = eval(self.builtin_books["list"].decode("utf-8-sig"))
        for i in showlist:
            dashboard.insert(END, i)
        enter = Button(
            self.select,
            text="GO",
            font=("Jetbrains Mono", 10),
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            width=25,
            relief=FLAT,
            command=lambda: self.open_filet(
                reallist[showlist.index(dashboard.get(ACTIVE))], True
            ),
        )
        enter.pack()

    def change_color(self):
        global tk
        CONFIG["THEME"] = 0 if CONFIG["THEME"] == 2 else CONFIG["THEME"] + 1
        tk.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]])
        self.title.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]], fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]])
        self.text.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]], fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]])
        self.status.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]], fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]])
        self.menu.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]], fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]])
        self.hint.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]], fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]])
        logging.info("颜色改变")

    def change_full_screen(self):
        """
        切换全屏
        """
        self.conditions["fullscreen"] = not self.conditions["fullscreen"]
        tk.attributes("-fullscreen", self.conditions["fullscreen"])
        self.hint.place_forget()
        self.status.place_forget()
        if self.conditions["fullscreen"]:
            CONFIG["WINDOW_WIDTH"] = CONFIG["INFO_SCREEN_WIDTH"]
            CONFIG["WINDOW_HEIGHT"] = CONFIG["INFO_SCREEN_HEIGHT"]
        else:
            CONFIG["WINDOW_WIDTH"] = DEFAULT["WINDOW_WIDTH"]
            CONFIG["WINDOW_HEIGHT"] = DEFAULT["WINDOW_HEIGHT"]
        CONFIG["HINT_LENGTH"] = (CONFIG["WINDOW_WIDTH"] - 48) // 16
        CONFIG["CHARATERS_PER_LINE"] = (CONFIG["WINDOW_WIDTH"] - 80) // 10
        CONFIG["LINES_PER_PAGE"] = (CONFIG["WINDOW_HEIGHT"] - 100) // 24
        CONFIG["MENU_WIDTH"] = (CONFIG["WINDOW_WIDTH"] - 80) // 12
        CONFIG["MENU_HEIGHT"] = int((CONFIG["WINDOW_HEIGHT"] - 100) / 23.84)
        self.status.place(x=10, y=CONFIG["WINDOW_HEIGHT"] - 55)
        self.hint.place(x=10, y=CONFIG["WINDOW_HEIGHT"] - 30)
        self.text.configure(
            width=CONFIG["CHARATERS_PER_LINE"], height=CONFIG["LINES_PER_PAGE"]
        )
        self.menu.configure(
            width=CONFIG["MENU_WIDTH"], height=CONFIG["MENU_HEIGHT"]
        )
        self.open_filet(file_path=self.file_path, built=self.builtin, reload=True)
        tk.focus_force()

    def change_menu(self, event, title, option):
        """
        显示菜单光标

        :param title: 菜单标题
        :type title: str
        :param option: 选项
        :type option: list -> str
        :return: 显示的文本
        :rtype: str
        """
        reply = title
        for i in range(len(option)):
            if i == self.pin:
                reply += "\n" + ">  " + option[i] + "  <"
            else:
                reply += "\n" + option[i]
        self.menu.configure(text=reply)
        return reply

    def change_page(self, delta):
        """
        切换页

        :param delta: 差
        :type delta: int
        """
        if not self.conditions["reading"] or self.conditions["loading"]:
            return
        if time.time() - self.change_time <= 0.1:
            self.change_fast += 1
            if self.change_fast == 50:
                self.title.configure(fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]])
                self.text.configure(fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]])
                tk.bind("<KeyRelease>", self.change_page_ended)
            if self.change_fast >= 50:
                speed = (self.change_fast - 50) // 30
                speed = int(math.pow(2, speed))
                if speed >= 32:
                    speed = 32
                if delta > 0:
                    # 向后翻页，切换到下一章
                    if self.chapter_now < len(self.chapter_name) - speed:
                        self.chapter_now += speed
                        self.conditions["now"] = self.chapter_page[self.chapter_now]
                    else:
                        self.conditions["now"] = 1
                        self.chapter_now = 0
                else:
                    # 向前翻页，切换到上一章
                    if self.chapter_now > speed - 1:
                        self.chapter_now -= speed
                        self.conditions["now"] = self.chapter_page[self.chapter_now]
                    else:
                        self.conditions["now"] = self.conditions["full"]
                        self.chapter_now = len(self.chapter_name) - 1
                self.title.configure(text=f"×{speed}  " + self.chapter_name[self.chapter_now])
                self.update_page(self.conditions["now"], check_chapter=0)
                self.change_time = time.time()
                return
        else:
            self.change_fast = 0
        self.conditions["now"] += delta
        if self.conditions["now"] > self.conditions["full"]:
            self.conditions["now"] = 1
            self.update_page(self.conditions["now"], check_chapter=2)
        elif self.conditions["now"] == 0:
            self.conditions["now"] = self.conditions["full"]
            self.update_page(self.conditions["now"], check_chapter=2)
        else:
            self.update_page(self.conditions["now"])
        self.change_time = time.time()
    
    def change_page_ended(self, event):
        """
        切换页结束
        """
        self.title.configure(fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]])
        self.text.configure(fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]])
        self.title.configure(text=self.chapter_name[self.chapter_now])
        tk.unbind("<KeyRelease>")

    def change_pin(self, title, option, delta):
        """
        改变光标位置

        :param title: 菜单标题
        :type title: str
        :param option: 选项
        :type param: list -> str
        :param delta: 差
        :type delta: int
        """
        self.pin += delta
        if self.pin >= len(option):
            self.pin = 0
        elif self.pin < 0:
            self.pin = len(option) - 1
        self.change_menu(None, title, option)

    def close_menu(self, event):
        """
        关闭菜单
        """
        tk.unbind("<Escape>")
        tk.unbind("<Up>")
        tk.unbind("<Down>")
        tk.unbind("<Return>")
        tk.bind("<Escape>", self.open_menu)
        if self.conditions["reading"]:
            tk.bind("<Left>", lambda event: self.change_page(-1))
            tk.bind("<Right>", lambda event: self.change_page(1))
        logging.debug("Close")
        if self.conditions["reading"]:
            self.menu.place_forget()
        else:
            self.menu.configure(text=CONFIG["EMPTY_TEXT"])

    def custom(self):
        self.custom_bar = Toplevel(tk)
        self.custom_bar.focus_force()
        self.custom_bar.geometry(
            f"""500x40+{int((CONFIG["INFO_SCREEN_WIDTH"] - 500) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - 40) / 2)}"""
        )  # 居中
        self.custom_bar.resizable(False, False)
        self.custom_bar.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]])
        self.command = Entry(
            self.custom_bar,
            font=("Jetbrains Mono", 10),
            width=60,
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            relief=FLAT,
        )
        self.command.pack()
        enter = Button(
            self.custom_bar,
            text="GO",
            font=("Jetbrains Mono", 10),
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            relief=FLAT,
            command=self.run,
        )
        enter.pack()

    def devlop(self, event):
        password = "CODESTUDIO"
        if event.char == password[self.dev]:
            self.dev += 1
            if self.dev == 10:
                tk.unbind("<KeyPress>")
                CONFIG["EMPTY_TEXT"] = "--- no file open ---\n[ESC]\nDEVLOP MODE ON"
                CONFIG["MENU_TITLE"] = "Menu [DEVLOP]"
                CONFIG["MENU_OPTIONS"].insert(
                    9,
                    "             CUSTOM COMMAND   自定义指令                  ",
                )
                CONFIG["MENU_OPTIONS"].insert(
                    9,
                    "                     EXPORT   导出                       ",
                )
                self.func.insert(9, self.custom)
                self.func.insert(9, unpack_resources)
                self.menu.configure(text=CONFIG["EMPTY_TEXT"])
        else:
            self.dev = 0

    def EMPTY(self):
        """
        空置函数
        """
        pass

    def generate_contents(self):
        """
        生成目录
        """
        with open("Contents.txt", "w", encoding="utf-8-sig") as f:
            f.write("目录:\n")
            for i in range(len(self.chapter_name)):
                f.write(f"  {self.chapter_name[i]} - {self.chapter_page[i]}\n")

    def getpage(
        self,
        file_path,
        encodeings=["utf-8-sig", "gbk", "gb2312"],
        charaters_per_line=0,
        lines_per_page=0,
        builtin=False,
    ):
        """
        分页

        :param file_path: 文件路径
        :type file_path: str
        :param encodeings: 文件编码
        :type encodeings: list -> str
        :param charaters_per_line: 每页行数，默认为CONFIG
        :type charaters_per_line: int
        :param lines_per_page: 每行字数，默认为CONFIG
        :type lines_per_page: int
        :param builtin: 是否为内置资源包，默认为False
        :type builtin: bool
        :return: 总页码，解析的行列表，章节页数，章节标题
        :rtype: tuple -> (int, list -> str, list -> int, list -> str)
        :raise -1: 没有文件路径
        :raise -2: 文件解码失败
        :raise -3: 文件没有内容
        """
        logging.info(f"开始分页处理: file_path={file_path if not builtin else 'builtin'}, builtin={builtin}")
        logging.debug(f"编码列表: {encodeings}")
        charaters_per_line = CONFIG["CHARATERS_PER_LINE"]
        lines_per_page = CONFIG["LINES_PER_PAGE"]
        self.conditions["loading"] = True
        self.need_process_lines = 1
        # 初始化章节追踪列表
        chapter_page = []
        chapter_title = []
        # 没有文件路径
        if not file_path:
            logging.error("没有提供文件路径")
            self.conditions["loading"] = False
            return -1
        # 文件内容
        content = None
        # 文件读取逻辑
        if not builtin:
            logging.info("尝试读取外部文件")
            # 尝试解码
            for encoding in encodeings:
                try:
                    logging.debug(f"尝试编码: {encoding}")
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.readlines()
                    logging.info(f"成功使用编码 {encoding} 读取文件")
                    break
                except UnicodeDecodeError:
                    logging.debug(f"编码 {encoding} 解码失败")
                    continue
            else:
                logging.error("所有编码尝试失败")
                self.conditions["loading"] = False
                return -2
        else:
            logging.info("处理内置资源内容")
            content = file_path.split("\n")

        try:
            wrap_font = font.Font(font=self.text.cget("font"))
        except Exception:
            wrap_font = font.Font(family="黑体", size=15)

        char_width_cache = {}

        def get_char_width(char):
            if char not in char_width_cache:
                char_width_cache[char] = wrap_font.measure(char)
            return char_width_cache[char]

        # 行处理函数
        def process_line(line, width=CONFIG["WINDOW_WIDTH"] - 80):
            current_line = line.rstrip("\n")
            remaining_width = width
            index_of_char = 0
            for char in current_line:
                remaining_width -= get_char_width(char)
                if remaining_width < 0:
                    if index_of_char == 0:
                        return current_line[:1] + "\n", current_line[1:]
                    new_line = current_line[:index_of_char] + "\n"
                    remaining_content = current_line[index_of_char:]
                    return new_line, remaining_content
                index_of_char += 1
            return (current_line + ("\n" if line.endswith("\n") else "")), None

        # 主处理循环
        self.processed_orginal_lines = 0
        self.need_process_lines = len(content)
        self.conditions["full"] = self.need_process_lines
        processed_lines = []
        current_processed_count = 0
        line_idx = 0
        for line_idx, line in enumerate(content):
            a = time.time()
            # 检测章节开始
            if line.strip() and not line.startswith((" ", "\n", "	")):
                # 计算当前页剩余行数
                remaining_lines = lines_per_page - (
                    current_processed_count % lines_per_page
                )
                # 记录章节信息（在填充空白行前）
                current_page = (current_processed_count // lines_per_page) + (
                    2 if current_processed_count % lines_per_page != 0 else 1
                )
                chapter_page.append(current_page)
                chapter_title.append(line.strip())
                if remaining_lines != lines_per_page:
                    padding = remaining_lines
                    processed_lines.extend(["\n"] * padding)
                    current_processed_count += padding
            # 处理单行拆分
            while True:
                new_line, remaining = process_line(line)
                processed_lines.append(new_line.rstrip() + "\n")
                current_processed_count += 1
                if not remaining:
                    break
                line = remaining
            # 每行之间插入一个空行
            processed_lines.append("\n")
            current_processed_count += 1
            self.processed_orginal_lines += 1
            self.conditions["load_speed"] = (
                self.conditions["load_speed"] * (self.processed_orginal_lines - 1)
                + time.time()
                - a
            ) / self.processed_orginal_lines
        lines = processed_lines
        # 计算页码
        full = math.ceil(len(lines) / lines_per_page)
        chapter_page.append(99999999)
        self.conditions["loading"] = False
        if full == 0:
            return -3
        return full, lines, chapter_page, chapter_title

    def load_ui(self):
        """
        UI加载
        """
        # 内置资源加载
        self.builtin_books = merge_and_unpack(prefix=".\\pack\\resources.bin")
        if self.builtin_books == -1:
            messagebox.showwarning(
                "警告", "未找到资源文件，请重新下载，否则无法使用内置书籍。"
            )
            self.conditions["resource_active"] = False
        # 居中
        tk.geometry(
            f"""{CONFIG["WINDOW_WIDTH"]}x{CONFIG["WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["WINDOW_HEIGHT"]) / 2)}"""
        )
        # 禁止缩放
        tk.resizable(False, False)
        # 标题
        tk.title("CODEZPC's READER")
        # 背景颜色
        tk.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]])
        # 里标题
        self.title = Label(
            text="CODEZPC's READER",
            fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            font=("JetBrains Mono", 15),
        )
        self.title.place(x=10, y=10)
        # 文本显示
        self.text = Label(
            text="",
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            width=CONFIG["CHARATERS_PER_LINE"],
            height=CONFIG["LINES_PER_PAGE"],
            font=("HYWenHei-85W", 15),
            justify="left",
            anchor="nw",
        )
        self.text.place(x=40, y=40)
        # 菜单
        self.menu = Label(
            text=CONFIG["EMPTY_TEXT"],
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            width=CONFIG["MENU_WIDTH"],
            height=CONFIG["MENU_HEIGHT"],
            font=("Jetbrains Mono", 15),
        )
        self.menu.place(x=40, y=40)
        # 状态栏
        self.status = Label(
            text="",
            fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            font=("HYWenHei-85W", 12),
        )
        self.status.place(x=10, y=665)
        # 操作栏
        self.hint = Label(
            text="",
            fg=CONFIG["COLOR_TITLE"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            font=("HYWenHei-85W", 12),
        )
        self.hint.place(x=10, y=690)
        # 按键绑定
        tk.bind("<Escape>", self.open_menu)
        tk.bind("<KeyPress>", self.devlop)

    def open_file(self, file_path=None, built=False, reload=False):
        """
        打开文件

        :param file_path: 文件路径
        :type file_path: str
        :param built: 是否为内置书籍，默认为False
        :type built: bool
        :param reload: 是否为重载，默认为False
        :type reload: bool
        """
        logging.info(f"开始打开文件: file_path={file_path}, built={built}, reload={reload}")
        if not file_path:
            if reload:
                logging.info("重载操作，跳过文件选择")
                return
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("Text Files(Suggest)", ("*.txt")),
                    (
                        "Code(Render err)",
                        "*.py;*.cpp;*.c;*.json;*.java;*.js;*.md;*.log",
                    ),
                ]
            )
            if not file_path:
                logging.info("用户取消了文件选择")
            else:
                logging.info(f"用户选择了文件: {file_path}")
            tmp = self.getpage(file_path)
            self.builtin = False
        elif built:
            logging.info(f"打开内置书籍: {file_path}")
            tmp = self.getpage(
                self.builtin_books[file_path].decode("utf-8-sig"), builtin=True
            )
            self.builtin = True
        else:
            logging.info(f"直接打开文件: {file_path}")
            tmp = self.getpage(file_path)
            self.builtin = False
        if tmp == -1:
            logging.error("未选择文件错误")
            messagebox.showerror("Error", "No file selected.")
            self.conditions["reading"] = False
            self.conditions["loading"] = False
            self.open_menu(None)
            self.close_menu(None)
            self.hint.configure(text="")
            self.status.configure(text="")
        elif tmp == -2:
            logging.error("文件解码错误")
            messagebox.showerror("Error", "Cannot decode file.")
            self.conditions["reading"] = False
            self.conditions["loading"] = False
            self.open_menu(None)
            self.close_menu(None)
            self.hint.configure(text="")
            self.status.configure(text="")
        elif tmp == -3:
            logging.error("空文件错误")
            messagebox.showerror("Error", "File is empty.")
            self.conditions["reading"] = False
            self.conditions["loading"] = False
            self.open_menu(None)
            self.close_menu(None)
            self.hint.configure(text="")
            self.status.configure(text="")
        else:
            logging.info(f"成功打开文件: {file_path}, 总页数: {tmp[0]}, 章节数: {len(tmp[3])}")
            self.file_path = file_path
            self.conditions["now"] = 1
            self.conditions["full"] = tmp[0]
            self.book = tmp[1]
            self.chapter_page = tmp[2]
            self.chapter_name = tmp[3]
            self.update_page(1, check_chapter=2)
            self.close_menu(None)

    def open_filet(self, file_path=None, built=False, reload=False):
        self.need_process_lines = 1
        self.processed_orginal_lines = 0
        if built and hasattr(self, "select"):
            self.select.destroy()
        self.conditions["loading"] = True

        # 初始显示加载信息
        self.conditions["full"] = 1
        self.conditions["now"] = 1
        self.conditions["reading"] = True
        if not file_path:
            if reload:
                self.conditions["reading"] = False
                self.conditions["loading"] = False
                return

        # 启动加载线程
        thread = threading.Thread(
            target=self.open_file, args=(file_path, built, reload)
        )
        thread.daemon = True
        thread.start()

        # 定期检查进度并更新UI
        def check_progress():
            if self.conditions["loading"]:
                # 更新加载状态
                self.conditions["now"] = self.processed_orginal_lines
                t = int(
                    (self.need_process_lines - self.processed_orginal_lines)
                    * self.conditions["load_speed"]
                )
                self.book = (
                    [f"Importing File...(Cauculating...)"]
                    if self.conditions["now"] == 0
                    else [
                        f"Loading File...({self.processed_orginal_lines}/{self.need_process_lines} | ETA {t // 60}:{'0' if t % 60 < 10 else ''}{t % 60})"
                    ]
                )
                self.update_page(1, check_chapter=0)
                tk.after(70, check_progress)

        tk.after(70, check_progress)
        self.close_menu(None)

    def open_menu(self, event):
        """
        打开菜单
        """
        if self.conditions["loading"]:
            return
        self.menu.place_forget()
        self.menu.place(x=40, y=40)
        title = CONFIG["MENU_TITLE"]
        option = CONFIG["MENU_OPTIONS"]
        self.pin = 0
        tk.unbind("<Escape>")
        tk.unbind("<Left>")
        tk.unbind("<Right>")
        tk.bind("<Escape>", self.close_menu)
        logging.debug("Open")
        tk.bind("<Up>", lambda event: self.change_pin(title, option, -1))
        tk.bind("<Down>", lambda event: self.change_pin(title, option, 1))
        tk.bind("<Return>", lambda event: self.func[self.pin]())
        self.change_menu(None, title, option)

    def quit(self):
        """
        退出程序
        """
        logging.info("正在退出程序...")
        tk.destroy()
        logging.info("程序已退出")
        quit()

    def restart(self):
        logging.info("正在重启程序...")
        python = sys.executable
        logging.info(f"使用Python解释器路径: {python}")
        os.execl(python, python, *sys.argv)
        logging.info("程序已重启")

    def run(self):
        logging.info(f"尝试执行{self.command.get()}")
        try:
            eval(self.command.get())
        except Exception as e:
            messagebox.showerror(f"出现错误！", f"{e}")
            logging.error(f"自定义指令错误：{e}")
        else:
            logging.info(f"自定义指令执行成功，返回{eval(self.command.get())}")

    def save(self):
        target_page = int(self.entry.get())
        logging.info(f"尝试跳转到页码: {target_page}, 总页数: {self.conditions['full']}")
        if 1 <= target_page <= self.conditions["full"]:
            logging.info(f"页码验证通过, 跳转到第{target_page}页")
            self.conditions["now"] = target_page
            self.jumping.destroy()
            self.update_page(self.conditions["now"], check_chapter=2)
            self.close_menu(None)
            logging.info(f"成功跳转到第{target_page}页")
        else:
            logging.warning(f"无效页码: {target_page}, 允许范围: 1-{self.conditions['full']}")
    
    def show_chapter(self, event):
        """
        显示章节
        """
        self.menu.configure(text=self.title.cget('text'))
        self.menu.place_forget()
        self.menu.place(x=40, y=40)

    def turn_to_page(self):
        """
        跳转页
        """
        logging.info("打开页码跳转窗口")
        self.jumping = Toplevel(tk)
        self.jumping.focus_force()
        self.jumping.geometry(
            f"""{CONFIG["JUMP_WINDOW_WIDTH"]}x{CONFIG["JUMP_WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["JUMP_WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["JUMP_WINDOW_HEIGHT"]) / 2)}"""
        )  # 居中
        self.jumping.configure(bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]])
        self.entry = Entry(
            self.jumping,
            font=("Jetbrains Mono", 10),
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            relief=FLAT,
        )
        self.entry.pack()
        enter = Button(
            self.jumping,
            text="GO",
            font=("Jetbrains Mono", 10),
            fg=CONFIG["COLOR_CONTEXT"][CONFIG["THEME"]],
            bg=CONFIG["COLOR_BACKGROUND"][CONFIG["THEME"]],
            relief=FLAT,
            command=self.save,
        )
        enter.pack()
        logging.debug("页码跳转窗口已创建")

    def update_page(self, page, check_chapter=1):
        """
        显示页

        :param page: 要显示的页码
        :type page: int
        :param check_chapter: 章节检查，默认为1
        :type check_chapter: int in [0 -> OFF, 1 -> LR, 2 -> FULL]
        """
        show = ""
        for i in range(
            (page - 1) * CONFIG["LINES_PER_PAGE"], page * CONFIG["LINES_PER_PAGE"]
        ):
            try:
                show += self.book[i]
            except IndexError:
                show += "\n"
        self.text.configure(text=show)
        self.status.configure(
            text=f"第{self.conditions['now']}/{self.conditions['full']}页 {round((self.conditions['now']/self.conditions['full'])*100,3):.3f}%"
        )
        le = int(
            math.floor(
                CONFIG["HINT_LENGTH"]
                * 8
                * self.conditions["now"]
                / self.conditions["full"]
            )
        )
        length = le // 8
        self.hint.configure(
            text=CONFIG["HINT_L"]
            + length * CONFIG["HINT_P"]
            + (
                CONFIG["HINT_Px"][le % 8]
                if self.conditions["now"] != self.conditions["full"]
                else ""
            )
            + "\u3000" * (CONFIG["HINT_LENGTH"] - (length + 1))
            + CONFIG["HINT_R"]
        )
        if check_chapter == 2:
            for i in range(len(self.chapter_name)):
                if page >= self.chapter_page[i] and page < self.chapter_page[i + 1]:
                    self.title.configure(text=self.chapter_name[i])
                    self.chapter_now = i
                    break
        elif check_chapter == 1:
            if self.chapter_now < len(self.chapter_name) - 1:
                if page >= self.chapter_page[self.chapter_now + 1]:
                    self.title.configure(text=self.chapter_name[self.chapter_now + 1])
                    self.chapter_now += 1
            if self.chapter_now >= 0:
                if page < self.chapter_page[self.chapter_now]:
                    self.title.configure(text=self.chapter_name[self.chapter_now - 1])
                    self.chapter_now -= 1


class BinUnpacker:
    def __init__(self, bin_prefix, output_dir="extracted"):
        self.bin_prefix = bin_prefix
        self.output_dir = output_dir
        self.merged_file = f"{bin_prefix}_merged.bin"

    def merge_chunks(self):
        """合并分卷文件"""
        chunk_files = sorted(glob.glob(f"{self.bin_prefix}*"))
        if not chunk_files:
            raise FileNotFoundError(f"No files found with prefix '{self.bin_prefix}'")

        logging.info(f"找到 {len(chunk_files)} 个分卷文件，开始合并...")

        with open(self.merged_file, "wb") as merged:
            for chunk in chunk_files:
                logging.info(f"处理分卷: {chunk}")
                with open(chunk, "rb") as f:
                    shutil.copyfileobj(f, merged)

        logging.info(f"合并完成: {self.merged_file}")
        return self.merged_file

    def unpack(self, bin_file=None):
        """解包二进制文件"""
        bin_file = bin_file or self.merged_file

        if not os.path.exists(bin_file):
            raise FileNotFoundError(f"文件不存在: {bin_file}")

        os.makedirs(self.output_dir, exist_ok=True)

        logging.info(f"开始解包: {bin_file} -> {self.output_dir}")

        with open(bin_file, "rb") as f:
            # 读取文件数量
            file_count = struct.unpack("I", f.read(4))[0]
            logging.info(f"包含 {file_count} 个文件")

            for i in range(file_count):
                # 读取路径长度和路径
                path_len = struct.unpack("I", f.read(4))[0]
                rel_path = f.read(path_len).decode("utf-8")

                # 读取文件大小和内容
                file_size = struct.unpack("I", f.read(4))[0]
                file_data = f.read(file_size)

                # 创建目标路径
                full_path = os.path.join(self.output_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # 写入文件
                with open(full_path, "wb") as out_file:
                    out_file.write(file_data)

                logging.info(f"解包: {rel_path} ({file_size} 字节)")

        logging.info(f"解包完成! 共解压 {file_count} 个文件到 {self.output_dir}")

    def cleanup(self):
        """清理合并的临时文件"""
        if os.path.exists(self.merged_file):
            os.remove(self.merged_file)
            logging.info(f"已清理临时文件: {self.merged_file}")


if __name__ == "__main__":
    # 启动实例
    Reader()
    tk.mainloop()
