# -*- coding: utf-8 -*-
"""Dump the user's own zh_cn.json edits (HEAD vs working tree) AND the current values
of those keys in the four target locales, so translations can be written against the
exact on-disk text. Nothing is hand-copied: the old side comes from `git show HEAD:`.

Also runs structural sanity on the user's new zh values (placeholders / empty / stray ws)
and reports any key whose value the user left byte-identical to HEAD.
"""
import io
import json
import os
import re
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
REL = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_user2_diff.txt")

old_raw = subprocess.run([GIT, "show", "HEAD:" + REL], cwd=ROOT,
                         capture_output=True, check=True).stdout.decode("utf-8")
old = json.loads(old_raw)
new = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))

base = subprocess.run([GIT, "rev-parse", "--short", "HEAD"], cwd=ROOT,
                      capture_output=True, check=True).stdout.decode().strip()

added = [k for k in new if k not in old]
removed = [k for k in old if k not in new]
changed = [k for k in new if k in old and old[k] != new[k]]

data = {}
for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
    data[loc] = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))

L = []
L.append("# zh_cn.json user edits vs %s" % base)
L.append("# old keys=%d  new keys=%d  added=%d  removed=%d  changed=%d"
         % (len(old), len(new), len(added), len(removed), len(changed)))
L.append("")

if added:
    L.append("## ADDED KEYS (user added -- targets probably missing too)")
    for k in added:
        L.append("+ %s" % k)
        L.append("    ZH NEW: %s" % new[k].replace("\n", "\\n"))
        for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
            v = data[loc].get(k)
            L.append("    %-6s: %s" % (loc, "<MISSING>" if v is None else v.replace("\n", "\\n")))
    L.append("")
if removed:
    L.append("## REMOVED KEYS")
    for k in removed:
        L.append("- %s" % k)
    L.append("")

L.append("## CHANGED (%d)" % len(changed))
L.append("")
for i, k in enumerate(changed, 1):
    L.append("[%02d] %s" % (i, k))
    L.append("  ZH OLD: %s" % old[k].replace("\n", "\\n"))
    L.append("  ZH NEW: %s" % new[k].replace("\n", "\\n"))
    for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
        v = data[loc].get(k)
        L.append("  %-6s: %s" % (loc, "<MISSING>" if v is None else v.replace("\n", "\\n")))
    L.append("")

L.append("## structural sanity of the user's NEW zh values")
for k in changed:
    v = new[k]
    po = sorted(re.findall(r"%[0-9$]*s", old[k]))
    pn = sorted(re.findall(r"%[0-9$]*s", v))
    if po != pn:
        L.append("PLACEHOLDER %s: %s -> %s" % (k, po, pn))
    if v.strip() == "" and old[k].strip() != "":
        L.append("EMPTY       %s" % k)
    if v != v.rstrip():
        L.append("TRAILSPACE  %s" % k)
    if v.startswith("\n"):
        L.append("LEADNEWLINE %s" % k)
    if "  " in v.replace("\n", ""):
        L.append("DBLSPACE    %s" % k)
    if v.count("\n") != old[k].count("\n"):
        L.append("LINECOUNT   %s: %d -> %d" % (k, old[k].count("\n"), v.count("\n")))
L.append("(no line above = clean)")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("changed=%d added=%d removed=%d -> %s" % (len(changed), len(added), len(removed), OUT))
