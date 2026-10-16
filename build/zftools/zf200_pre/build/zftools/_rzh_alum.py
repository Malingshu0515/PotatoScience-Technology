# -*- coding: utf-8 -*-
"""How widespread is 'aluminium' vs 'aluminum' in en_us now, and where?"""
import io
import json
import os

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "en_us.json"), encoding="utf-8"))

out = []
for needle in ("aluminium", "aluminum", "Aluminium", "Aluminum"):
    hits = [(k, v.count(needle)) for k, v in d.items() if needle in v]
    out.append("%-10s total=%d  keys=%d" % (needle, sum(c for _, c in hits), len(hits)))
out.append("")
out.append("=== keys carrying either spelling ===")
for k, v in d.items():
    if "luminium" in v or "luminum" in v:
        i = max(v.find("luminium"), v.find("luminum"))
        out.append("%-56s ...%s..." % (k, v[max(0, i - 40):i + 30]))
io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_alum.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
