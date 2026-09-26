# -*- coding: utf-8 -*-
r"""_rzh_snapdelta.py —— 把"某个快照 vs 现在"被改过值的键**机械算出来**，按语言分组。

为什么必须机械算：`_zf117_verify.py` 的 D7 判据是"被改动的键**正好等于**一张
名单"。那张名单一旦凭记忆补，就会犯两类错 —— 漏（门红）或猜（门假绿）。
§4.36 的口径是**改锚点、不放宽断言**，前提就是锚点得是算出来的。

用法：
    python build/zftools/_rzh_snapdelta.py <快照目录> [语言...]
默认跑 `zh_cn en_us ja_jp ru_ru`，结论写 `_rzh_snapdelta.txt`（UTF-8）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REL = u"src/main/resources/assets/potato_s_t/lang/%s.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_snapdelta.txt")


def main():
    if len(sys.argv) < 2:
        print(u"用法: python _rzh_snapdelta.py <快照目录> [语言...]")
        return 1
    snap = sys.argv[1]
    langs = sys.argv[2:] or [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

    lines = [u"快照目录: %s" % snap, u""]
    for loc in langs:
        sp = os.path.join(snap, REL.replace(u"/", os.sep) % loc)
        # 快照的目录层级可能少一层，兜一下
        if not os.path.exists(sp):
            alt = os.path.join(snap, u"lang", loc + u".json")
            sp = alt if os.path.exists(alt) else sp
        if not os.path.exists(sp):
            lines.append(u"%s: 快照里没有（跳过）—— %s" % (loc, sp))
            continue
        old = json.load(io.open(sp, encoding=u"utf-8"))
        cur = json.load(io.open(os.path.join(ROOT, REL % loc), encoding=u"utf-8"))
        changed = sorted(k for k in old if k in cur and old[k] != cur[k])
        added = sorted(k for k in cur if k not in old)
        lines.append(u"########## %s" % loc)
        lines.append(u"   被改值 %d 个：" % len(changed))
        for k in changed:
            lines.append(u"       u\"%s\"," % k)
        lines.append(u"   新增 %d 个（前 40）：" % len(added))
        for k in added[:40]:
            lines.append(u"       %s" % k)
        lines.append(u"")

    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
