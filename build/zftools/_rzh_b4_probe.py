# -*- coding: utf-8 -*-
"""B4 investigation: the check counts the literal two-char sequence backslash-n in the
PARSED values (where escaped newlines became real newlines) -- so it compares 0 to 0 and
can only ever fail when a value contains a literal backslash-n. Show the real state of
the flagged key, and whether B4 has ever been meaningful."""
import io
import json
import os
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = ROOT + r"\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
K = "tooltip.potato_s_t.fluid_converter"

zh = json.load(io.open(LANG + r"\zh_cn.json", encoding="utf-8"))
lzh = json.load(io.open(LANG + r"\lzh.json", encoding="utf-8"))
hzh = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
hlzh = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/lzh.json"],
                                 cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))

L = []
L.append("key: %s" % K)
L.append("")
L.append("zh  HEAD newlines=%d  literal backslash-n=%d" % (hzh[K].count("\n"), hzh[K].count("\\n")))
L.append("zh  now  newlines=%d  literal backslash-n=%d" % (zh[K].count("\n"), zh[K].count("\\n")))
L.append("lzh HEAD newlines=%d  literal backslash-n=%d" % (hlzh[K].count("\n"), hlzh[K].count("\\n")))
L.append("lzh now  newlines=%d  literal backslash-n=%d" % (lzh[K].count("\n"), lzh[K].count("\\n")))
L.append("")
L.append("zh  changed vs HEAD this round? %s" % (zh[K] != hzh[K]))
L.append("lzh changed vs HEAD this round? %s" % (lzh[K] != hlzh[K]))
L.append("")
L.append("B4 rule as written = `zv.count('\\\\n') != lv.count('\\\\n')` -- counts the two-character")
L.append("sequence backslash+n in ALREADY-PARSED strings, so it is 0 on both sides unless a value")
L.append("contains a literal backslash-n. On parsed values the meaningful check is `.count(chr(10))`.")
L.append("")
L.append("=== real newline-count mismatches zh vs lzh across the whole file (the check B4 MEANT) ===")
mism = [(k, zh[k].count("\n"), lzh[k].count("\n")) for k in zh if k in lzh and zh[k].count("\n") != lzh[k].count("\n")]
L.append("件数 = %d" % len(mism))
for k, a, b in mism[:20]:
    L.append("   %-52s zh=%d lzh=%d" % (k, a, b))
L.append("")
L.append("=== raw text of the flagged key (zh, then lzh) ===")
L.append("zh : %r" % zh[K])
L.append("lzh: %r" % lzh[K])
io.open(ROOT + r"\build\zftools\_rzh_b4_probe.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
