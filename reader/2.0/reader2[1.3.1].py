from tkinter import *
from tkinter import filedialog, messagebox
import time, threading, math, os

tk = Tk()
CONFIG = {
    # 每页行数
    "LINES_PER_PAGE": 31,
    # 每行字数
    "CHARATERS_PER_LINE": 120,
    # 窗口宽
    "WINDOW_WIDTH": 1280,
    # 窗口高
    "WINDOW_HEIGHT": 720,
    # 跳转窗口宽
    "JUMP_WINDOW_WIDTH": 150,
    # 跳转窗口高
    "JUMP_WINDOW_HEIGHT": 20,
    # 字体A - JetBrains Mono
    "FONT_A": ".\\A.ttf",
    # 图标
    "ICON": "",
    # 识别编码
    "ENCODEINGS": ["gbk", "utf-8"],
    # 提示文本 - 正常
    "HINT_NORMAL": "[←][→] 上下页 | [T] 跳转 | [O] 打开 | [↑][↓] 调整预估阅读速度 | [H] 隐藏操作提示 | [Q] 退出",
    # 提示文本 - Shift
    "HINT_SHIFT": "[←][→] 上下十页 | [↑][↓] 调整预估阅读速度",
    # 提示文本 - 空
    "HINT_EMPTYL": "|",
    "HINT_EMPTYR": "|[H]",
    "HINT_EMPTYP": "█",
    # ===以下为用户设置获取=== #
    "TIME_PER_PAGE": 80,
    # ===以下为系统配置获取=== #
    # 屏幕宽
    "INFO_SCREEN_WIDTH": tk.winfo_screenwidth(),
    # 屏幕高
    "INFO_SCREEN_HEIGHT": tk.winfo_screenheight(),
}

showhint = True
lines = []
rip = []
backup = []
eng_char = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-={}[]|\\:\"';<>?,./`~ ·"
now = 1
full = 0
load = False


def loading():
    global text, status, title, hint
    tk.geometry(
        f"""{CONFIG["WINDOW_WIDTH"]}x{CONFIG["WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["WINDOW_HEIGHT"]) / 2)}"""
    )  # 居中
    tk.resizable(False, False)  # 禁止缩放
    tk.title("")  # 空标题
    tk.iconbitmap(CONFIG["ICON"])  # 图标
    tk.configure(bg="#23272E")  # 背景颜色
    title = Label(
        text="CODEZPC's READER", fg="#767F89", bg="#23272E", font=("JetBrains Mono", 15)
    )  # 里标题
    title.place(x=10, y=10)
    text = Label(
        text="",
        fg="#C8C8C8",
        bg="#23272E",
        width=CONFIG["CHARATERS_PER_LINE"],
        height=CONFIG["LINES_PER_PAGE"],
        font=("黑体", 15),
        justify="left",
        anchor="nw",
    )  # 文本显示
    text.place(x=40, y=40)
    status = Label(
        text="---未打开文本---", fg="#767F89", bg="#23272E", font=("黑体", 12)
    )  # 状态栏
    status.place(x=10, y=665)
    hint = Label(
        text=CONFIG["HINT_NORMAL"],
        fg="#767F89",
        bg="#23272E",
        font=("黑体", 12),
    )  # 操作栏
    hint.place(x=10, y=690)
    version = Label(
        text="1.2", fg="#767F89", bg="#23272E", font=("JetBrains Mono", 5)
    )  # 版本号
    version.place(x=0, y=0)
    # 键盘监听
    tk.bind("<q>", qit)
    tk.bind("<Q>", qit)
    tk.bind("<o>", openfile_th)
    tk.bind("<O>", openfile_th)
    tk.bind("<t>", jump)
    tk.bind("<T>", jump)
    tk.bind("<Control-g>", genlist)
    tk.bind("<Control-G>", genlist)
    tk.bind("<h>", hide)
    tk.bind("<H>", hide)
    tk.bind("<Right>", nextpage)
    tk.bind("<Shift-Right>", nextpagex)
    tk.bind("<Left>", prevpage)
    tk.bind("<Shift-Left>", prevpagex)
    tk.bind("<Up>", addtime)
    tk.bind("<Shift-Up>", addtimex)
    tk.bind("<Down>", minustime)
    tk.bind("<Shift-Down>", minustimex)
    tk.bind("<KeyPress-Shift_L>", hintb)
    tk.bind("<KeyRelease-Shift_L>", hinta)


def openfile_th(event):
    th = threading.Thread(target=openfile)
    th.daemon = True
    th.start()


def loadingui():
    global load
    load = True
    th = threading.Thread(target=updatestatus, args=(1, 1))
    th.daemon = True
    th.start()


# 打开文件
def openfile(event=None):
    global lines, full, file, title, now, status, backup, rip, line_idx, content, load
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", ("*.txt"))])
    if not file_path:
        return
    start = time.time()

    # 读取文件内容（优化编码尝试逻辑）
    content = None
    for encoding in CONFIG["ENCODEINGS"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.readlines()
            backup = content.copy()  # 直接复制内容避免二次读取
            break
        except UnicodeDecodeError:
            continue
    else:
        messagebox.showerror("错误", "无法识别文件编码")
        return

    # 处理行格式（提取为独立逻辑）
    def process_line(line):
        current_line = line
        remaining_length = CONFIG["CHARATERS_PER_LINE"]
        idx = 0
        for char in current_line:
            if char == "\n":
                return current_line[:idx] + " " * remaining_length + "\n", None
            remaining_length -= 1 if char in eng_char else 2
            if remaining_length <= 1:
                next_char = current_line[idx + 1] if idx + 1 < len(current_line) else ""
                if next_char == "\n" or (
                    next_char in eng_char and remaining_length == 1
                ):
                    idx += 1
                    continue
                new_line = current_line[:idx] + "\n"
                remaining_content = current_line[idx:]
                return new_line, remaining_content
            idx += 1
        return current_line, None

    # 主处理循环（优化变量命名与结构）
    processed_lines = []
    current_processed_count = 0
    line_idx = 0
    if os.path.getsize(file_path) > 3000000:
        loadingui()

    for line_idx, line in enumerate(content):
        # 自动填充空行逻辑
        if line.strip() and not line.startswith((" ", "\n", "	")):
            # 计算当前页剩余行数
            remaining_lines = CONFIG["LINES_PER_PAGE"] - (
                current_processed_count % CONFIG["LINES_PER_PAGE"]
            )
            if remaining_lines != CONFIG["LINES_PER_PAGE"]:
                padding = remaining_lines
                processed_lines.extend(["\n"] * padding)
                current_processed_count += padding

        # 处理单行拆分
        while True:
            new_line, remaining = process_line(line)
            processed_lines.append(new_line.rstrip() + "\n")
            current_processed_count += 1  # 每处理一行计数
            if not remaining:
                break
            line = remaining

    lines = processed_lines
    full = math.ceil(len(lines) / CONFIG["LINES_PER_PAGE"])
    now = 1

    # 更新UI状态
    file = os.path.basename(file_path)  # 使用os优化路径处理
    title.configure(text=os.path.splitext(file)[0], font=("黑体", 15))
    rip = [line.rstrip() for line in lines]
    load = False
    update(lines, now)
    updatestatus(now, full)
    end = time.time() - start
    print(end)


def update(txt, page):
    global full
    show = ""
    for i in range(
        (page - 1) * CONFIG["LINES_PER_PAGE"], page * CONFIG["LINES_PER_PAGE"]
    ):
        try:
            show += txt[i]
        except IndexError:
            show += "\n"
    text.configure(text=show)
    updatestatus(now, full)
    if not showhint:
        length = int(math.floor(75 * now / full))
        hint.configure(
            text=CONFIG["HINT_EMPTYL"]
            + length * CONFIG["HINT_EMPTYP"]
            + " " * (150 - 2 * length)
            + CONFIG["HINT_EMPTYR"]
        )


def loadtime(page, all):
    second = (all - page) * CONFIG["TIME_PER_PAGE"]
    minute = second // 60
    hour = minute // 60
    minute %= 60
    return (hour, minute)


def updatestatus(page, all):
    global status, load
    while load:
        status.configure(text=f"加载中...{line_idx/len(content)*100:.3f}%")
        time.sleep(0.1)
    hour, minute = loadtime(page, all)
    text = f"第{now}/{full}页 {round((now/full)*100,3):.3f}%"
    text += " 预计剩余"
    if hour != 0:
        if 0 < hour <= 1200:
            text += f"{hour}小时"
        else:
            text += "1200+小时"
    if 0 <= hour < 20:
        text += f"{minute:02d}分钟"
    text += f" 速度设置为{CONFIG['TIME_PER_PAGE']}秒/页"
    status.configure(text=text)


def nextpage(event):
    global now, full
    if full == 0:
        return
    if now < full:
        now += 1
    else:
        now = 1
    update(lines, now)


def prevpage(event):
    global now, full
    if full == 0:
        return
    if now > 1:
        now -= 1
    else:
        now = full
    update(lines, now)


def nextpagex(event):
    global now, full
    if full == 0:
        return
    if now + 9 < full:
        now += 10
    elif now < full:
        now = full
    else:
        now = 1
    update(lines, now)


def prevpagex(event):
    global now, full
    if full == 0:
        return
    if now - 9 > 1:
        now -= 10
    elif now > 1:
        now = 1
    else:
        now = full
    update(lines, now)


def addtime(event):
    if CONFIG["TIME_PER_PAGE"] < 600:
        CONFIG["TIME_PER_PAGE"] += 1
    if full != 0:
        update(lines, now)


def minustime(event):
    if CONFIG["TIME_PER_PAGE"] > 1:
        CONFIG["TIME_PER_PAGE"] -= 1
    if full != 0:
        update(lines, now)


def addtimex(event):
    if CONFIG["TIME_PER_PAGE"] + 10 <= 600:
        CONFIG["TIME_PER_PAGE"] += 10
    else:
        CONFIG["TIME_PER_PAGE"] = 600
    if full != 0:
        update(lines, now)


def minustimex(event):
    if CONFIG["TIME_PER_PAGE"] - 10 >= 1:
        CONFIG["TIME_PER_PAGE"] -= 10
    else:
        CONFIG["TIME_PER_PAGE"] = 1
    if full != 0:
        update(lines, now)


def hinta(event):
    global hint
    if showhint:
        hint.configure(text=CONFIG["HINT_NORMAL"])


def hintb(event):
    global hint
    if showhint:
        hint.configure(text=CONFIG["HINT_SHIFT"])


def hide(event):
    global showhint
    if showhint:
        showhint = False
        if full != 0:
            length = int(math.floor(75 * now / full))
            hint.configure(
                text=CONFIG["HINT_EMPTYL"]
                + length * CONFIG["HINT_EMPTYP"]
                + " " * (150 - 2 * length)
                + CONFIG["HINT_EMPTYR"]
            )
        else:
            hint.configure(text="")
    else:
        showhint = True
        hint.configure(text=CONFIG["HINT_NORMAL"])


def jump(event):
    def save(event):
        global now, full
        if 1 <= int(entry.get()) <= full:
            now = int(entry.get())
            jumping.destroy()
            update(lines, now)

    jumping = Toplevel(tk)
    jumping.geometry(
        f"""{CONFIG["JUMP_WINDOW_WIDTH"]}x{CONFIG["JUMP_WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["JUMP_WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["JUMP_WINDOW_HEIGHT"]) / 2)}"""
    )  # 居中
    entry = Entry(jumping)
    entry.pack()
    jumping.bind("<Return>", save)


def genlist(event):
    with open("./cont" + file, "w", encoding="utf-8") as f:
        for i in backup:
            if i[0] != " " and i[0] != "\n":
                f.write(f"{i[:-1]} --- {(rip.index(i[:-1])+1)//31+1}\n")


def loadconfig():
    global CONFIG
    if os.path.exists("./userconfig.txt"):
        with open("./userconfig.txt", "r", encoding="utf-8") as f:
            for i in f.readlines():
                if "TIME_PER_PAGE" in i:
                    CONFIG["TIME_PER_PAGE"] = int(i.split("=")[1])


def saveconfig():
    with open("./userconfig.txt", "w", encoding="utf-8") as f:
        f.write(f"TIME_PER_PAGE={CONFIG['TIME_PER_PAGE']}")


# 退出
def qit(event):
    saveconfig()
    tk.destroy()
    exit()


if __name__ == "__main__":
    loadconfig()
    loading()

mainloop()
#II 2895837139
#III 2895820664
#IV 2895739186
#V 2895830434
#TOONE 2538567931
#workshop_download_item 431960
