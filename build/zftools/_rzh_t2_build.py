# -*- coding: utf-8 -*-
r"""_rzh_t2_build.py —— 合成第二份（GUI/工具提示/流体名）文言文译稿并自检。

三编（甲/乙/丙）合起来必须**恰好**等于 _rzh_lzh_in2.json 的键集与键序；
逐键核对 %s / %% 序列、\n 个数、单位记号；两张图纸的 ASCII 网格逐行逐字节比对。
任一条不过 ⇒ 不落盘。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, u"_rzh_lzh_in2.json")
OUT = os.path.join(HERE, u"_rzh_lzh_out2.json")
sys.path.insert(0, HERE)

import _rzh_t2_a
import _rzh_t2_b
import _rzh_t2_c

PH = re.compile(u"%\\d+\\$s|%s|%%")
TOKENS = [u"FE", u"mB", u"tick", u"JEI", u"Shift", u"Y=", u"c:"]
# 图纸键：网格行必须逐字节照抄（数字与格线一个不动）
GRID = re.compile(u"^[0-9 |\uff5c]+$")
BLUEPRINTS = [u"tooltip.potato_s_t.alloy_smelter",
              u"tooltip.potato_s_t.diesel_generator_controller"]


def main():
    with io.open(IN, encoding=u"utf-8") as f:
        src = json.load(f)

    merged = {}
    for name, mod in ((u"甲", _rzh_t2_a), (u"乙", _rzh_t2_b), (u"丙", _rzh_t2_c)):
        dup = set(mod.D) & set(merged)
        if dup:
            raise SystemExit(u"[拒绝] %s编与前者键重叠：%s" % (name, sorted(dup)[:5]))
        merged.update(mod.D)
        print(u"%s编 %4d 键" % (name, len(mod.D)))
    print(u"\n三编合计 %d 键；输入 %d 键" % (len(merged), len(src)))

    missing = [k for k in src if k not in merged]
    extra = [k for k in merged if k not in src]
    if missing or extra:
        print(u"  [缺] %d：%s" % (len(missing), missing[:10]))
        print(u"  [多] %d：%s" % (len(extra), extra[:10]))
        raise SystemExit(u"[拒绝] 键集不符")

    bad_ph, bad_nl, bad_tok, bad_grid, same, empty = [], [], [], [], [], []
    for k, zv in src.items():
        v = merged[k]
        if not isinstance(v, str) or not v.strip():
            empty.append(k)
            continue
        if PH.findall(zv) != PH.findall(v):
            bad_ph.append((k, PH.findall(zv), PH.findall(v)))
        if zv.count(u"\n") != v.count(u"\n"):
            bad_nl.append((k, zv.count(u"\n"), v.count(u"\n")))
        for t in TOKENS:
            if zv.count(t) != v.count(t):
                bad_tok.append((k, t, zv.count(t), v.count(t)))
        if zv == v:
            same.append(k)
        if k in BLUEPRINTS:
            za = [ln for ln in zv.split(u"\n") if GRID.match(ln)]
            zb = [ln for ln in v.split(u"\n") if GRID.match(ln)]
            if za != zb:
                bad_grid.append((k, za, zb))

    def dump(title, items, limit=12):
        if items:
            print(u"\n== %s：%d 条 ==" % (title, len(items)))
            for it in items[:limit]:
                print(u"   %s" % (it,))

    dump(u"占位符序列不一致", bad_ph)
    dump(u"换行个数不一致", bad_nl)
    dump(u"单位/记号数目不一致", bad_tok)
    dump(u"图纸网格行不一致", bad_grid)
    dump(u"空值", empty)
    if bad_ph or bad_nl or bad_tok or bad_grid or empty:
        raise SystemExit(u"[拒绝] 上列问题必须先修掉")

    ordered = dict((k, merged[k]) for k in src)
    text = json.dumps(ordered, ensure_ascii=False, indent=2)
    if u"\r" in text:
        text = text.replace(u"\r\n", u"\n")
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"\nwrote %s（%d 键，%d 字节）" % (OUT, len(ordered), os.path.getsize(OUT)))
    if same:
        print(u"注：%d 条与中文原文逐字相同：%s" % (len(same), same[:10]))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
