# -*- coding: utf-8 -*-
"""Dump the current values of the user-touched zh keys in all target locales.

Purpose: before writing translations I need the exact on-disk text of
en_us / ja_jp / ru_ru / lzh for the 81 keys the user hand-edited in zh_cn.
Nothing is hand-copied anywhere in this pipeline.
"""
import io
import json
import os
import subprocess

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
REL = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_user_zh_targets.txt")

old = json.loads(subprocess.run([GIT, "show", "HEAD:" + REL], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode("utf-8"))
new = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
zh_old = {k: old[k] for k in new if k in old and old[k] != new[k]}
order = [k for k in new if k in zh_old]

def load(loc):
    return json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))

data = {loc: load(loc) for loc in ("en_us", "ja_jp", "ru_ru", "lzh")}

# group by category for readability
def cat(k):
    if k.startswith("advancements."):
        return "ACHIEVEMENT"
    if k.startswith("gui."):
        return "GUI-STATUS"
    if k.startswith("message.") or k.startswith("death."):
        return "MESSAGE"
    if k.startswith("item."):
        return "ITEM-NAME"
    return "TOOLTIP"

lines = []
lines.append("# keys hand-edited by user in zh_cn.json -- target values BEFORE my pass")
lines.append("# total = %d" % len(order))
curcat = None
for k in order:
    c = cat(k)
    if c != curcat:
        lines.append("")
        lines.append("=" * 70)
        lines.append("## %s" % c)
        lines.append("=" * 70)
        curcat = c
    lines.append("")
    lines.append("### %s" % k)
    lines.append("ZH-OLD: %s" % zh_old[k].replace("\n", "\\n"))
    lines.append("ZH-NEW: %s" % new[k].replace("\n", "\\n"))
    for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
        v = data[loc].get(k)
        if v is None:
            lines.append("%-6s: <MISSING>" % loc)
        else:
            lines.append("%-6s: %s" % (loc, v.replace("\n", "\\n")))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("keys=%d -> %s" % (len(order), OUT))

# also: any zh key that is now EMPTY, or that broke a placeholder
print("\n-- structural sanity of zh NEW values --")
import re
for k in order:
    v = new[k]
    po = set(re.findall(r"%[0-9$]*s", old[k]))
    pn = set(re.findall(r"%[0-9$]*s", v))
    if po != pn:
        print("PLACEHOLDER %s: %s -> %s" % (k, sorted(po), sorted(pn)))
    if v.strip() == "":
        print("EMPTY       %s" % k)
    if v != v.rstrip():
        print("TRAILSPACE  %s" % k)
    if "  " in v.replace("\n", ""):
        print("DBLSPACE    %s" % k)
