# -*- coding: utf-8 -*-
u"""_zf158_gatediff.py —— 对比 ZF156 与 ZF158 两次全门快照的红名单（只读）。"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"


def reds(path):
    if not os.path.isfile(path):
        return None, u""
    text = io.open(path, encoding="utf-8", errors="replace").read()
    out, inred = set(), False
    for line in text.split(u"\n"):
        if line.startswith(u"---- 红的"):
            inred = True
            continue
        if line.startswith(u"---- 绿的") or line.startswith(u"---- 不在盘上"):
            inred = False
            continue
        if inred:
            m = re.match(u"\\s{2}!!\\s+(_[A-Za-z0-9_]+\\.py|_[A-Za-z0-9_]+\\.ps1)\\s*$|"
                         u"\\s{2}!!\\s+(_[A-Za-z0-9_]+\\.py)\\s", line)
            if m:
                out.add(m.group(1) or m.group(2))
    head = re.search(u"绿 = \\d+\\s+红 = \\d+\\s+不存在 = \\d+", text)
    return out, (head.group(0) if head else u"")


a, ha = reds(os.path.join(ZT, u"_zf156_gatesnap.txt"))
b, hb = reds(os.path.join(ZT, u"_zf158_gatesnap.txt"))
if a is None or b is None:
    print(u"!! 缺快照：ZF156=%s ZF158=%s" % (a is not None, b is not None))
    sys.exit(1)
print(u"ZF156：%s" % ha)
print(u"ZF158：%s" % hb)
new, fixed = sorted(b - a), sorted(a - b)
print(u"\n新增的红（%d 条）：%s" % (len(new), u", ".join(new) if new else u"无"))
print(u"变绿的（%d 条）：%s" % (len(fixed), u", ".join(fixed) if fixed else u"无"))
print(u"两轮都红（%d 条，历史账）" % len(a & b))
