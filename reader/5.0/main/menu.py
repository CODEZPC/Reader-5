from imports import *


class ReaderMenu:
    """ESC 菜单 —— 全屏覆盖 Frame，居中排列 FLAT 按钮，悬停添加装饰箭头"""

    def __init__(self, parent, reader):
        self.parent = parent
        self.reader = reader
        self.visible = False

        self.frame = Frame(parent, bg=reader.color_bg)

        # 顶部弹簧
        top_spacer = Frame(self.frame, bg=reader.color_bg)
        top_spacer.pack(expand=True)

        # 按钮容器 —— 保证按钮垂直居中
        btn_container = Frame(self.frame, bg=reader.color_bg)
        btn_container.pack(expand=False)

        self._create_button(btn_container, "继续阅读", self.hide)
        self._create_button(btn_container, "打开文件", self._open_file)
        self._create_button(btn_container, "跳转页码", self._jump_page)
        self._create_button(btn_container, "退出", self._exit_app)

        # 底部弹簧
        bottom_spacer = Frame(self.frame, bg=reader.color_bg)
        bottom_spacer.pack(expand=True)

    def _create_button(self, container, text, command):
        btn = Button(
            container,
            text=text,
            font=self.reader.font_status,
            fg=self.reader.color_fg,
            bg=self.reader.color_bg,
            activeforeground=self.reader.color_fg,
            activebackground="#3A3F4B",
            relief=FLAT,
            bd=0,
            command=command,
            cursor="hand2",
            padx=20,
            pady=6,
        )
        btn.pack()
        btn.bind("<Enter>", lambda e, b=btn, t=text: b.config(text=f">  {t}  <"))
        btn.bind("<Leave>", lambda e, b=btn, t=text: b.config(text=t))

    def show(self):
        if not self.visible:
            self.frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.frame.lift()
            self.frame.focus_set()
            self.visible = True

    def hide(self):
        if self.visible:
            self.frame.place_forget()
            self.visible = False

    def _open_file(self):
        self.hide()
        self.reader.open_file()

    def _jump_page(self):
        self.hide()
        self.reader.jump_page_dialog()

    def _exit_app(self):
        self.parent.destroy()