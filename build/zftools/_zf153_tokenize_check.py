# -*- coding: utf-8 -*-
u"""用 tokenize 精确定位未闭合的字符串/括号（比数引号靠谱）。"""
import io
import sys
import tokenize

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf153_verify.py"
src = io.open(P, encoding="utf-8").read()

stack = []
try:
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.OP:
            if tok.string in u"([{":
                stack.append(tok)
            elif tok.string in u")]}":
                if stack:
                    stack.pop()
except Exception as e:
    print(u"tokenize 报错：%r" % (e,))

if stack:
    lines = src.split(u"\n")
    for tok in stack:
        print(u"未闭合：第 %d 行第 %d 列的 %r" % (tok.start[0], tok.start[1], tok.string))
        for i in range(max(1, tok.start[0] - 1), min(len(lines), tok.start[0] + 8) + 1):
            print(u"  %4d | %s" % (i, lines[i - 1]))
        print(u"")
else:
    print(u"括号全平")
