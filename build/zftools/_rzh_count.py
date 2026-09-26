# -*- coding: utf-8 -*-
r"""_rzh_count.py —— 在动手前数一数：某个词在四份语言文件的值里各出现几次。

用途：`_rzh_fix_batch.py` 的替换段要求"命中次数至少 N 次"，N 必须来自实测。
⚠ 只读。结论自己写 UTF-8 文件 —— **不要用 shell 重定向**（PowerShell `>` 落盘
   是 UTF-16，read 工具会当二进制拒读；本会话已经栽过一次）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_count.txt")

NEEDLES = [
    (u"zh_cn", u"钛矿"), (u"zh_cn", u"深层钛矿"),
    (u"zh_cn", u"黑钨矿"), (u"zh_cn", u"深层黑钨矿"),
    (u"zh_cn", u"光伏原件"), (u"zh_cn", u"锂电池原件"),
    (u"zh_cn", u"盐分解构器"), (u"zh_cn", u"氨气组成室"),
    (u"zh_cn", u"加氢脱硫反应仓"), (u"zh_cn", u"一般金属块"),
    (u"en_us", u"Oil Extractor"), (u"en_us", u"Container Fluid Exchanger"),
    (u"en_us", u"aluminium"), (u"en_us", u"aluminum"),
]


def main():
    lines = []
    cache = {}
    for loc, needle in NEEDLES:
        if loc not in cache:
            with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
                cache[loc] = json.load(f)
        d = cache[loc]
        total = sum(v.count(needle) for v in d.values())
        keys = [k for k, v in d.items() if needle in v]
        lines.append(u"%-6s %-24s 命中 %2d 次 / %d 个键" % (loc, needle, total, len(keys)))
        for k in keys:
            lines.append(u"          %s" % k)
    text = u"\n".join(lines)
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
