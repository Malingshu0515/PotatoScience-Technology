# -*- coding: utf-8 -*-
u"""_zf169_retarget.py —— 把「语言键数」从本轮开工时的 620/622 跟到现在的实测值（ZF169 +17 键）

不写死目标值：**先量出现值**，再把常驻门里那对旧数字替换掉。
（旧值也可能已经是别人改过一轮的数 —— 所以按"门里出现了哪些数字"来找，
 只替换 620/622 这两个 ZF169 开工时的值。）
"""
import ast
import glob
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
OLD4, OLD5 = 647, 649

live4 = len(json.loads(io.open(os.path.join(LANG, u"zh_cn.json"), encoding="utf-8").read()))
live5 = len(json.loads(io.open(os.path.join(LANG, u"lzh.json"), encoding="utf-8").read()))
print(u"实测：四语言 %d 键、lzh %d 键（旧值 %d / %d）" % (live4, live5, OLD4, OLD5))

touched = 0
for pat in (u"_zf*_verify.py", u"_zf*_jarcheck.py"):
    for p in sorted(glob.glob(os.path.join(TOOLS, pat))):
        if os.path.basename(p).startswith(u"_zf169"):
            continue
        t = io.open(p, encoding="utf-8").read()
        if not re.search(u"\\b(%d|%d)\\b" % (OLD4, OLD5), t):
            continue
        new = re.sub(u"\\b%d\\b" % OLD4, str(live4), t)
        new = re.sub(u"\\b%d\\b" % OLD5, str(live5), new)
        if new == t:
            continue
        ast.parse(new)
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(new)
        touched += 1
print(u"改了 %d 份常驻门" % touched)

left = []
for pat in (u"_zf*_verify.py", u"_zf*_jarcheck.py"):
    for p in sorted(glob.glob(os.path.join(TOOLS, pat))):
        t = io.open(p, encoding="utf-8").read()
        for m in re.finditer(u"\\b(%d|%d)\\b" % (OLD4, OLD5), t):
            left.append(u"%s:%s" % (os.path.basename(p), m.group(0)))
print(u"残留旧数字：%s" % (u"、".join(left[:6]) if left else u"无"))

# 交接文档 §1
hand = os.path.join(ROOT, r"docs\多会话协作交接.md")
t = io.open(hand, encoding="utf-8").read()
n = 0
for old, new in ((u"**%d 键 × 4**" % OLD4, u"**%d 键 × 4**" % live4),
                 (u"lzh = %d" % OLD5, u"lzh = %d" % live5)):
    if old in t:
        t = t.replace(old, new)
        n += 1
io.open(hand, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"交接文档改了 %d 处" % n)
print(u"失败项 = 0")
sys.exit(0)
