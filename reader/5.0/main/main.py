"""
Reader 5 - UI
"""

from bs4 import BeautifulSoup
from threading import Thread
from tkinter import *
from tkinter import font as tkfont
from tkinter import filedialog
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

tk = Tk()

class ErrorAnalyzer:
    def __init__(self):
        self.error_codes = {
            0: "成功",
            1: "未知错误",
            2: "屏幕分辨率过低"
        }
    
    def translate_code(self, code):
        unit = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]
        hex_code = "0x" + unit[code // 16] + unit[code % 16]
        return hex_code

    def __call__(self, code):
        return f"{self.error_codes.get(code, '未知错误代码')}\n错误代码: {self.translate_code(code)}"

class ReaderUI:
    def __init__(self):
        self.preload_info()
        self.preload_config()
        self.preload_conditions()
        self.calculate_config()
        self.create_widgets()
    
    def preload_info(self):
        """获取系统屏幕信息"""
        self.screen_width = tk.winfo_screenwidth()
        self.screen_height = tk.winfo_screenheight()
    
    def preload_config(self):
        """设置初始UI配置"""

        # 窗口大小
        if self.screen_width >= 1920 and self.screen_height >= 1080:
            self.window_width = 1600
            self.window_height = 900
        elif self.screen_width >= 1366 and self.screen_height >= 768:
            self.window_width = 1280
            self.window_height = 720
        elif self.screen_width >= 1024 and self.screen_height >= 768:
            self.window_width = 768
            self.window_height = 432
        else:
            messagebox.showerror("错误", f"无法运行Reader 5\n{ERROR(2)}")
            sys.exit(2)

        # 字体（使用非等宽字体）
        self.font_text = tkfont.Font(family="HYWenHei-85W", size=15)
        self.font_title = tkfont.Font(family="HYWenHei-85W", size=15)
        self.font_status = tkfont.Font(family="HYWenHei-85W", size=12)
        self.font_hint = tkfont.Font(family="HYWenHei-85W", size=8)

        # 颜色
        self.color_bg = "#23272E"
        self.color_fg = "#C8C8C8"
        self.color_mid = "#767F89"
    
    def preload_conditions(self):

        self.page = 0
        self.page_total = 0
    
    def calculate_config(self):
        # 计算提示条长度，保证至少为1，避免窗口过窄导致负值
        block_width = self.font_hint.measure("█")
        line_width = self.font_hint.measure("|")
        space_width = self.font_hint.measure(" ")
        available_width = self.window_width - 20 - 2 * line_width
        self.hint_length = max(1, available_width // block_width)
        self.hint_block_width = block_width
        self.hint_line_width = line_width
        self.hint_space_width = max(1, space_width)
        self.hint_total_width = self.hint_length * block_width
    
    def create_widgets(self):
        """创建UI组件"""

        # 设置窗口基本属性
        tk.title("Reader 5")
        tk.geometry(f"{self.window_width}x{self.window_height}+{(self.screen_width - self.window_width) // 2}+{(self.screen_height - self.window_height) // 2}")
        tk.config(bg=self.color_bg)

        self.title = Label(
            text="READER 5",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_title,
        )
        self.title.place(x=10, y=10)

        self.status = Label(
            text="",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_status,
        )
        self.status.place(x=10, y=665)

        self.hint = Label(
            text="",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_hint,
        )
        self.hint.place(x=10, y=690)

        tk.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        """窗口调整大小时重新计算组件位置"""
        width = tk.winfo_width()
        height = tk.winfo_height()
        if width == self.screen_width and height == self.screen_height:
            return  # 忽略初始配置事件
        self.window_width = width
        self.window_height = height

        # 重新计算
        self.calculate_config()

        self.change_hint(self.page, self.page_total)
    
    def change_hint(self, current, total):
        """更新状态栏提示"""
        hint_unit = ["∅", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
        ratio = current / total if total > 0 else 0
        ratio = max(0.0, min(1.0, ratio))
        hint_unit_length = 8 * self.hint_length
        hint_interger = int(ratio * self.hint_length)
        hint_decimal = int((ratio * hint_unit_length) % 8)

        filled_width = hint_interger * self.hint_block_width
        if hint_decimal > 0:
            filled_width += self.font_hint.measure(hint_unit[hint_decimal])
        remaining_width = max(0, self.hint_total_width - filled_width)
        empty = remaining_width // self.hint_space_width
        if hint_decimal == 0:
            self.hint.config(text=f"|{hint_interger * hint_unit[8]}{' ' * empty}|")
        else:
            self.hint.config(text=f"|{hint_interger * hint_unit[8]}{hint_unit[hint_decimal]}{' ' * empty}|")

if __name__ == "__main__":
    global UI, ERROR
    ERROR = ErrorAnalyzer()
    UI = ReaderUI()
    tk.mainloop()
