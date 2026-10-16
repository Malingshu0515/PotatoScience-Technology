# -*- coding: utf-8 -*-
"""Side-by-side of this round's keys: zh (reference, read-only) vs the four targets."""
import io
import json
import os
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = ROOT + r"\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
OUT = ROOT + r"\build\zftools\_rzh_ztrans2_show.txt"

old = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
new = json.load(io.open(LANG + r"\zh_cn.json", encoding="utf-8"))
changed = [k for k in new if k in old and old[k] != new[k]]

d = {}
for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
    d[loc] = json.load(io.open(LANG + "\\" + loc + ".json", encoding="utf-8"))

L = ["# 本轮：用户改了中文 %d 键；下方是四语跟随后的结果（中文只作参考，未改动）" % len(changed), ""]
for i, k in enumerate(changed, 1):
    L.append("[%02d] %s" % (i, k))
    L.append("   zh   (参考): %s" % new[k].replace("\n", "\\n"))
    for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
        L.append("   %-6s     : %s" % (loc, d[loc][k].replace("\n", "\\n")))
    L.append("")

L.append("=== 拼写收口：guide 三条的 aluminium → aluminum ===")
for k in ("potato_s_t.guide.entry.power.storage.p2",
          "potato_s_t.guide.entry.materials.ore_chain.p1",
          "potato_s_t.guide.entry.materials.ore_chain.p2"):
    v = d["en_us"][k]
    L.append("   %s" % k)
    L.append("      aluminium=%d  aluminum=%d" % (v.count("aluminium"), v.count("aluminum")))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("changed=%d -> %s" % (len(changed), OUT))
