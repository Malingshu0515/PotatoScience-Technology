# -*- coding: utf-8 -*-
u"""临时：把交接 §1 成品行（第 22 行）的原样内容写成 UTF-8 报告，供人眼核对有没有被吃字符。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
HAND = r"E:\PotatoST\docs\多会话协作交接.md"
OUT = r"E:\PotatoST\build\zftools\_zf156_handline.txt"
h = io.open(HAND, encoding="utf-8").read()
lines = h.split(u"\n")
found = [i for i, l in enumerate(lines) if u"已发布成品" in l]
with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    for i in found:
        fh.write(u"行号 %d\n" % (i + 1))
        fh.write(u"repr: " + repr(lines[i]) + u"\n")
        fh.write(u"原样:\n" + lines[i] + u"\n")
print(u"写了 %s（命中 %d 行）" % (OUT, len(found)))
