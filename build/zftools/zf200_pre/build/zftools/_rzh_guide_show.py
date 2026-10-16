# -*- coding: utf-8 -*-
"""Before/after samples of the guide rewrite, plus the final gate summary.
Reads the pre-change text from git HEAD so nothing is hand-copied."""
import io
import json
import os
import subprocess
import sys

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
OUT = os.path.join(ROOT, build := "build", "zftools", "_rzh_guide_show.txt")

SAMPLE = [
    "potato_s_t.guide.entry.materials.salt.p1",
    "potato_s_t.guide.entry.getting_started.start.p1",
    "potato_s_t.guide.entry.power.generation.p3",
    "potato_s_t.guide.entry.starfall.star_steel.p1",
    "potato_s_t.guide.entry.faq.fluid.p1",
    "potato_s_t.guide.landing",
]

L = []
L.append("# 手册去 AI 味：改动前后对照（中文为权威源，四语同步）")
L.append("")
for loc in ("zh_cn", "en_us", "ru_ru"):
    # ⚠ 必须跟 HEAD~1 比：本轮改动已经提交成 HEAD，跟 HEAD 比会得到"前后一样"。
    old = json.loads(subprocess.run(
        [GIT, "show", "HEAD~1:src/main/resources/assets/potato_s_t/lang/%s.json" % loc],
        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
    new = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    L.append("=" * 72)
    L.append("## %s" % loc)
    L.append("=" * 72)
    for k in SAMPLE:
        L.append("")
        L.append("### %s" % k.split(".")[-2] + "." + k.split(".")[-1])
        L.append("  改前: %s" % old[k].replace("\n", " "))
        L.append("  改后: %s" % new[k].replace("\n", " "))
    L.append("")

L.append("=" * 72)
L.append("## 门的结果")
L.append("=" * 72)
for f, label in (("_rzh_guide_verify.txt", "验证（禁词 / 结构 / 机制事实 / 数字）"),
                 ("_rzh_guide_lint.txt", "风格体检（感叹号・破折号・废话词…）")):
    p = os.path.join(ROOT, "build", "zftools", f)
    if not os.path.exists(p):
        continue
    L.append("")
    L.append("### %s  (%s)" % (label, f))
    txt = io.open(p, encoding="utf-8").read().split("\n")
    for line in txt[-14:]:
        L.append("  " + line)

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("wrote %s" % OUT)
