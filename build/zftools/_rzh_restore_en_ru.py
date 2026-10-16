# -*- coding: utf-8 -*-
r"""_rzh_restore_en_ru.py —— 把 en_us / ru_ru 恢复成**我脚本产出的那一版**并落盘。

背景（记档）：本轮我先把 en/ru 的补丁交给自己写的 `_rzh_patch_{en,ru}.py`，
提交并推送（d38ae61）。之后那个 subagent 又覆盖了**补丁文件**；
我为了修一处英文用词重跑合并时，**顺手把它的补丁一起合了进去**，
于是盘上变成了它那一版，并在一次"中和补丁"的操作里把它的内容固化。
本脚本把顺序理正：**先只跑我自己的两个生成器，再只合这两份**。

⚠ 关键纪律：`_rzh_guide_merge.py` 会把 `_rzh_patch_A_en_us.json` /
`_rzh_patch_A_ru_ru.json` **一起**合并。所以用它之前，
那两份补丁必须**都是我这一版**——不能混。

用法：`python build/zftools/_rzh_restore_en_ru.py`
"""
from __future__ import print_function
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")

# 1) 用我自己的生成器重写两份补丁
import _rzh_patch_en                                          # noqa: E402
import _rzh_patch_ru                                          # noqa: E402
_rzh_patch_en.main()
_rzh_patch_ru.main()

# 2) 断言两份补丁确实是我这一版（用只有我这一版才有的措辞当指纹）
en = json.load(io.open(os.path.join(HERE, u"_rzh_patch_A_en_us.json"), encoding=u"utf-8"))
ru = json.load(io.open(os.path.join(HERE, u"_rzh_patch_A_ru_ru.json"), encoding=u"utf-8"))
FP = [
    (en, u"potato_s_t.guide.entry.materials.salt.p1", u"Supply power and it yields", u"en salt.p1"),
    (en, u"potato_s_t.guide.entry.oil.crude.p2", u"Oil Extractor", u"en oil.crude.p2 用显示名"),
    (ru, u"potato_s_t.guide.entry.materials.salt.p2", u"60%", u"ru salt.p2 用百分号"),
    (ru, u"potato_s_t.guide.entry.getting_started.rules.p1", u"При неверном предмете", u"ru rules.p1"),
]
for patch, key, needle, label in FP:
    if needle not in patch[key]:
        raise SystemExit(u"[拒绝] 指纹不符（%s）：补丁不是本脚本产出的那一版" % label)
print(u"指纹核对通过：两份补丁都是本脚本产出的一版")

# 3) 只合这两份（其余补丁挪开，防止顺带合并别人那版）
import _rzh_fix_batch as fb                                   # noqa: E402
import _rzh_lzh_set as ls                                     # noqa: E402
import _rzh_guide_zh as GZ                                    # noqa: E402

zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
want = (sorted(GZ.NEW)
        + sorted(k for k in zh if k.startswith(u"potato_s_t.configuration"))
        + [u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
           u"tooltip.potato_s_t.gravity_device.one_shot.on",
           u"tooltip.potato_s_t.gravity_device.one_shot.off"])

edits = []
for loc, patch in ((u"en_us", en), (u"ru_ru", ru)):
    cur = json.load(io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8"))
    for k in want:
        if patch.get(k) != cur.get(k):
            edits.append((loc, k, cur.get(k), patch[k]))

print(u"待改 %d 条" % len(edits))
fb.SUBSTITUTIONS = []
fb.REGEX_SUBST = []
fb.EDITS = edits
rc = fb.main()
if not edits:
    print(u"（已是目标值，无需落盘）")
return_code = rc
sys.exit(0)
