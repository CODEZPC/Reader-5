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

        # 颜色
        self.color_bg = "#23272E"
        self.color_fg = "#C8C8C8"
        self.color_mid = "#767F89"
    
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
            font=self.font_status,
        )
        self.hint.place(x=10, y=690)


        tk.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        """窗口调整大小时重新计算组件位置"""
        if event.width == self.screen_width and event.height == self.screen_height:
            return  # 忽略初始配置事件
        self.screen_width = event.width
        self.screen_height = event.height

        # 重新计算标题位置
        pass

        tk.update_idletasks()

if __name__ == "__main__":
    global UI, ERROR
    ERROR = ErrorAnalyzer()
    UI = ReaderUI()
    tk.mainloop()
