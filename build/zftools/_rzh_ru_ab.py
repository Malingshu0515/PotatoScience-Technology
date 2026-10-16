# -*- coding: utf-8 -*-
"""JUDGE-style side-by-side of the two ru_ru drafts (committed vs the subagent's
later overwrite), so the choice is made on text rather than on either side's claim."""
import io
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", "resources", "assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_ru_ab.txt")

cur = json.load(io.open(os.path.join(LANGDIR, u"ru_ru.json"), encoding=u"utf-8"))
alt = json.load(io.open(os.path.join(HERE, u"_rzh_patch_A_ru_ru.json"), encoding=u"utf-8"))
zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
# 旧译文（用户改写中文之前那版），用于看"事实有没有被新稿丢掉"
git = r"C:\Program Files\Git\cmd\git.exe"
old = json.loads(subprocess.run(
    [git, "show", "HEAD~1:src/main/resources/assets/potato_s_t/lang/ru_ru.json"],
    cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))

SHOW = [
    "potato_s_t.guide.entry.getting_started.rules.p1",
    "potato_s_t.guide.entry.power.generation.p2",
    "potato_s_t.guide.entry.materials.salt.p2",
    "potato_s_t.guide.entry.faq.machine.p1",
    "potato_s_t.guide.entry.oil.distillation.p1",
    "potato_s_t.guide.entry.starfall.sky_and_star.p2",
]

L = [u"# ru_ru 两份稿对照（已提交 vs subagent 后续覆盖稿）", u""]
for k in SHOW:
    L.append(u"=" * 70)
    L.append(u"### %s" % k)
    L.append(u"=" * 70)
    L.append(u"ZH      : %s" % zh[k].replace(u"\n", u" "))
    L.append(u"旧译文  : %s" % old.get(k, u"").replace(u"\n", u" "))
    L.append(u"已提交  : %s" % cur[k].replace(u"\n", u" "))
    L.append(u"它的稿  : %s" % alt[k].replace(u"\n", u" "))
    L.append(u"")

io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
print(u"wrote %s" % OUT)
