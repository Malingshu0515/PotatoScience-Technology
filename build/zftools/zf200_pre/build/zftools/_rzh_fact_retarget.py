# -*- coding: utf-8 -*-
"""For the G4 facts that fail, print the ACTUAL on-disk text of the target key in every
locale plus whether the Chinese needle's number is present in some form. Used to retarget
the fact table at real strings instead of guessed formatting."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_guide_verify as V                             # noqa: E402

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
data = {l: json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8"))
        for l in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh")}

seen = set()
out = []
for loc, key, needle, why in V.FACTS:
    v = data[loc].get(key, "")
    if needle in v:
        continue
    if (key, why) in seen:
        continue
    seen.add((key, why))
    out.append("### %s   [%s]" % (key, why))
    out.append("  zh    : %s" % data["zh_cn"].get(key, "")[:300])
    for l in ("en_us", "ja_jp", "ru_ru", "lzh"):
        mark = "FAIL" if (l == loc) else "    "
        out.append("  %s %-6s: %s" % (mark, l, data[l].get(key, "")[:300]))
    out.append("")

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_fact_retarget.txt", "w",
        encoding="utf-8", newline="\n").write("\n".join(out))
print("keys to inspect = %d" % len(seen))
