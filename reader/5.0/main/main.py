"""
Reader 5 - UI
"""
from imports import *

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

        # 预填窗口尺寸，避免 geometry() 触发的首次 Configure 事件重复重建
        self._last_width = self.window_width
        self._last_height = self.window_height
    
    def preload_conditions(self):

        self.page = 0
        self.page_total = 0
        self.text_labels = []  # 阅读器显示 Label 列表
        self._updating = False  # 防重入标志
    
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
            text="",
            fg=self.color_mid,
            bg=self.color_bg,
            font=self.font_status,
        )
        self.status.place(x=10, y=self.window_height - 35)

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
    
    def create_text_labels(self):
        """创建或重建阅读器显示 Label 列表"""
        self._updating = True  # 防重入：place 子控件会触发父级 Configure
        try:
            # 销毁旧 Label
            for label in self.text_labels:
                label.destroy()
            self.text_labels.clear()

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
        finally:
            self._updating = False

    def on_resize(self, event):
        """窗口调整大小时重新计算组件位置"""
        # 忽略非根窗口事件和内部更新触发的伪事件
        if self._updating or str(event.widget) != str(tk):
            return
        width = event.width
        height = event.height
        # 忽略初始配置事件和未变化的尺寸
        if width == self._last_width and height == self._last_height:
            return
        self._last_width = width
        self._last_height = height
        self.window_width = width
        self.window_height = height

        # 重新计算
        self.calculate_config()

        # 重建显示 Label
        self.create_text_labels()

        # 更新底部状态栏位置（相对窗口底部固定）
        self.status.place_configure(y=height - 35)
        self.hint.place_configure(y=height - 22)

        self.change_hint(self.page, self.page_total)
    
    def change_hint(self, current, total):
        """更新状态栏提示"""
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
            self.hint.config(text=f"|{hint_interger * hint_unit[8]}{hint_unit[hint_decimal]}{' ' * empty}|")

if __name__ == "__main__":
    global UI, ERROR
    ERROR = ErrorAnalyzer()
    UI = ReaderUI()
    tk.mainloop()
