# -*- coding: utf-8 -*-
"""What number style does each locale actually use in FE values and counts?
This decides how the G4 fact table must be written (and what the lzh translator must do)."""
import io
import json
import os
import re

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
OUT = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_numstyle.txt"

CN = "零一二三四五六七八九十百千萬万兩两"
out = []
for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    fe = [v for v in d.values() if "FE" in v]
    arabic = sum(1 for v in fe if re.search(r"[0-9]\s*FE", v))
    han = sum(1 for v in fe if re.search(r"[%s]+\s*FE" % CN, v))
    out.append("%-6s 含 FE 的值 %d 条：阿拉伯数字 %d 条 / 汉字数字 %d 条"
               % (loc, len(fe), arabic, han))
    # sample
    for v in fe[:4]:
        m = re.search(r"[^\s]{0,12}FE", v)
        out.append("      ...%s" % (m.group(0) if m else v[:20]))
    out.append("")

out.append("=== lzh 里汉字数字的样例（用于确认写法）===")
d = json.load(io.open(os.path.join(LANG, "lzh.json"), encoding="utf-8"))
for k, v in list(d.items()):
    if k.startswith("potato_s_t.guide") and re.search(r"[%s]" % CN, v):
        out.append("  %-58s %s" % (k.split(".")[-2:], v[:110]))
io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
