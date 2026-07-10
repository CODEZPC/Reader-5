"""
READER 3 - 核心阅读器模块
包含 Reader 类及其所有 UI 与阅读逻辑。
"""

import gc
import logging
import math
import os
import sys
import threading
import time
from tkinter import *
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox

from config import DEFAULT, make_default_config, BOSS_KEY_COMBO, BOSS_KEY_DISGUISE_TITLE
from utils import merge_and_unpack, unpack_resources


class Reader:
    """小说阅读器主类，管理窗口、分页、章节、菜单等全部 UI 与状态。"""

    def __init__(self, tk_instance: Tk):
        """
        启动函数

        :param tk_instance: 外部传入的 Tk 根窗口
        """
        logging.info("==========READER LAUNCHED==========")

        # 全局引用
        self.tk = tk_instance

        # --- 状态 ---
        self.conditions = {
            "reading": False,
            "loading": False,
            "now": 0,
            "full": 0,
            "resource_active": True,
            "fullscreen": False,
            "load_speed": 0,
        }

        # --- 快速翻页 ---
        self.change_fast = 0
        self.change_time = 0

        # --- 文件信息 ---
        self.file_path = None
        self.builtin = False
        self.book = []
        self.chapter_page = []
        self.chapter_name = []
        self.chapter_now = 0

        # --- 老板键 ---
        self.boss_key_active = False
        self._boss_saved_title = "CODEZPC's READER"

        # --- 开发者模式 ---
        self.dev = 0
        self.dev_password = "CODESTUDIO"

        # --- 初始化运行时配置 ---
        self.CONFIG = make_default_config(self.tk)
        # 初始化时根据 DEFAULT 计算一次派生值
        self._apply_dimensions()

        # --- 菜单功能表（与 MENU_OPTIONS 一一对应）---
        self.func = [
            lambda: self.close_menu(None),         # 返回阅读
            self.open_filet,                        # 打开文件
            self.turn_to_page,                      # 转到页码
            lambda: self.open_filet(                # 重载
                file_path=self.file_path, built=self.builtin, reload=True
            ),
            self.builtin_select,                    # 内置书籍
            self.generate_contents,                 # 生成目录
            self.change_full_screen,                # 设置全屏
            self.change_resolution,                 # 修改分辨率
            self.change_color,                      # 切换颜色
            self.about,                             # 关于
            lambda: os.system(                      # 赞助
                "start https://github.com/CODEZPC/CODEZPC/blob/main/README.md"
            ),
            self.restart,                           # 重启
            self.quit,                              # 退出
        ]

        # --- 加载 UI ---
        self.tk.bind("<Key>", self.devlop)
        self.load_ui()

    # ==================== 派生尺寸计算 ====================

    def _apply_dimensions(self):
        """根据当前 WINDOW_WIDTH / WINDOW_HEIGHT 重新计算所有派生尺寸。"""
        cfg = self.CONFIG
        cfg["HINT_LENGTH"] = (cfg["WINDOW_WIDTH"] - 48) // 16
        cfg["CHARATERS_PER_LINE"] = (cfg["WINDOW_WIDTH"] - 80) // 10
        cfg["LINES_PER_PAGE"] = (cfg["WINDOW_HEIGHT"] - 100) // 24
        cfg["MENU_WIDTH"] = (cfg["WINDOW_WIDTH"] - 80) // 12
        cfg["MENU_HEIGHT"] = int((cfg["WINDOW_HEIGHT"] - 100) / 23.84)
        logging.debug(
            f"尺寸重算: {cfg['WINDOW_WIDTH']}x{cfg['WINDOW_HEIGHT']}, "
            f"每行{cfg['CHARATERS_PER_LINE']}字, 每页{cfg['LINES_PER_PAGE']}行"
        )

    # ==================== UI 加载 ====================

    def load_ui(self):
        """创建并布局所有 UI 组件。"""
        cfg = self.CONFIG
        logging.info("开始加载 UI 组件...")

        # --- 内置资源加载 ---
        self.builtin_books = merge_and_unpack(prefix=".\\_internal\\pack\\resources.bin")
        if self.builtin_books == -1:
            logging.warning("未找到资源文件，内置书籍功能不可用")
            messagebox.showwarning(
                "警告", "未找到资源文件，请重新下载，否则无法使用内置书籍。"
            )
            self.conditions["resource_active"] = False
        else:
            logging.info(f"成功加载 {len(self.builtin_books)} 个内置资源条目")

        # --- 主窗口 ---
        self.tk.geometry(
            f"{cfg['WINDOW_WIDTH']}x{cfg['WINDOW_HEIGHT']}"
            f"+{int((cfg['INFO_SCREEN_WIDTH'] - cfg['WINDOW_WIDTH']) / 2)}"
            f"+{int((cfg['INFO_SCREEN_HEIGHT'] - cfg['WINDOW_HEIGHT']) / 2)}"
        )
        self.tk.resizable(False, False)
        self.tk.title("CODEZPC's READER")
        self.tk.iconbitmap(".\\_internal\\CR.ico")
        self.tk.configure(bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])

        # --- 标题标签 ---
        self.title = Label(
            text="CODEZPC's READER",
            fg=cfg["COLOR_TITLE"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            font=("HYWenHei-85W", 15),
        )
        self.title.place(x=10, y=10)

        # --- 文本显示区 ---
        self.text = Label(
            text=cfg["EMPTY_TEXT"],
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            width=cfg["CHARATERS_PER_LINE"],
            height=cfg["LINES_PER_PAGE"],
            font=("HYWenHei-85W", 15),
            justify="left",
            anchor="nw",
        )
        self.text.place(x=40, y=40)

        # --- 状态栏 ---
        self.status = Label(
            text="",
            fg=cfg["COLOR_TITLE"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            font=("HYWenHei-85W", 12),
        )
        self.status.place(x=10, y=cfg["WINDOW_HEIGHT"] - 55)

        # --- 操作提示栏 ---
        self.hint = Label(
            text="",
            fg=cfg["COLOR_TITLE"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            font=("HYWenHei-85W", 12),
        )
        self.hint.place(x=10, y=cfg["WINDOW_HEIGHT"] - 30)

        # --- 菜单面板（全屏覆盖）---
        self.menu_frame = Frame(
            self.tk,
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
        )

        # 左侧按钮面板（垂直居中）
        self.menu_left_panel = Frame(
            self.menu_frame,
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
        )
        self.menu_left_panel.pack(side="left", fill="y", padx=(80, 5))

        # 顶部弹簧使按钮垂直居中
        top_spacer = Frame(self.menu_left_panel, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        top_spacer.pack(expand=True)

        self.btn_container = Frame(
            self.menu_left_panel, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]]
        )
        self.btn_container.pack(expand=False)

        # 中间伸缩弹簧（将右侧面板推至远端）
        self.menu_center_spacer = Frame(
            self.menu_frame, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]]
        )
        self.menu_center_spacer.pack(side="left", expand=True, fill="x")

        # 右侧描述面板（垂直居中）
        self.menu_right_panel = Frame(
            self.menu_frame,
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
        )
        self.menu_right_panel.pack(side="left", fill="y", padx=(5, 80))

        right_top = Frame(self.menu_right_panel, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        right_top.pack(expand=True)

        self.menu_desc = Label(
            self.menu_right_panel,
            text="",
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            font=("HYWenHei-85W", 13),
            justify="left",
            anchor="w",
            wraplength=300,
        )
        self.menu_desc.pack(expand=False)

        right_bottom = Frame(self.menu_right_panel, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        right_bottom.pack(expand=True)

        # 构建菜单按钮（带悬停效果）
        self.menu_options = []
        descriptions = cfg.get("MENU_DESCRIPTIONS", {})
        BTN_WIDTH = 16  # 按钮固定总宽度（字符数），base 和 hover 等宽避免位移

        for i, opt_name in enumerate(cfg["MENU_OPTIONS"]):
            # base 与 hover 使用相同总宽度，确保悬停时按钮尺寸不变
            base_text = opt_name.center(BTN_WIDTH)
            hover_text = (">  " + opt_name + "  <").center(BTN_WIDTH)
            desc_text = descriptions.get(opt_name, "")

            btn = Button(
                self.btn_container,
                text=base_text,
                width=BTN_WIDTH,           # 固定 widget 宽度，防止 resize
                anchor="center",           # 文本始终居中
                fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
                bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
                font=("HYWenHei-85W", 12),
                relief=FLAT,
                command=self.func[i],
                activeforeground=cfg["COLOR_CONTEXT"][cfg["THEME"]],
                activebackground=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
                bd=0,
                padx=0,
                pady=0,
            )
            btn.pack(side="top", anchor="center", pady=0)

            # 悬停事件绑定（使用默认参数捕获当前值）
            btn.bind("<Enter>", lambda e, b=btn, ht=hover_text, d=desc_text: (
                b.configure(text=ht),
                self.menu_desc.configure(text=d),
            ))
            btn.bind("<Leave>", lambda e, b=btn, bt=base_text: (
                b.configure(text=bt),
                self.menu_desc.configure(text=""),
            ))

            self.menu_options.append(btn)

        # 左侧底部弹簧
        bottom_spacer = Frame(self.menu_left_panel, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        bottom_spacer.pack(expand=True)

        # --- 按键绑定 ---
        self.tk.bind("<Escape>", self.open_menu)
        # 老板键：Ctrl+H 隐藏/恢复窗口
        self.tk.bind(BOSS_KEY_COMBO, self.toggle_boss_key)
        # 同时绑定大写版本，确保 CapsLock 状态下也能触发
        self.tk.bind("<Control-H>", self.toggle_boss_key)

        logging.info("UI 加载完成")

    # ==================== 菜单系统 ====================

    def open_menu(self, event):
        """打开菜单"""
        if self.conditions["loading"]:
            return
        self.menu_frame.place_forget()
        self.menu_frame.place(x=0, y=0, relheight=1, relwidth=1)
        self.pin = 0
        self.tk.unbind("<Escape>")
        self.tk.unbind("<Left>")
        self.tk.unbind("<Right>")
        self.tk.bind("<Escape>", self.close_menu)
        logging.debug("Open")

    def close_menu(self, event):
        """关闭菜单"""
        self.tk.unbind("<Escape>")
        self.tk.bind("<Escape>", self.open_menu)
        if self.conditions["reading"]:
            self.tk.bind("<Left>", lambda event: self.change_page(-1, 1))
            self.tk.bind("<Shift-Left>", lambda event: self.change_page(-1, 0))
            self.tk.bind("<Control-Left>", lambda event: self.change_page(-1, 2))
            self.tk.bind("<Right>", lambda event: self.change_page(1, 1))
            self.tk.bind("<Shift-Right>", lambda event: self.change_page(1, 0))
            self.tk.bind("<Control-Right>", lambda event: self.change_page(1, 2))
        logging.debug("Close")
        self.menu_frame.place_forget()

    # ==================== 页码切换 ====================

    def change_page(self, delta, fast):
        """
        切换页

        :param delta: 页码增量（+1 或 -1）
        :param fast: 0 -> 禁止 | 1 -> 标准 | 2 -> 最快
        """
        if not self.conditions["reading"] or self.conditions["loading"]:
            return
        if time.time() - self.change_time <= 0.1:
            limit = len(self.chapter_name) // 100
            if fast == 1:
                self.change_fast += 1
            elif fast == 2:
                self.change_fast = 51
                speed = limit
                logging.debug("进入极速翻页模式")
                self.title.configure(
                    fg=self.CONFIG["COLOR_CONTEXT"][self.CONFIG["THEME"]]
                )
                self.text.configure(
                    fg=self.CONFIG["COLOR_TITLE"][self.CONFIG["THEME"]]
                )
                self.tk.bind("<KeyRelease>", self.change_page_ended)
            if self.change_fast == 50:
                logging.debug("进入快速翻页模式")
                self.title.configure(
                    fg=self.CONFIG["COLOR_CONTEXT"][self.CONFIG["THEME"]]
                )
                self.text.configure(
                    fg=self.CONFIG["COLOR_TITLE"][self.CONFIG["THEME"]]
                )
                self.tk.bind("<KeyRelease>", self.change_page_ended)
            if self.change_fast >= 50:
                if fast == 1:
                    speed = min(int(math.pow(2, (self.change_fast - 50) // 100)), limit)
                if delta > 0:
                    if self.chapter_now < len(self.chapter_name) - speed:
                        self.chapter_now += speed
                        self.conditions["now"] = self.chapter_page[self.chapter_now]
                    else:
                        self.conditions["now"] = 1
                        self.chapter_now = 0
                else:
                    if self.chapter_now > speed - 1:
                        self.chapter_now -= speed
                        self.conditions["now"] = self.chapter_page[self.chapter_now]
                    else:
                        self.conditions["now"] = self.conditions["full"]
                        self.chapter_now = len(self.chapter_name) - 1
                self.title.configure(
                    text=f"×{speed}  " + self.chapter_name[self.chapter_now]
                )
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
        """快速翻页结束，恢复颜色与标题"""
        logging.debug("快速翻页结束")
        self.title.configure(fg=self.CONFIG["COLOR_TITLE"][self.CONFIG["THEME"]])
        self.text.configure(fg=self.CONFIG["COLOR_CONTEXT"][self.CONFIG["THEME"]])
        self.title.configure(text=self.chapter_name[self.chapter_now])
        self.tk.unbind("<KeyRelease>")

    # ==================== 跳转页 ====================

    def turn_to_page(self):
        """打开页码跳转窗口"""
        logging.info("打开页码跳转窗口")
        cfg = self.CONFIG
        self.jumping = Toplevel(self.tk)
        self.jumping.focus_force()
        self.jumping.geometry(
            f"{cfg['JUMP_WINDOW_WIDTH']}x{cfg['JUMP_WINDOW_HEIGHT']}"
            f"+{int((cfg['INFO_SCREEN_WIDTH'] - cfg['JUMP_WINDOW_WIDTH']) / 2)}"
            f"+{int((cfg['INFO_SCREEN_HEIGHT'] - cfg['JUMP_WINDOW_HEIGHT']) / 2)}"
        )
        self.jumping.configure(bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        self.entry = Entry(
            self.jumping,
            font=("Jetbrains Mono", 10),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
        )
        self.entry.pack()
        enter = Button(
            self.jumping,
            text="GO",
            font=("Jetbrains Mono", 10),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
            command=self.save,
        )
        enter.pack()
        logging.debug("页码跳转窗口已创建")

    def save(self):
        """确认跳转到输入页码"""
        target_page = int(self.entry.get())
        logging.info(
            f"尝试跳转到页码: {target_page}, 总页数: {self.conditions['full']}"
        )
        if 1 <= target_page <= self.conditions["full"]:
            logging.info(f"页码验证通过, 跳转到第{target_page}页")
            self.conditions["now"] = target_page
            self.jumping.destroy()
            self.update_page(self.conditions["now"], check_chapter=2)
            self.close_menu(None)
            logging.info(f"成功跳转到第{target_page}页")
        else:
            logging.warning(
                f"无效页码: {target_page}, 允许范围: 1-{self.conditions['full']}"
            )

    # ==================== 页面渲染 ====================

    def update_page(self, page, check_chapter=1):
        """
        显示指定页

        :param page: 要显示的页码
        :param check_chapter: 章节检查模式（0=关闭, 1=左右边界, 2=完全扫描）
        """
        cfg = self.CONFIG
        show = ""
        start = (page - 1) * cfg["LINES_PER_PAGE"]
        end = page * cfg["LINES_PER_PAGE"]
        for i in range(start, end):
            try:
                show += self.book[i]
            except IndexError:
                show += "\n"
        self.text.configure(text=show)
        self.status.configure(
            text=f"第{self.conditions['now']}/{self.conditions['full']}页 "
                 f"{round((self.conditions['now'] / self.conditions['full']) * 100, 3):.3f}%"
        )
        le = int(
            math.floor(
                cfg["HINT_LENGTH"] * 8 * self.conditions["now"] / self.conditions["full"]
            )
        )
        length = le // 8
        self.hint.configure(
            text=cfg["HINT_L"]
            + length * cfg["HINT_P"]
            + (
                cfg["HINT_Px"][le % 8]
                if self.conditions["now"] != self.conditions["full"]
                else ""
            )
            + "\u3000" * (cfg["HINT_LENGTH"] - (length + 1))
            + cfg["HINT_R"]
        )
        if check_chapter == 2:
            for i in range(len(self.chapter_name)):
                if page >= self.chapter_page[i] and page < self.chapter_page[i + 1]:
                    self.title.configure(text=self.chapter_name[i])
                    self.chapter_now = i
                    logging.debug(f"章节切换(扫描): [{i}] {self.chapter_name[i]}")
                    break
        elif check_chapter == 1:
            if self.chapter_now < len(self.chapter_name) - 1:
                if page >= self.chapter_page[self.chapter_now + 1]:
                    self.title.configure(text=self.chapter_name[self.chapter_now + 1])
                    self.chapter_now += 1
                    logging.debug(f"章节切换(前进): [{self.chapter_now}] {self.chapter_name[self.chapter_now]}")
            if self.chapter_now >= 0:
                if page < self.chapter_page[self.chapter_now]:
                    self.title.configure(text=self.chapter_name[self.chapter_now - 1])
                    self.chapter_now -= 1
                    logging.debug(f"章节切换(后退): [{self.chapter_now}] {self.chapter_name[self.chapter_now]}")

    # ==================== 分页处理 ====================

    def getpage(
        self,
        file_path,
        encodeings=None,
        charaters_per_line=0,
        lines_per_page=0,
        builtin=False,
    ):
        """
        分页：将文件内容拆分为屏幕可显示的行列表。

        :param file_path: 文件路径或内容字符串（内置模式）
        :param encodeings: 编码尝试列表
        :param charaters_per_line: 每行字数（使用 CONFIG 值）
        :param lines_per_page: 每页行数（使用 CONFIG 值）
        :param builtin: 是否为内置资源
        :return: (总页数, 行列表, 章节页码列表, 章节标题列表) 或错误码
        """
        cfg = self.CONFIG
        if encodeings is None:
            encodeings = cfg["ENCODEINGS"]
        charaters_per_line = cfg["CHARATERS_PER_LINE"]
        lines_per_page = cfg["LINES_PER_PAGE"]

        logging.info(
            f"开始分页处理: file_path={file_path if not builtin else 'builtin'}, "
            f"builtin={builtin}"
        )
        logging.debug(f"编码列表: {encodeings}")

        self.conditions["loading"] = True
        self.need_process_lines = 1

        chapter_page = []
        chapter_title = []

        if not file_path:
            logging.error("没有提供文件路径")
            self.conditions["loading"] = False
            return -1

        content = None
        if not builtin:
            logging.info("尝试读取外部文件")
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

        def process_line(line, width=cfg["WINDOW_WIDTH"] - 80):
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

        self.processed_orginal_lines = 0
        self.need_process_lines = len(content)
        self.conditions["full"] = self.need_process_lines
        processed_lines = []
        current_processed_count = 0

        for line_idx, line in enumerate(content):
            a = time.time()
            # 章节检测：非空行且不以空白字符开头
            if line.strip() and not line.startswith((" ", "\n", "	")):
                remaining_lines = lines_per_page - (
                    current_processed_count % lines_per_page
                )
                current_page = (current_processed_count // lines_per_page) + (
                    2 if current_processed_count % lines_per_page != 0 else 1
                )
                chapter_page.append(current_page)
                chapter_title.append(line.strip())
                if remaining_lines != lines_per_page:
                    padding = remaining_lines
                    processed_lines.extend(["\n"] * padding)
                    current_processed_count += padding
            # 行拆分
            while True:
                new_line, remaining = process_line(line)
                processed_lines.append(new_line.rstrip() + "\n")
                current_processed_count += 1
                if not remaining:
                    break
                line = remaining
            # 行间插入空行
            processed_lines.append("\n")
            current_processed_count += 1
            self.processed_orginal_lines += 1
            self.conditions["load_speed"] = (
                self.conditions["load_speed"] * (self.processed_orginal_lines - 1)
                + time.time()
                - a
            ) / self.processed_orginal_lines

        lines = processed_lines
        full = math.ceil(len(lines) / lines_per_page)
        chapter_page.append(99999999)
        self.conditions["loading"] = False
        logging.info(
            f"分页完成: 总行数={len(lines)}, 总页数={full}, "
            f"检测到{len(chapter_title)}个章节"
        )
        if full == 0:
            return -3
        return full, lines, chapter_page, chapter_title

    # ==================== 文件打开 ====================

    def open_file(self, file_path=None, built=False, reload=False):
        """
        打开文件（同步分页，在后台线程中调用）

        :param file_path: 文件路径或内置键
        :param built: 是否为内置书籍
        :param reload: 是否为重载
        """
        logging.info(
            f"开始打开文件: file_path={file_path}, built={built}, reload={reload}"
        )
        if not file_path:
            if reload:
                logging.info("重载操作，跳过文件选择")
                return
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("Text Files(Suggest)", "*.txt"),
                    ("Code(Render err)", "*.py;*.cpp;*.c;*.json;*.java;*.js;*.md;*.log"),
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
            self._reset_reading_state()
        elif tmp == -2:
            logging.error("文件解码错误")
            messagebox.showerror("Error", "Cannot decode file.")
            self._reset_reading_state()
        elif tmp == -3:
            logging.error("空文件错误")
            messagebox.showerror("Error", "File is empty.")
            self._reset_reading_state()
        else:
            logging.info(
                f"成功打开文件: {file_path}, 总页数: {tmp[0]}, 章节数: {len(tmp[3])}"
            )
            self.file_path = file_path
            self.conditions["now"] = 1
            self.conditions["full"] = tmp[0]
            self.book = tmp[1]
            self.chapter_page = tmp[2]
            self.chapter_name = tmp[3]
            self.update_page(1, check_chapter=2)
            self.close_menu(None)

    def _reset_reading_state(self):
        """打开文件失败时重置状态"""
        logging.info("重置阅读状态（文件打开失败）")
        self.conditions["reading"] = False
        self.conditions["loading"] = False
        self.book = []
        self.chapter_page = []
        self.chapter_name = []
        self.open_menu(None)
        self.close_menu(None)
        self.hint.configure(text="")
        self.status.configure(text="")

    def open_filet(self, file_path=None, built=False, reload=False):
        """
        线程化打开文件（带进度条）

        :param file_path: 文件路径
        :param built: 是否内置
        :param reload: 是否重载
        """
        self.need_process_lines = 1
        self.processed_orginal_lines = 0
        if built and hasattr(self, "select"):
            self.select.destroy()
        self.conditions["loading"] = True

        # 释放旧数据，避免新旧数据同时在内存中导致峰值翻倍
        self.book = []
        self.chapter_page = []
        self.chapter_name = []
        gc.collect()

        self.conditions["full"] = 1
        self.conditions["now"] = 1
        self.conditions["reading"] = True
        if not file_path:
            if reload:
                self.conditions["reading"] = False
                self.conditions["loading"] = False
                return

        thread = threading.Thread(
            target=self.open_file, args=(file_path, built, reload)
        )
        thread.daemon = True
        thread.start()

        def check_progress():
            if self.conditions["loading"]:
                self.conditions["now"] = self.processed_orginal_lines
                t = int(
                    (self.need_process_lines - self.processed_orginal_lines)
                    * self.conditions["load_speed"]
                )
                self.book = (
                    ["Importing File...(Cauculating...)"]
                    if self.conditions["now"] == 0
                    else [
                        f"Loading File...({self.processed_orginal_lines}/"
                        f"{self.need_process_lines} | ETA {t // 60}:"
                        f"{'0' if t % 60 < 10 else ''}{t % 60})"
                    ]
                )
                self.update_page(1, check_chapter=0)
                self.tk.after(70, check_progress)

        self.tk.after(70, check_progress)
        self.close_menu(None)

    # ==================== 内置书籍选择 ====================

    def builtin_select(self):
        """内置书籍选择窗口"""
        cfg = self.CONFIG
        logging.info("打开内置书籍选择窗口")
        if not self.conditions["resource_active"]:
            logging.warning("资源未激活，无法使用内置书籍")
            messagebox.showwarning(
                "警告", "未找到资源文件，请重新下载，否则无法使用内置书籍。"
            )
            return
        self.select = Toplevel(self.tk)
        self.select.focus_force()
        self.select.geometry(
            f"{cfg['SELECT_WINDOW_WIDTH']}x{cfg['SELECT_WINDOW_HEIGHT']}"
            f"+{int((cfg['INFO_SCREEN_WIDTH'] - cfg['SELECT_WINDOW_WIDTH']) / 2)}"
            f"+{int((cfg['INFO_SCREEN_HEIGHT'] - cfg['SELECT_WINDOW_HEIGHT']) / 2)}"
        )
        self.select.configure(bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        empty = Label(
            self.select,
            text="",
            font=("Jetbrains Mono", 5),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
        )
        empty.pack()
        dashboard = Listbox(
            self.select,
            font=("Jetbrains Mono", 10),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
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
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            width=25,
            relief=FLAT,
            command=lambda: self.open_filet(
                reallist[showlist.index(dashboard.get(ACTIVE))], True
            ),
        )
        enter.pack()

    # ==================== 主题切换 ====================

    def change_color(self):
        """切换颜色主题（0→1→2→0）"""
        cfg = self.CONFIG
        cfg["THEME"] = 0 if cfg["THEME"] == 2 else cfg["THEME"] + 1
        bg = cfg["COLOR_BACKGROUND"][cfg["THEME"]]
        fg_ctx = cfg["COLOR_CONTEXT"][cfg["THEME"]]
        fg_title = cfg["COLOR_TITLE"][cfg["THEME"]]

        self.tk.configure(bg=bg)
        self.title.configure(bg=bg, fg=fg_title)
        self.text.configure(bg=bg, fg=fg_ctx)
        self.status.configure(bg=bg, fg=fg_ctx)
        self.menu_frame.configure(bg=bg)
        self.menu_left_panel.configure(bg=bg)
        self.menu_center_spacer.configure(bg=bg)
        self.menu_right_panel.configure(bg=bg)
        self.btn_container.configure(bg=bg)
        for i in self.menu_options:
            i.configure(
                bg=bg, fg=fg_ctx,
                activeforeground=fg_ctx, activebackground=bg,
            )
        self.menu_desc.configure(bg=bg, fg=fg_ctx)
        self.hint.configure(bg=bg, fg=fg_title)
        theme_names = ["暗蓝", "暗灰", "浅色"]
        logging.info(f"颜色主题切换为: {theme_names[cfg['THEME']]}")

    # ==================== 分辨率修改 ====================

    def change_resolution(self):
        """打开分辨率选择窗口"""
        from config import RESOLUTIONS

        cfg = self.CONFIG
        logging.info("打开分辨率选择窗口")
        if self.conditions["fullscreen"]:
            messagebox.showinfo("提示", "请先退出全屏模式再修改分辨率。")
            return

        self.res_win = Toplevel(self.tk)
        self.res_win.focus_force()
        self.res_win.title("选择分辨率")
        self.res_win.configure(bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        self.res_win.resizable(False, False)

        # 标题
        title_lbl = Label(
            self.res_win,
            text="请选择窗口分辨率",
            font=("HYWenHei-85W", 13),
            fg=cfg["COLOR_TITLE"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
        )
        title_lbl.pack(pady=(15, 10))

        # 分辨率列表
        list_frame = Frame(
            self.res_win, bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]]
        )
        list_frame.pack(padx=20, pady=5)

        res_list = Listbox(
            list_frame,
            font=("Jetbrains Mono", 11),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            selectmode=BROWSE,
            width=28,
            height=len(RESOLUTIONS),
            relief=FLAT,
            activestyle="none",
        )
        res_list.pack(side="left")

        for _, _, label in RESOLUTIONS:
            res_list.insert(END, f"  {label}")

        # 默认选中当前分辨率
        current_w, current_h = cfg["WINDOW_WIDTH"], cfg["WINDOW_HEIGHT"]
        for idx, (w, h, _) in enumerate(RESOLUTIONS):
            if w == current_w and h == current_h:
                res_list.selection_set(idx)
                res_list.activate(idx)
                break

        # 确认按钮
        def apply_resolution():
            sel = res_list.curselection()
            if sel:
                w, h, _ = RESOLUTIONS[sel[0]]
                logging.info(f"切换分辨率: {w}×{h}")
                cfg["WINDOW_WIDTH"] = w
                cfg["WINDOW_HEIGHT"] = h

                # 隐藏底部控件（与全屏切换逻辑一致）
                self.hint.place_forget()
                self.status.place_forget()

                # 重新计算全部派生尺寸
                self._apply_dimensions()

                # 重设窗口几何
                self.tk.geometry(
                    f"{w}x{h}"
                    f"+{int((cfg['INFO_SCREEN_WIDTH'] - w) / 2)}"
                    f"+{int((cfg['INFO_SCREEN_HEIGHT'] - h) / 2)}"
                )

                # 重新摆放底部控件
                self.status.place(x=10, y=cfg["WINDOW_HEIGHT"] - 55)
                self.hint.place(x=10, y=cfg["WINDOW_HEIGHT"] - 30)

                # 更新文本显示区尺寸
                self.text.configure(
                    width=cfg["CHARATERS_PER_LINE"],
                    height=cfg["LINES_PER_PAGE"],
                )

                # 重载文件以适配新尺寸
                self.res_win.destroy()
                logging.info(f"分辨率已切换至 {w}×{h}，重新加载文件")
                self.open_filet(
                    file_path=self.file_path, built=self.builtin, reload=True
                )
                self.close_menu(None)

        btn = Button(
            self.res_win,
            text="确认",
            font=("HYWenHei-85W", 12),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
            command=apply_resolution,
        )
        btn.pack(pady=(5, 15))

        # 窗口居中
        self.res_win.update_idletasks()
        rw = self.res_win.winfo_width()
        rh = self.res_win.winfo_height()
        self.res_win.geometry(
            f"+{int((cfg['INFO_SCREEN_WIDTH'] - rw) / 2)}"
            f"+{int((cfg['INFO_SCREEN_HEIGHT'] - rh) / 2)}"
        )

    # ==================== 全屏切换 ====================

    def change_full_screen(self):
        """切换全屏模式，重新计算所有尺寸并重载页面"""
        cfg = self.CONFIG
        self.conditions["fullscreen"] = not self.conditions["fullscreen"]
        logging.info(
            f"切换全屏: {'进入全屏' if self.conditions['fullscreen'] else '退出全屏'}"
        )
        self.tk.attributes("-fullscreen", self.conditions["fullscreen"])
        self.hint.place_forget()
        self.status.place_forget()

        if self.conditions["fullscreen"]:
            # 保存当前窗口尺寸，退出全屏时恢复
            self._saved_width = cfg["WINDOW_WIDTH"]
            self._saved_height = cfg["WINDOW_HEIGHT"]
            cfg["WINDOW_WIDTH"] = cfg["INFO_SCREEN_WIDTH"]
            cfg["WINDOW_HEIGHT"] = cfg["INFO_SCREEN_HEIGHT"]
        else:
            # 恢复进入全屏前的分辨率（而非 DEFAULT 硬编码值）
            cfg["WINDOW_WIDTH"] = getattr(self, "_saved_width", DEFAULT["WINDOW_WIDTH"])
            cfg["WINDOW_HEIGHT"] = getattr(self, "_saved_height", DEFAULT["WINDOW_HEIGHT"])

        self._apply_dimensions()

        self.status.place(x=10, y=cfg["WINDOW_HEIGHT"] - 55)
        self.hint.place(x=10, y=cfg["WINDOW_HEIGHT"] - 30)
        self.text.configure(
            width=cfg["CHARATERS_PER_LINE"], height=cfg["LINES_PER_PAGE"]
        )
        self.open_filet(file_path=self.file_path, built=self.builtin, reload=True)
        self.tk.focus_force()

    # ==================== 目录 & 关于 ====================

    def generate_contents(self):
        """生成目录文件 Contents.txt"""
        logging.info(f"正在生成目录，共 {len(self.chapter_name)} 个章节")
        with open("Contents.txt", "w", encoding="utf-8-sig") as f:
            f.write("目录:\n")
            for i in range(len(self.chapter_name)):
                f.write(f"  {self.chapter_name[i]} - {self.chapter_page[i]}\n")
        logging.info("目录已生成至 Contents.txt")

    def about(self):
        """显示关于信息"""
        logging.info("显示关于信息")
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

    # ==================== 开发者模式 ====================

    def devlop(self, event):
        """检测开发者密码输入"""
        if event.char == self.dev_password[self.dev]:
            self.dev += 1
            if self.dev == 10:
                logging.info("开发者模式已激活")
                self.tk.unbind("<Key>")
                self.CONFIG["EMPTY_TEXT"] = "--- 未打开文件，开发者模式启动 ---"
                self.CONFIG["MENU_OPTIONS"].insert(9, "自定义指令")
                self.CONFIG["MENU_OPTIONS"].insert(9, "导出")
                self.func.insert(9, self.custom)
                self.func.insert(9, unpack_resources)
                self.load_ui()
                self.text.configure(text=self.CONFIG["EMPTY_TEXT"])
        else:
            self.dev = 0

    def custom(self):
        """自定义指令窗口"""
        cfg = self.CONFIG
        self.custom_bar = Toplevel(self.tk)
        self.custom_bar.focus_force()
        self.custom_bar.geometry(
            f"500x40"
            f"+{int((cfg['INFO_SCREEN_WIDTH'] - 500) / 2)}"
            f"+{int((cfg['INFO_SCREEN_HEIGHT'] - 40) / 2)}"
        )
        self.custom_bar.resizable(False, False)
        self.custom_bar.configure(bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]])
        self.command = Entry(
            self.custom_bar,
            font=("Jetbrains Mono", 10),
            width=60,
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
        )
        self.command.pack()
        enter = Button(
            self.custom_bar,
            text="GO",
            font=("Jetbrains Mono", 10),
            fg=cfg["COLOR_CONTEXT"][cfg["THEME"]],
            bg=cfg["COLOR_BACKGROUND"][cfg["THEME"]],
            relief=FLAT,
            command=self.run,
        )
        enter.pack()

    def run(self):
        """执行自定义指令"""
        cmd = self.command.get()
        logging.info(f"尝试执行{cmd}")
        try:
            result = eval(cmd)
        except Exception as e:
            messagebox.showerror("出现错误！", f"{e}")
            logging.error(f"自定义指令错误：{e}")
        else:
            logging.info(f"自定义指令执行成功，返回{result}")

    # ==================== 程序控制 ====================

    def restart(self):
        """重启程序"""
        logging.info("正在重启程序...")
        python = sys.executable
        logging.info(f"使用Python解释器路径: {python}")
        os.execl(python, python, *sys.argv)

    def quit(self):
        """退出程序"""
        logging.info("正在退出程序...")
        self.tk.destroy()
        logging.info("程序已退出")
        quit()

    # ==================== 老板键 ====================

    def toggle_boss_key(self, event=None):
        """老板键：Ctrl+H 一键隐藏/恢复窗口，伪装为记事本"""
        if not self.boss_key_active:
            # --- 隐藏模式 ---
            logging.info("老板键触发：隐藏窗口")
            self.boss_key_active = True
            # 保存当前标题
            self._boss_saved_title = self.tk.title()
            # 修改标题为无害文本
            self.tk.title(BOSS_KEY_DISGUISE_TITLE)
            # 最小化窗口
            self.tk.iconify()
            # 监听窗口恢复事件
            self.tk.bind("<Map>", self._on_boss_restore)
        else:
            # --- 恢复模式 ---
            logging.info("老板键触发：恢复窗口")
            self._restore_from_boss()

    def _on_boss_restore(self, event=None):
        """当窗口从最小化恢复时，自动还原标题"""
        if self.boss_key_active:
            self._restore_from_boss()

    def _restore_from_boss(self):
        """从老板键隐藏状态恢复"""
        self.boss_key_active = False
        self.tk.title(self._boss_saved_title)
        self.tk.deiconify()
        self.tk.lift()
        self.tk.focus_force()
        self.tk.unbind("<Map>")
        logging.info(f"老板键恢复：标题已还原为 '{self._boss_saved_title}'")

    def EMPTY(self):
        """空置函数（占位）"""
        pass
