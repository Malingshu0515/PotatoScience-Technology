# -*- coding: utf-8 -*-
"""Round 3 recon: what does the user's zh_cn change (vs HEAD), and what guide/
config keys exist now, and where is the Patchouli book defined?"""
import io
import json
import os
import re
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
REL = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_user3_diff.txt")

old = json.loads(subprocess.run([GIT, "show", "HEAD:" + REL], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode("utf-8"))
new = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))

data = {}
for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
    data[loc] = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))

added = [k for k in new if k not in old]
removed = [k for k in old if k not in new]
changed = [k for k in new if k in old and old[k] != new[k]]

L = []
L.append("# zh_cn vs HEAD")
L.append("# old=%d new=%d added=%d removed=%d changed=%d"
         % (len(old), len(new), len(added), len(removed), len(changed)))
L.append("")
if added:
    L.append("## ADDED (%d)" % len(added))
    for k in added:
        L.append("+ %s" % k)
        L.append("    ZH: %s" % new[k].replace("\n", "\\n"))
        for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
            v = data[loc].get(k)
            L.append("    %-6s: %s" % (loc, "<MISSING>" if v is None else v.replace("\n", "\\n")))
    L.append("")
if removed:
    L.append("## REMOVED (%d)" % len(removed))
    for k in removed:
        L.append("- %s" % k)
    L.append("")
if changed:
    L.append("## CHANGED (%d)" % len(changed))
    for i, k in enumerate(changed, 1):
        L.append("[%02d] %s" % (i, k))
        L.append("   OLD: %s" % old[k].replace("\n", "\\n"))
        L.append("   NEW: %s" % new[k].replace("\n", "\\n"))
        for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
            v = data[loc].get(k)
            L.append("   %-6s: %s" % (loc, "<MISSING>" if v is None else v.replace("\n", "\\n")))
    L.append("")

L.append("## all guide.* / config-ish keys in zh_cn")
for k in sorted(new):
    if ("guide" in k.lower() or "config" in k.lower() or k.startswith("potato_s_t.")):
        L.append("  %-62s %s" % (k, new[k].replace("\n", "\\n")[:120]))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("added=%d removed=%d changed=%d -> %s" % (len(added), len(removed), len(changed), OUT))
