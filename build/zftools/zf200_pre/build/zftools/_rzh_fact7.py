# -*- coding: utf-8 -*-
"""Show the actual text at the 7 remaining fact failures so the fact table (or the
translation) can be corrected on evidence rather than guesswork."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_guide_verify as V                             # noqa: E402

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
data = {l: json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8"))
        for l in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh")}

out = []
seen = set()
for loc, key, needle, why in V.FACTS:
    v = data[loc].get(key, "")
    if needle in v or (key, why) in seen:
        continue
    seen.add((key, why))
    out.append("### %s   [%s]" % (key, why))
    out.append("  期望(%s): %r" % (loc, needle))
    for l in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
        out.append("  %-6s: %s" % (l, data[l].get(key, "")[:260]))
    out.append("")

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_fact7.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("cases=%d" % len(seen))
