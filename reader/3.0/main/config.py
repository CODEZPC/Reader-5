"""
READER 3 - 配置文件
所有可调整参数集中于此，便于修改。
"""

import logging

# ==================== 日志配置 ====================

def setup_logging(log_file: str = "reader.log"):
    """初始化日志系统，可在入口调用。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"日志系统已初始化，日志文件: {log_file}")


# ==================== 老板键配置 ====================

BOSS_KEY_COMBO = "<Control-h>"        # 老板键快捷键（Ctrl+H）
BOSS_KEY_DISGUISE_TITLE = "Code Render Pro"  # 伪装标题


# ==================== 默认值 ====================

DEFAULT = {
    "LINES_PER_PAGE": 26,       # 每页行数
    "CHARATERS_PER_LINE": 120,  # 每行字数
    "WINDOW_WIDTH": 1280,       # 窗口宽
    "WINDOW_HEIGHT": 720,       # 窗口高
    "MENU_WIDTH": 100,          # 菜单宽
    "MENU_HEIGHT": 25,          # 菜单高
    "HINT_LENGTH": 77,          # 提示栏长
}


# ==================== 可用分辨率列表 ====================
# 格式：(宽, 高, 显示名称)
RESOLUTIONS = [
    (330,  480,  "330×480 SMALL"),
    (800,  600,  "800×600"),
    (1024, 768,  "1024×768"),
    (1280, 130,  "1280×130"),
    (1280, 720,  "1280×720 (默认)"),
    (1366, 768,  "1366×768"),
    (1440, 900,  "1440×900"),
    (1600, 900,  "1600×900"),
    (1920, 1080, "1920×1080"),
]


# ==================== 运行时可动态计算，此处仅提供初始值 ====================

def make_default_config(tk_instance=None):
    """
    根据 tk 实例（可选）生成初始 CONFIG 字典。
    Reader.__init__ 中会调用此函数并进一步根据屏幕尺寸调整。
    """
    screen_w = tk_instance.winfo_screenwidth() if tk_instance else 1920
    screen_h = tk_instance.winfo_screenheight() if tk_instance else 1080

    return {
        # --- 显示参数（初始值与 DEFAULT 一致，运行时可被全屏切换覆盖）---
        "LINES_PER_PAGE": DEFAULT["LINES_PER_PAGE"],
        "CHARATERS_PER_LINE": DEFAULT["CHARATERS_PER_LINE"],
        "WINDOW_WIDTH": DEFAULT["WINDOW_WIDTH"],
        "WINDOW_HEIGHT": DEFAULT["WINDOW_HEIGHT"],

        # --- 弹窗尺寸 ---
        "JUMP_WINDOW_WIDTH": 150,
        "JUMP_WINDOW_HEIGHT": 40,
        "SELECT_WINDOW_WIDTH": 265,
        "SELECT_WINDOW_HEIGHT": 640,

        # --- 文件编码尝试顺序 ---
        "ENCODEINGS": ["gbk", "utf-8-sig", "utf-8"],

        # --- 进度条字符 ---
        "HINT_L": "|",
        "HINT_R": "|",
        "HINT_P": "█",
        "HINT_Px": ["\u3000", "▏", "▎", "▍", "▌", "▋", "▊", "▉"],
        "HINT_LENGTH": DEFAULT["HINT_LENGTH"],

        # --- 屏幕信息（运行时获取）---
        "INFO_SCREEN_WIDTH": screen_w,
        "INFO_SCREEN_HEIGHT": screen_h,

        # --- 空文本提示 ---
        "EMPTY_TEXT": "--- 未打开文件，按ESC以打开菜单 ---",

        # --- 菜单选项 ---
        "MENU_OPTIONS": [
            "返回阅读",
            "打开文件",
            "转到页码",
            "重载",
            "内置书籍",
            "生成目录",
            "设置全屏",
            "修改分辨率",
            "切换颜色",
            # "导出",        # 开发者模式专用
            # "自定义指令",  # 开发者模式专用
            "关于",
            "赞助",
            "重启",
            "退出",
        ],

        # --- 菜单描述（鼠标悬停时右侧显示）---
        "MENU_DESCRIPTIONS": {
            "返回阅读":     "关闭菜单，返回当前阅读位置",
            "打开文件":     "从本地磁盘选择一个 .txt 文本文件打开",
            "转到页码":     "输入页码，快速跳转到指定页面",
            "重载":         "重新加载当前文件，刷新分页与章节",
            "内置书籍":     "从内置资源包中选择一本书籍阅读",
            "生成目录":     "将当前书籍的章节目录导出为 Contents.txt",
            "设置全屏":     "切换窗口的全屏 / 窗口模式",
            "修改分辨率":   "从预设分辨率列表中选择窗口尺寸",
            "切换颜色":     "在暗蓝、暗灰、浅色三种主题间循环切换",
            "导出":         "将内置资源包解压输出到 extracted 目录",
            "自定义指令":   "打开命令行输入框，执行自定义 Python 代码",
            "关于":         "查看 READER 的版本与作者信息",
            "赞助":         "在浏览器中打开赞助 / 项目主页",
            "重启":         "重新启动 READER 程序",
            "退出":         "退出 READER 程序",
        },

        # --- 颜色主题 ---
        # 顺序：[蓝灰, 灰白, 浅色]
        "COLOR_TITLE":      ["#767F89", "#767F89", "#767F89"],
        "COLOR_CONTEXT":    ["#90BFF5", "#C8C8C8", "#23272E"],
        "COLOR_BACKGROUND": ["#23272E", "#23272E", "#DEDEDE"],
        "THEME": 0,  # 当前主题索引：0-暗蓝, 1-暗灰, 2-浅色
    }
