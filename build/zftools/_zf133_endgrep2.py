# -*- coding: utf-8 -*-
"""_zf133_endgrep2.py —— 只看 (h) 末地场景：从 [A133] 的 (h) 段开始，到 T_F 之前。

用法：
    python build\\zftools\\_zf133_endgrep2.py
结果写到 build\\zftools\\_zf133_endgrep2.txt（UTF-8）。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LOG = os.path.join(ROOT, r"build\zftools\_zf133_runSrv.log")

body = io.open(LOG, encoding="utf-8", errors="replace").read().split("\n")
OUT = io.open(os.path.join(ROOT, r"build\zftools\_zf133_endgrep2.txt"),
              "w", encoding="utf-8", errors="replace")
OUT.write("源日志：%s（共 %d 行）\n" % (LOG, len(body)))


def w(s):
    OUT.write(s + "\n")


w("")
w("========== 含 A133 / zf133end / 末影人 / DMG / tick exception 的行 ==========")
for i, line in enumerate(body, 1):
    if re.search(r"A133|zf133end|末影人|\[DMG\]|tick exception", line):
        w("%6d| %s" % (i, line.rstrip()))

w("")
w("========== dim=minecraft:the_end 的 TRLOOP / TRENTRY 行 ==========")
n = 0
for i, line in enumerate(body, 1):
    if "the_end" in line and ("TRLOOP" in line or "TRENTRY" in line):
        w("%6d| %s" % (i, line.rstrip()))
        n += 1
        if n > 40:
            w("     ... （截断）")
            break
w("共 %d 行" % n)
OUT.close()
print("done")
