import os

a = "　　"  # 全角空格
b = "  "   # 半角空格（两个空格）
c = "\n  \n"
d = "\n"
e = " (第1/2页)"

# 遍历当前目录所有文件
for filename in os.listdir('.'):
    # 只处理txt文件
    if filename.endswith('.txt'):
        with open(filename, 'r', encoding="UTF-8") as file:
            content = file.read()
        
        # 执行替换操作
        content = content.replace(a, b)
        content = content.replace(c, d)
        c="\n\n"
        content = content.replace(c, d)
        content = content.replace(e, "")
        
        # 写回原文件
        with open(filename, 'w', encoding="UTF-8") as file:
            file.write(content)
