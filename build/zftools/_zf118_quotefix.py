# -*- coding: utf-8 -*-
u"""_zf118_quotefix.py —— 一次性小工具：把 `_zf118_verify.py` 里几处 ASCII 双引号换成「」

（§4.24 族：中文串里不许出现 ASCII 引号。这次是我自己在**校验器源码**里犯的，
`python -c` 一跑就 SyntaxError。改完立刻回读 + compile。）
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf118_verify.py"

PAIRS = [
    (u'check(u"E4 报告里验过"形状匹配"（照着图纸摆一遍能匹配到这条配方）",',
     u'check(u"E4 报告里验过「形状匹配」（照着图纸摆一遍能匹配到这条配方）",'),
    (u'check(u"E6 报告里验过"合成出来的东西真能点亮星轨坠那条进度"",',
     u'check(u"E6 报告里验过「合成出来的东西真能点亮星轨坠那条进度」",'),
    (u'check(u"F3 _zf118_newfiles.txt 记着"本轮开始前不该存在"的路径",',
     u'check(u"F3 _zf118_newfiles.txt 记着「本轮开始前不该存在」的路径",'),
]

fails = []
raw = io.open(P, encoding="utf-8").read()
for old, new in PAIRS:
    if new in raw:
        print(u"  [--]   已经是「」：%s" % new[:40])
        continue
    n = raw.count(old)
    if n != 1:
        fails.append(u"锚点出现 %d 次：%s" % (n, old[:60]))
        continue
    raw = raw.replace(old, new, 1)
    print(u"  [OK]   %s" % new[:60])
io.open(P, "w", encoding="utf-8", newline=u"").write(raw)
try:
    compile(raw, P, "exec")
    print(u"  [OK]   改完 compile 通过")
except SyntaxError as e:
    fails.append(u"compile 失败：%s" % e)
print(u"失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
