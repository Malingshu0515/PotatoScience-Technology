# -*- coding: utf-8 -*-
u"""_zf80_probefix.py —— 探针自己的编译错误：枚举不能传给 eq(String, long, long)

只改探针（build/zftools/check/FillingOilCheck.java），不碰生产代码。
做法：把「参数里带枚举常量」的那些 eq( 改成 eqEnum(，并补一个 eqEnum 帮助方法。
      —— 不靠 javac 报的行号（那份是 src 里的副本，且和 check 副本的行号对不上，
         第一版就是按行号改的，结果第 365 行没有 eq( 直接中止），改成按内容定位。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\check\FillingOilCheck.java"

text = io.open(P, encoding="utf-8").read()

# 按「调用」定位，不按行：4 处枚举断言是跨行的（eq( 在上一行、枚举在下一行），
# 第一版按行找只改到 7 处、编译报的还是 11 处。
hit = 0
i = 0
while True:
    j = text.find(u"eq(", i)
    if j < 0:
        break
    k = j + 3
    depth = 1
    while depth > 0 and k < len(text):
        if text[k] == u"(":
            depth += 1
        elif text[k] == u")":
            depth -= 1
        k += 1
    args = text[j + 3:k - 1]
    if u"PourResult." in args or u"SlotState." in args:
        text = text[:j] + u"eqEnum(" + text[j + 3:]
        hit += 1
        i = j + 7
    else:
        i = j + 3

if u"private static void eqEnum(" not in text:
    anchor = u"    private static void eq(String label, long expected, long actual) {"
    add = (u"    /** 枚举/对象的相等断言（枚举不能传给 long 版的 eq）。 */\n"
           u"    private static void eqEnum(String label, Object expected, Object actual) {\n"
           u"        ok(label + \"（期望 \" + expected + \"，实际 \" + actual + \"）\",\n"
           u"                java.util.Objects.equals(expected, actual));\n"
           u"    }\n\n")
    if anchor not in text:
        print(u"  !! 找不到 eq 的定义，中止")
        sys.exit(1)
    text = text.replace(anchor, add + anchor, 1)

io.open(P, "w", encoding="utf-8", newline=u"").write(text)
print(u"改了几处 eq( → eqEnum(：%d（并补了 eqEnum 方法）" % hit)
sys.exit(0 if hit == 11 else 1)
