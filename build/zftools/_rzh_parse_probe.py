# -*- coding: utf-8 -*-
"""Find which lang file(s) fail to parse, and show the tail, so the cause is visible."""
import io
import json
import os

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
out = []
for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
    p = os.path.join(LANG, loc + ".json")
    raw = io.open(p, "rb").read()
    txt = raw.decode("utf-8")
    lines = txt.split("\n")
    try:
        d = json.loads(txt)
        out.append("%-6s OK    keys=%d  lines=%d  bytes=%d" % (loc, len(d), len(lines), len(raw)))
    except Exception as e:                                   # noqa: BLE001
        out.append("%-6s FAIL  %s" % (loc, e))
        out.append("       lines=%d bytes=%d" % (len(lines), len(raw)))
        # show the offending line and neighbours
        import re
        m = re.search(r"line (\d+) column (\d+)", str(e))
        if m:
            n = int(m.group(1))
            for i in range(max(0, n - 3), min(len(lines), n + 2)):
                mark = ">>" if i == n - 1 else "  "
                out.append("%s %4d | %s" % (mark, i + 1, lines[i][:170]))
        out.append("       last 4 lines:")
        for i in range(max(0, len(lines) - 4), len(lines)):
            out.append("         %4d | %s" % (i + 1, lines[i][:170]))
    out.append("")

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_parse_probe.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
