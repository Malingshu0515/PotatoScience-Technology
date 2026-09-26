# -*- coding: utf-8 -*-
u"""_zf142_quotefind.py —— 找出「中文字符串里混了 ASCII 双引号」的位置

本工程的老坑（§4.146 那条记的就是它）：`u"...是"扇子"..."` 会把字符串提前截断，
Python 报的是"Perhaps you forgot a comma?"，**指向的行还是对的，但原因看着完全不搭**。
这个脚本直接把人肉找的活干掉：扫每一行，凡是一个 ASCII `"` 的两侧**有一侧是中文字符**，
就说明它是混在正文里的，不是字符串边界。
"""
import io
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

for path in sys.argv[1:]:
    lines = io.open(path, encoding="utf-8").read().split("\n")
    n = 0
    for i, l in enumerate(lines, 1):
        for m in re.finditer(r'"', l):
            j = m.start()
            prev = l[j - 1] if j > 0 else ""
            nxt = l[j + 1] if j + 1 < len(l) else ""
            if (prev and ord(prev) > 127) or (nxt and ord(nxt) > 127):
                n += 1
                print(u"%s:%d  %s" % (path, i, l[max(0, j - 28):j + 28]))
    print(u"%s：混进正文的 ASCII 双引号 %d 处" % (path, n))
