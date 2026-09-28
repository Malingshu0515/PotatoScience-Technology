# -*- coding: utf-8 -*-
u"""_zf151_peek.py —— 把挂载后的那几行按 repr 打出来（UTF-8 报告），看有没有隐藏字符。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
p = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"
t = io.open(p, encoding=u"utf-8", newline=u"").read()
lines = t.split(u"\n")
print(u"总行数 %d ；CRLF 数 %d" % (len(lines), t.count(u"\r\n")))
for i in range(86, 94):
    print(u"%3d | %r" % (i + 1, lines[i]))
