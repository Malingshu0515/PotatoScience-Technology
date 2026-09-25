# -*- coding: utf-8 -*-
u"""_zf102_fixdup.py —— 去掉 `_zf74_verify.py` 里被重复插入的 c: 标签条目（一次性清理）

来历：ZF101 那轮的 retarget 被跑了两遍，而它插的是"在某一行为后追加三行" ⇒ 三行被插了两遍。
Python 的字典字面量重复键是合法的（后者胜），所以这条重复一直没被校验抓到 ——
但它是**同一份东西写了两遍**，按工程规矩要清掉。
"""
import io
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf74_verify.py"
text = io.open(P, encoding="utf-8").read()
lines = text.split(u"\n")
seen = set()
out = []
removed = 0
pat = re.compile(r'^\s*u"([a-z_]+\.json)":')
inside = False
for line in lines:
    if u"want = {" in line:
        inside = True
    if inside and line.strip() == u"}":
        inside = False
    m = pat.match(line)
    if inside and m:
        key = m.group(1)
        if key in seen:
            removed += 1
            print(u"  删掉重复条目：%s" % key)
            continue
        seen.add(key)
    out.append(line)
if removed:
    io.open(P, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(out))
print(u"删掉 %d 行重复；剩下的标签 %d 个" % (removed, len(seen)))
