# -*- coding: utf-8 -*-
"""Which keys does zh_cn have that the four targets are missing or stale on?
Focus: my 9 changed keys + every config key + every guide key."""
import io
import json
import os
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_user3_state.txt")
LOCS = ["en_us", "ja_jp", "ru_ru", "lzh"]

old = json.loads(subprocess.run(
    [GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
    cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
d = {l: json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8")) for l in LOCS}

changed = [k for k in zh if k in old and old[k] != zh[k]]

L = []
L.append("## 用户这轮改的 9 键：四语现状")
for k in changed:
    L.append("%s" % k)
    L.append("   zh : %s" % zh[k].replace("\n", "\\n"))
    for l in LOCS:
        v = d[l].get(k)
        L.append("   %-6s: %s" % (l, "<MISSING>" if v is None else v.replace("\n", "\\n")))
    L.append("")

L.append("## 配置键（potato_s_t.configuration.*）：四语缺失情况")
cfg = sorted(k for k in zh if k.startswith("potato_s_t.configuration"))
L.append("zh 里共 %d 条" % len(cfg))
for k in cfg:
    miss = [l for l in LOCS if k not in d[l]]
    if miss:
        L.append("  [缺] %-64s 缺: %s" % (k, ", ".join(miss)))
L.append("（没列出的 = 四语都在）")

L.append("")
L.append("## guide 键：四语缺失情况")
gd = sorted(k for k in zh if k.startswith("potato_s_t.guide"))
L.append("zh 里共 %d 条" % len(gd))
for k in gd:
    miss = [l for l in LOCS if k not in d[l]]
    if miss:
        L.append("  [缺] %-64s 缺: %s" % (k, ", ".join(miss)))
L.append("（没列出的 = 四语都在）")

L.append("")
L.append("## 其它 zh 有而四语缺的键（全局）")
for l in LOCS:
    miss = sorted(set(zh) - set(d[l]))
    L.append("  %-6s 缺 %d 条" % (l, len(miss)))
    for k in miss[:25]:
        L.append("        %s" % k)

L.append("")
L.append("## guide 正文的规模（zh）")
tot = 0
for k in gd:
    if ".p" in k or k.endswith(".landing"):
        tot += len(zh[k])
L.append("  guide 正文合计 %d 字符（含 $(br2)）" % tot)
L.append("  最长几条：")
for k in sorted(gd, key=lambda x: -len(zh[x]))[:6]:
    L.append("    %-58s %d 字符" % (k, len(zh[k])))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("changed=%d cfg=%d guide=%d -> %s" % (len(changed), len(cfg), len(gd), OUT))
