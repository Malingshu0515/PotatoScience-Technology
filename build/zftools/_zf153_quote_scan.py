# -*- coding: utf-8 -*-
u"""扫「中文串里嵌了 ASCII 双引号」的行（用法：python _zf153_quote_scan.py <py 文件>…）。

判据：一行里 `u"…"` 之后又冒出一个 `"`，且这中间有 CJK —— 那就是把字符串提前截断了。
这个坑本会话已经踩了 8 次，写成工具比靠眼睛靠谱。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PAT = re.compile(u'u"[^"]*"[^,)]*[\u4e00-\u9fff][^"]*"')

for p in sys.argv[1:]:
    lines = io.open(p, encoding="utf-8").read().split(u"\n")
    bad = [(i, l) for i, l in enumerate(lines, 1) if PAT.search(l)]
    print(u"\n== %s：可疑 %d 行 ==" % (p, len(bad)))
    for i, l in bad:
        print(u"  %4d | %s" % (i, l.rstrip()))
