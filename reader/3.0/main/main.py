"""
READER 3 - 程序入口
"""

from tkinter import Tk

from config import setup_logging
from reader import Reader


def main():
    """主函数：初始化日志、创建 Tk 根窗口、启动 Reader。"""
    # --- 日志初始化 ---
    setup_logging(".\\_internal\\reader.log")

    # --- 创建 tkinter 根窗口 ---
    tk = Tk()

    # --- 启动 Reader ---
    Reader(tk)

    # --- 进入主循环 ---
    tk.mainloop()


if __name__ == "__main__":
    main()
