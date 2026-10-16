# -*- coding: utf-8 -*-
"""Ground truth for the three keys Z1 still flags: show old (HEAD) vs new (disk),
with repr so whitespace differences are visible."""
import io
import json
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = ROOT + r"\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
KEYS = ["message.potato_s_t.gravity.charging", "message.potato_s_t.gravity.fired",
        "message.potato_s_t.ore_detector.no_power"]

old = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
new = json.load(io.open(LANG + r"\zh_cn.json", encoding="utf-8"))

out = []
for k in KEYS:
    out.append("### %s" % k)
    out.append("  ZH OLD repr: %r" % old[k])
    out.append("  ZH NEW repr: %r" % new[k])
    out.append("  same? %s" % (old[k] == new[k]))
    for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
        d = json.load(io.open(LANG + "\\" + loc + ".json", encoding="utf-8"))
        out.append("  %-6s now : %r" % (loc, d[k]))
    out.append("")

io.open(ROOT + r"\build\zftools\_rzh_gt.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
