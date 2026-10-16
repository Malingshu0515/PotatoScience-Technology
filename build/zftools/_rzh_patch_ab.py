# -*- coding: utf-8 -*-
r"""_rzh_patch_ab.py —— 评那个 subagent 后续覆盖上来的 en/ru 补丁（A/B 对比）。

它的自述不算证据，**同一道门**才算：把它这两份补丁按 `_rzh_guide_merge.py` 的
M1~M6 全跑一遍，并列出**与已提交内容不同**的键，供人工判优劣。

用法：`python build/zftools/_rzh_patch_ab.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_patch_ab.txt")

from _rzh_guide_merge import BANNED, nums, PH               # noqa: E402
import _rzh_guide_zh as GZ                                   # noqa: E402

zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
guide_keys = sorted(GZ.NEW)
config_keys = sorted(k for k in zh if k.startswith(u"potato_s_t.configuration"))
sync_keys = [u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
             u"tooltip.potato_s_t.gravity_device.one_shot.on",
             u"tooltip.potato_s_t.gravity_device.one_shot.off"]
want = guide_keys + config_keys + sync_keys

L = []
for fname, loc in ((u"_rzh_patch_A_en_us.json", u"en_us"), (u"_rzh_patch_A_ru_ru.json", u"ru_ru")):
    p = os.path.join(HERE, fname)
    patch = json.load(io.open(p, encoding=u"utf-8"))
    cur = json.load(io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8"))

    L.append(u"=" * 70)
    L.append(u"## %s（%s）" % (fname, loc))
    L.append(u"=" * 70)
    L.append(u"  键数 %d / 期望 %d" % (len(patch), len(want)))
    L.append(u"  键集合一致: %s" % (set(patch) == set(want)))

    problems = []
    for k in want:
        v = patch.get(k)
        src = zh.get(k, u"")
        if v is None or not isinstance(v, str) or not v.strip():
            problems.append(u"M2 空值/缺键 %s" % k)
            continue
        if v == src and cur.get(k) != src:
            problems.append(u"M2 与中文相同（未翻）%s" % k)
        for rule, needles in BANNED.get(loc, []):
            h = [n for n in needles if n in v]
            if h:
                problems.append(u"M3 %s %s: %s" % (rule, k, u",".join(h)))
        if v.count(u"$(br2)") != src.count(u"$(br2)"):
            problems.append(u"M4 $(br2) %s: %d != %d" % (k, v.count(u"$(br2)"), src.count(u"$(br2)")))
        if sorted(PH.findall(v)) != sorted(PH.findall(src)):
            problems.append(u"M5 占位符 %s" % k)
        ss, vs = nums(src), nums(v)
        miss = [n for n in ss if n not in vs]
        if miss and len(miss) > max(1, len(ss) // 2):
            problems.append(u"M6 缺数字 %s %s" % (k, miss[:6]))

    L.append(u"")
    L.append(u"  == 门的结果：%s ==" % (u"全过" if not problems else u"%d 处问题" % len(problems)))
    for s in problems[:40]:
        L.append(u"     %s" % s)

    diff = [k for k in want if patch.get(k) != cur.get(k)]
    L.append(u"")
    L.append(u"  == 与已提交内容不同的键：%d / %d ==" % (len(diff), len(want)))
    for k in diff[:20]:
        L.append(u"     %s" % k)
        L.append(u"        已提交: %s" % cur.get(k, u"")[:150])
        L.append(u"        它的稿: %s" % patch.get(k, u"")[:150])
    L.append(u"")

io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
print(u"wrote %s" % OUT)
