l = ["[CS]传说管理局",
     "[FK]超能：我有一面复刻镜",
     "[GM]诡秘之主",
     "[NJ]女将星",
     "[SR]十日终焉",
     "[UN]夜幕之下",
     "[XS]我不是戏神",
     "[YS]异兽迷城",
     "[ZS]诸神愚戏"
]
b = ["CS·传说管理局.txt",
     "FK·我有一面复刻镜.txt",
     "GM·诡秘之主.txt",
     "NJ·女将星.txt",
     "SR·十日终焉.txt",
     "UN·夜幕之下.txt",
     "XS·我不是戏神.txt",
     "YS·异兽迷城.txt",
     "ZS·诸神愚戏.txt"
]
f = open("FULL.txt","w",encoding="utf-8-sig")
for j in range(1):
     for i in range(9):
          f.write(l[i]+"\n")
          f.write(open(l[i]+"\\"+b[i],"r",encoding="utf-8-sig").read()+"\n")
