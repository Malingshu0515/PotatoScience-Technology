# -*- coding: utf-8 -*-
r"""_rzh_guide_bundle.py —— 给四语翻译用的**单一输入文件**。

把三件事合成一份：① 44 段手册正文（已去 AI 味的中文定稿）
② 用户本轮改动的 9 键 ③ 31 条配置说明。
输出 `_rzh_guide_bundle.txt`，供并行翻译使用；并生成每语言的**补丁骨架**，
让翻译只需往 `value` 里填字，避免手抄键名出错。
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")

import _rzh_guide_zh as GZ                                   # noqa: E402

zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
guide_keys = sorted(GZ.NEW)
config_keys = sorted(k for k in zh if k.startswith(u"potato_s_t.configuration"))
sync_keys = [u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
             u"tooltip.potato_s_t.gravity_device.one_shot.on",
             u"tooltip.potato_s_t.gravity_device.one_shot.off",
             u"potato_s_t.configuration.black_hole.one_shot.tooltip",
             u"potato_s_t.configuration.black_hole.pull_entities.tooltip",
             u"potato_s_t.configuration.black_hole.void_damage.tooltip",
             u"potato_s_t.configuration.gravity_device.charge_seconds.tooltip",
             u"potato_s_t.configuration.gravity_device.capacity_fe.tooltip"]

TARGETS = [u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
cur = {l: json.load(io.open(os.path.join(LANGDIR, l + u".json"), encoding=u"utf-8"))
       for l in TARGETS}

L = []
L.append(u"# 待翻译清单（中文为权威源；共 %d 键）" % len(guide_keys + config_keys))
L.append(u"")
L.append(u"## A 帕秋莉手册正文（%d 键）—— 本次重点：去 AI 味" % len(guide_keys))
L.append(u"")
for k in guide_keys:
    L.append(u"### %s" % k)
    L.append(u"ZH: %s" % zh[k])
    for l in TARGETS:
        L.append(u"%-6s: %s" % (l, cur[l].get(k, u"<MISSING>")))
    L.append(u"")
L.append(u"## B 配置说明（%d 键）—— 同样口径：无破折号、无口语备注、无废话词" % len(config_keys))
L.append(u"")
for k in config_keys:
    L.append(u"### %s" % k)
    L.append(u"ZH: %s" % zh[k])
    for l in TARGETS:
        L.append(u"%-6s: %s" % (l, cur[l].get(k, u"<MISSING>")))
    L.append(u"")
L.append(u"## C 用户本轮改动的 9 键" % ())
L.append(u"")
for k in sync_keys:
    L.append(u"### %s" % k)
    L.append(u"ZH: %s" % zh[k])
    for l in TARGETS:
        L.append(u"%-6s: %s" % (l, cur[l].get(k, u"<MISSING>")))
    L.append(u"")

io.open(os.path.join(HERE, u"_rzh_guide_bundle.txt"), u"w",
        encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")

# 补丁骨架：只有 key 与空 value，翻译填 value
allkeys = guide_keys + config_keys + sync_keys
for group, locs in ((u"A", [u"en_us", u"ru_ru"]), (u"B", [u"ja_jp", u"lzh"])):
    for l in locs:
        skel = {}
        for k in allkeys:
            skel[k] = cur[l].get(k, u"")
        p = os.path.join(HERE, u"_rzh_patch_%s_%s.json" % (group, l))
        io.open(p, u"w", encoding=u"utf-8", newline=u"\n").write(
            json.dumps(skel, ensure_ascii=False, indent=2) + u"\n")

print(u"bundle keys=%d -> _rzh_guide_bundle.txt" % len(allkeys))
print(u"patch skeletons: _rzh_patch_A_en_us.json / _rzh_patch_A_ru_ru.json / "
      u"_rzh_patch_B_ja_jp.json / _rzh_patch_B_lzh.json")
