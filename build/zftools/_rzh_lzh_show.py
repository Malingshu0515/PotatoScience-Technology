# -*- coding: utf-8 -*-
r"""_rzh_lzh_show.py —— 把合并后的 lzh.json 按类别抽样打印，供人工过目。

用法：`python build/zftools/_rzh_lzh_show.py [类别前缀，默认 item.,block.]`
结论写 `_rzh_lzh_show.txt`（UTF-8；不用 shell 重定向 —— 那是 UTF-16）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_lzh_show.txt")


def main():
    prefixes = tuple((sys.argv[1] if len(sys.argv) > 1 else u"item.,block.").split(u","))
    zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
    lz = json.load(io.open(os.path.join(LANGDIR, u"lzh.json"), encoding=u"utf-8"))
    L = [u"== 文言文成品抽样：%s ==" % u", ".join(prefixes), u""]
    for k in zh:
        if not k.startswith(prefixes):
            continue
        short = k.split(u".", 2)[-1] if k.count(u".") > 1 else k
        L.append(u"%-34s %-16s %s" % (short, zh[k].replace(u"\n", u"\\n")[:16],
                                      lz[k].replace(u"\n", u"\\n")))
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
