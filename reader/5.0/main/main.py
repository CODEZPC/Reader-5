"""
Reader 5 - UI
"""
from imports import *
from menu import ReaderMenu

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
        self.create_menu()
        self.bind_keys()
    
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
        self.font_status = tkfont.Font(family="Jetbrains mono", size=12)
        self.font_hint = tkfont.Font(family="HYWenHei-85W", size=8)

        # 颜色
        self.color_bg = "#23272E"
        self.color_fg = "#C8C8C8"
        self.color_mid = "#767F89"

        # 预填窗口尺寸，避免 geometry() 触发的首次 Configure 事件重复重建
        self._last_width = self.window_width
        self._last_height = self.window_height
    
    def preload_conditions(self):

        self.page = 0
        self.page_total = 0
        self.text_labels = []  # 阅读器显示 Label 列表
        self._updating = False  # 防重入标志

        # 文件与分页相关
        self.filename = ""
        self.text_content = ""
        self.display_lines = []
        self.pages = []
        self._original_lines = []
        self._paginate_busy = False
        self._char_w_cache = {}  # 字符宽度缓存：{char: pixels}
        self._orig_to_disp = []  # 原始行索引 → 首个显示行索引
    
    def calculate_config(self):
        self.hint_length = (self.window_width - 20 - self.font_hint.measure("|") * 2) // self.font_hint.measure("█")

        # 阅读器显示区计算
        self.line_height = self.font_text.metrics("linespace")  # 单行高度
        self.label_gap = 5  # Label 间隔
        self.margin_x = 25  # 左右边距
        self.margin_top = 45  # 顶部留白（标题下方）
        self.margin_bottom = 40  # 底部留白（状态栏上方）
        self.label_width = self.window_width - self.margin_x * 2
        available_height = self.window_height - self.margin_top - self.margin_bottom
        self.max_lines = max(1, available_height // (self.line_height + self.label_gap))
    
    def create_widgets(self):
        """创建UI组件"""

        # 设置窗口基本属性
        tk.title("Reader 5")
        tk.geometry(f"{self.window_width}x{self.window_height}+{(self.screen_width - self.window_width) // 2}+{(self.screen_height - self.window_height) // 2}")
        tk.minsize(240, 150)
        tk.config(bg=self.color_bg)

        self.title = Label(
            text="READER 5",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_title,
        )
        self.title.place(x=10, y=10)

        self.status = Label(
            text="未打开文件",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_status,
            anchor="w",
        )
        self.status.place(x=10, y=self.window_height - 44)

        self.hint = Label(
            text="",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_hint,
        )
        self.hint.place(x=10, y=self.window_height - 22)

        # 创建阅读器显示 Label 列表
        self.create_text_labels()

        tk.bind("<Configure>", self.on_resize)
    
    def create_menu(self):
        """创建 ESC 菜单"""
        self.menu = ReaderMenu(tk, self)

    def bind_keys(self):
        """绑定快捷键"""
        tk.bind("<Escape>", lambda e: self.menu.show() if not self.menu.visible else self.menu.hide())
        tk.bind("<Left>", lambda e: self.prev_page())
        tk.bind("<Right>", lambda e: self.next_page())
    
    def create_text_labels(self):
        """创建或重建阅读器显示 Label 列表"""
        self._updating = True  # 防重入：place 子控件会触发父级 Configure
        try:
            # 销毁旧 Label（先 place_forget 再 destroy，防止残影）
            for label in self.text_labels:
                label.place_forget()
                label.destroy()
            self.text_labels.clear()
            tk.update_idletasks()

            # 按计算出的行数创建新 Label
            for i in range(self.max_lines):
                y_pos = self.margin_top + i * (self.line_height + self.label_gap)
                label = Label(
                    tk,
                    text="",
                    fg=self.color_fg,
                    bg=self.color_bg,
                    font=self.font_text,
                    anchor="w",
                    justify="left",
                    wraplength=self.label_width,
                )
                label.place(x=self.margin_x, y=y_pos, width=self.label_width, height=self.line_height)
                self.text_labels.append(label)
            tk.update_idletasks()
        finally:
            self._updating = False

    # ── 翻页（左右方向键）────────────────────────────────────

    def prev_page(self):
        if not self.pages or self._paginate_busy:
            return
        if self.page > 0:
            self.page -= 1
            self.display_page()

    def next_page(self):
        if not self.pages or self._paginate_busy:
            return
        if self.page < self.page_total - 1:
            self.page += 1
            self.display_page()

    # ── 文件打开与异步分批分页（不阻塞 UI）──────────────────

    def open_file(self):
        """打开 txt 文件并启动分批异步分页"""
        if self._paginate_busy:
            return
        filepath = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not filepath:
            return
        self.filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                self.text_content = f.read()
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件:\n{e}")
            return
        
        tk.resizable(False, False)
        self.page = 0
        self._paginate_busy = True
        self.display_lines = []
        self._orig_to_disp = []
        self._original_lines = self.text_content.split("\n")
        self._paginate_idx = 0
        self.status.config(text="正在分页... 0%")
        tk.after(10, self._paginate_step)

    def _paginate_step(self):
        """每次处理一批原始行（通过 after 调度，保持 UI 响应）"""
        batch = 300
        total = len(self._original_lines)
        start = self._paginate_idx
        end = min(start + batch, total)

        for idx in range(start, end):
            line = self._original_lines[idx]
            self._orig_to_disp.append(len(self.display_lines))
            if line == "":
                self.display_lines.append("")
            else:
                self.display_lines.extend(self._break_line_fast(line))

        self._paginate_idx = end
        pct = end / total * 100 if total > 0 else 100
        self.status.config(text=f"正在分页... {pct:.0f}%  ({end}/{total} 行)")
        self.change_hint(end, total)

        if end < total:
            tk.after(1, self._paginate_step)
        else:
            tk.after(1, self._paginate_finish)

    def _break_line_fast(self, line):
        """快速断行：字符宽度缓存字典，首次测量后命中 O(1)"""
        result = []
        current = ""
        current_w = 0
        max_w = self.label_width - 2
        cache = self._char_w_cache

        for ch in line:
            ch_w = cache.get(ch)
            if ch_w is None:
                ch_w = self.font_text.measure(ch)
                cache[ch] = ch_w
            if current_w + ch_w <= max_w:
                current += ch
                current_w += ch_w
            else:
                if current:
                    result.append(current)
                current = ch
                current_w = ch_w
        if current:
            result.append(current)
        return result if result else [""]

    def _paginate_finish(self):
        """分页完成：章节检测 → 对齐 → 构建页面 → 显示"""
        # 章节检测与对齐
        self._adjust_chapters()

        # 按 max_lines 分组为页
        self.pages = []
        for i in range(0, len(self.display_lines), self.max_lines):
            self.pages.append(self.display_lines[i:i + self.max_lines])

        if not self.pages:
            self.pages = [[""]]

        self.page_total = len(self.pages)
        self.page = min(self.page, self.page_total - 1)
        self._paginate_busy = False
        self.display_page()

    # ── 章节检测与对齐 ────────────────────────────────────────

    def _adjust_chapters(self):
        """在原始行上检测章节标题（^[^\\s]），映射到显示行后补齐空行"""
        CHAPTER_RE = re.compile(r'^[^\s]')

        # 在原始行上找出章节标题的原始索引
        chapter_orig_indices = []
        for i, line in enumerate(self._original_lines):
            if line.strip() == "":
                continue
            if CHAPTER_RE.match(line):
                chapter_orig_indices.append(i)

        if not chapter_orig_indices:
            return

        # 映射到显示行索引
        chapter_disp_indices = [self._orig_to_disp[i] for i in chapter_orig_indices]

        # 构建新显示行列表：正向遍历，在章节标题前补齐空行
        new_lines = []
        prev = 0

        for di in chapter_disp_indices:
            new_lines.extend(self.display_lines[prev:di])
            cur_pos = len(new_lines)
            remainder = cur_pos % self.max_lines
            if remainder != 0:
                padding = self.max_lines - remainder
                new_lines.extend([""] * padding)
            new_lines.append(self.display_lines[di])
            prev = di + 1

        new_lines.extend(self.display_lines[prev:])
        self.display_lines = new_lines

    def display_page(self):
        """将当前页内容填入显示 Label"""
        if not self.pages or self.page >= len(self.pages):
            return
        page_lines = self.pages[self.page]
        for i, label in enumerate(self.text_labels):
            if i < len(page_lines):
                label.config(text=page_lines[i])
            else:
                label.config(text="")
        self.update_status()
        self.change_hint(self.page, self.page_total)

    def update_status(self):
        """刷新底部状态栏"""
        if self.filename and self.page_total > 0:
            percent = (self.page + 1) / self.page_total * 100
            self.status.config(
                text=f"{self.filename}  {self.page + 1}/{self.page_total}  {percent:.3f}%"
            )
        elif self.filename:
            self.status.config(text=f"{self.filename}  0/0  0.000%")
        else:
            self.status.config(text="未打开文件")

    def jump_to_page(self, page_num):
        """跳转到指定页码（1-indexed）"""
        if 1 <= page_num <= self.page_total:
            self.page = page_num - 1
            self.display_page()

    def jump_page_dialog(self):
        """弹出跳转页码对话框"""
        if not self.text_content:
            messagebox.showinfo("提示", "请先打开文件")
            return
        page_str = simpledialog.askstring(
            "跳转页码", f"请输入页码 (1 - {self.page_total}):",
            parent=tk,
        )
        if page_str is None:
            return
        try:
            page_num = int(page_str.strip())
            if 1 <= page_num <= self.page_total:
                self.jump_to_page(page_num)
            else:
                messagebox.showwarning("警告", f"页码超出范围 (1 - {self.page_total})")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数页码")

    # ── 窗口 resize ───────────────────────────────────────────

    def on_resize(self, event):
        """窗口调整大小时重新计算布局并保持阅读位置"""
        if self._updating or self._paginate_busy or str(event.widget) != str(tk):
            return
        width = event.width
        height = event.height
        if width == self._last_width and height == self._last_height:
            return
        self._last_width = width
        self._last_height = height
        self.window_width = width
        self.window_height = height

        # 保存当前阅读位置（当前页首行在 display_lines 中的索引）
        current_line_idx = 0
        if self.pages and self.page < len(self.pages):
            for i in range(self.page):
                current_line_idx += len(self.pages[i])

        # 重新计算布局参数
        self.calculate_config()

        # 重建显示 Label
        self.create_text_labels()

        # 重新分页并定位（同步完成，resize 时使用快速断行）
        if self._original_lines:
            self.display_lines = []
            self._orig_to_disp = []
            for line in self._original_lines:
                self._orig_to_disp.append(len(self.display_lines))
                if line == "":
                    self.display_lines.append("")
                else:
                    self.display_lines.extend(self._break_line_fast(line))
            self._adjust_chapters()
            self.pages = []
            for i in range(0, len(self.display_lines), self.max_lines):
                self.pages.append(self.display_lines[i:i + self.max_lines])
            if not self.pages:
                self.pages = [[""]]
            self.page_total = len(self.pages)
            # 找到包含旧位置的新页码
            new_page = 0
            line_count = 0
            for i, page_lines in enumerate(self.pages):
                if line_count + len(page_lines) > current_line_idx:
                    new_page = i
                    break
                line_count += len(page_lines)
            self.page = new_page
            self.display_page()

        # 更新底部状态栏位置
        self.status.place_configure(y=height - 44)
        self.hint.place_configure(y=height - 22)
    
    def change_hint(self, current, total):
        """更新状态栏提示（进度条）"""
        hint_unit = ["∅", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
        ratio = current / total if total > 0 else 0
        ratio = max(0.0, min(1.0, ratio))
        hint_unit_length = 8 * self.hint_length
        hint_interger = int(ratio * self.hint_length)
        hint_decimal = int((ratio * hint_unit_length) % 8)

        empty = self.hint_length - hint_interger - (1 if hint_decimal > 0 else 0)
        if hint_decimal == 0:
            self.hint.config(text=f"|{hint_interger * hint_unit[8]}{'\u3000' * empty}|")
        else:
            self.hint.config(text=f"|{hint_interger * hint_unit[8]}{hint_unit[hint_decimal]}{'\u3000' * empty}|")

if __name__ == "__main__":
    global UI, ERROR
    ERROR = ErrorAnalyzer()
    UI = ReaderUI()
    tk.mainloop()
