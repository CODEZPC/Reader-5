from tkinter import *
from tkinter import filedialog, messagebox

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
    # 字体A - JetBrains Mono
    "FONT_A": ".\\A.ttf",
    # 图标
    "ICON": "",
    # 识别编码
    "ENCODEINGS": ["gbk", "utf-8"],
    # ===以下为系统配置获取=== #
    # 屏幕宽
    "INFO_SCREEN_WIDTH": tk.winfo_screenwidth(),
    # 屏幕高
    "INFO_SCREEN_HEIGHT": tk.winfo_screenheight(),
}

lines = []
eng_char = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-={}[]|\\:\"';<>?,./`~ ·"
now = 0
full = 0


def loading():
    global text, status, title, hint
    tk.geometry(
        f"""{CONFIG["WINDOW_WIDTH"]}x{CONFIG["WINDOW_HEIGHT"]}+{int((CONFIG["INFO_SCREEN_WIDTH"] - CONFIG["WINDOW_WIDTH"]) / 2)}+{int((CONFIG["INFO_SCREEN_HEIGHT"] - CONFIG["WINDOW_HEIGHT"]) / 2)}"""
    )  # 居中
    tk.resizable(0, 0)  # 禁止缩放
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
    )  # 文本显示
    text.place(x=40, y=40)
    status = Label(
        text="---未打开文本---", fg="#767F89", bg="#23272E", font=("黑体", 12)
    )  # 状态栏
    status.place(x=10, y=665)
    hint = Label(
        text="[←] 上一页 | [→] 下一页 | [T] 跳转 | [O] 打开 | [Q] 退出",
        fg="#767F89",
        bg="#23272E",
        font=("黑体", 12),
    )  # 操作栏
    hint.place(x=10, y=690)
    version = Label(
        text="1.0", fg="#767F89", bg="#23272E", font=("JetBrains Mono", 5)
    )  # 版本号
    version.place(x=0, y=0)
    # 键盘监听
    tk.bind("<q>", qit)
    tk.bind("<Q>", qit)
    tk.bind("<o>", openfile)
    tk.bind("<O>", openfile)
    tk.bind("<t>", jump)
    tk.bind("<T>", jump)
    tk.bind("<Right>", nextpage)
    tk.bind("<Shift-Right>", nextpagex)
    tk.bind("<Left>", prevpage)
    tk.bind("<Shift-Left>", prevpagex)
    tk.bind("<KeyPress-Shift_L>", hintb)
    tk.bind("<KeyRelease-Shift_L>", hinta)


# 打开文件
def openfile(event):
    global lines, full, file, title, now
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        for encoding in CONFIG["ENCODEINGS"]:
            try:
                lines = open(file_path, "r", encoding=encoding).readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            messagebox.showerror("错误", "无法识别文件编码")
            return
        idxl = 0
        for i in lines:
            length = CONFIG["CHARATERS_PER_LINE"]
            idx = 0
            for j in i:
                if j in eng_char:
                    length -= 1
                elif j == "\n":
                    lines[idxl] = i[0:idx] + length * " " + "\n"
                    break
                else:
                    length -= 2
                if length <= 1:
                    if (i[idx + 1] == "\n") or (i[idx + 1] in eng_char and length == 1):
                        idx += 1
                        continue
                    lines[idxl] = i[0:idx] + "\n"
                    lines.insert(idxl + 1, i[idx:])
                    break
                idx += 1
            idxl += 1
        while full * CONFIG["LINES_PER_PAGE"] < len(lines):
            full += 1
        file = file_path
        while "/" in file:
            file = file[file.index("/") + 1 :]
        title.configure(text=file[:-4], font=("黑体", 15))
        now = 1
        update(lines, 1)


def update(txt, page):
    global full
    show = ""
    for i in range(
        (page - 1) * CONFIG["LINES_PER_PAGE"], page * CONFIG["LINES_PER_PAGE"] - 1
    ):
        try:
            show += txt[i]
        except IndexError:
            show += "\n"
    text.configure(text=show)
    status.configure(text=f"第{page}/{full}页")


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


def hinta(event):
    global hint
    hint.configure(text="[←] 上一页 | [→] 下一页 | [T] 跳转 | [O] 打开 | [Q] 退出")


def hintb(event):
    global hint
    hint.configure(text="[←] 上十页 | [→] 下十页")


def jump():
    # TODO JUMP PAGE
    pass


# 退出
def qit(event):
    exit(0)


if __name__ == "__main__":
    loading()

mainloop()
