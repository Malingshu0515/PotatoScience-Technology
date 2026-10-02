# -*- coding: utf-8 -*-
"""_zf133_parentfix13.py —— 清掉 `enderWho` 的残留引用与赋值（字段已被替换成血量快照）"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

s = io.open(CHK, encoding="utf-8").read()
before = s.count("enderWho")

# 删掉赋值块
s = s.replace("""        if (!who.contains("末影人") && !who.contains("Ender")) {
            enderWho = who;   // 记下"不是末影人的那个"（末地龙），断言用它
        }
""", "")
# 删掉打印行
s = re.sub(r"\n *say\(TAG \+ \"      \[DMG-OK\] 打中的实体 = \" \+ enderWho\);", "", s)

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
after = io.open(CHK, encoding="utf-8").read().count("enderWho")
print("enderWho 引用：%d -> %d" % (before, after))
