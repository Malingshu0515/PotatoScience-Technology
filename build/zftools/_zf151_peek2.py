# -*- coding: utf-8 -*-
u"""_zf151_peek2.py —— 找"javac 眼中第 91 行"与我眼中第 91 行为什么对不上：
Java 的行终止符比 Python 的 `\\n` 多（`\\r`、`\\u2028`、`\\u2029`、`\\u0085`、`\\f` 等）。
"""
import io
import sys
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
p = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"
t = io.open(p, encoding=u"utf-8", newline=u"").read()
print(u"Python 视角：%d 行" % (len(t.split(u"\n"))))
weird = {u"\u2028": u"LINE SEPARATOR", u"\u2029": u"PARAGRAPH SEPARATOR",
         u"\u0085": u"NEL", u"\x0b": u"VT", u"\x0c": u"FF", u"\r": u"CR"}
for ch, name in weird.items():
    n = t.count(ch)
    if n:
        print(u"  含有 %s（%s）× %d" % (repr(ch), name, n))
        i = t.find(ch)
        print(u"    第一次出现在字符 %d，上下文：%r" % (i, t[max(0, i - 60):i + 60]))
        # 报告它前面有多少个 \n（= 在第几行）
        print(u"    它前面有 %d 个 \\n（约第 %d 行）" % (t[:i].count(u"\n"), t[:i].count(u"\n") + 1))
if not any(t.count(c) for c in weird):
    print(u"  没有这些额外行终止符")
