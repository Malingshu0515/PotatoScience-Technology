# -*- coding: utf-8 -*-
"""_zf133_dump.py —— 打印原始日志的指定行区间（默认末地那一场）。

用法：
    python build\\zftools\\_zf133_dump.py 4380 4420
结果同时写到 build\\zftools\\_zf133_dump.txt（UTF-8）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LOG = os.path.join(ROOT, r"build\zftools\_zf133_runSrv.log")

a = int(sys.argv[1]) if len(sys.argv) > 1 else 4380
b = int(sys.argv[2]) if len(sys.argv) > 2 else 4420

body = io.open(LOG, encoding="utf-8", errors="replace").read().split("\n")
OUT = io.open(os.path.join(ROOT, r"build\zftools\_zf133_dump.txt"),
              "w", encoding="utf-8", errors="replace")
OUT.write("源日志：%s，行 %d..%d\n" % (LOG, a, b))
for i in range(a, min(b, len(body)) + 1):
    OUT.write("%6d| %s\n" % (i, body[i - 1].rstrip()))
OUT.close()
print("done -> _zf133_dump.txt")
