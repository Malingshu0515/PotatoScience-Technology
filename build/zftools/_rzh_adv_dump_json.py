# -*- coding: utf-8 -*-
r"""_rzh_adv_dump_json.py —— 把 43 条成就说明的**盘上现况**导成一份 JSON，供 `_rzh_adv_trim` 校对。

为什么要这一步：`_rzh_adv_trim.TRIM` 里的"旧值"是我照着一次 dump 写的，
而**平行线随时会动这些键**。手抄旧值 = 抄一次就有一次抄错的机会。
这里把现况机械导出来，写成 Python 字面量，直接替换进去。

⚠ 输出用 `ensure_ascii=True`，全转义成 \uXXXX —— 这样复制粘贴**不会因为
   PowerShell 控制台的 GBK 编码而变成乱码**（本会话栽过不止一次）。

用法：`python build/zftools/_rzh_adv_dump_json.py [节点...]`
输出 `_rzh_adv_now.txt`（Python 字面量）与 `_rzh_adv_now.json`（原始 JSON）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
HERE = os.path.dirname(os.path.abspath(__file__))
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def main():
    want = sys.argv[1:]
    data = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            data[loc] = json.load(f)

    keys = sorted(k for k in data[u"zh_cn"]
                  if k.startswith(u"advancements.potato_s_t.")
                  and k.endswith(u".description"))
    if want:
        keys = [k for k in keys
                if k[len(u"advancements.potato_s_t."):-len(u".description")] in want]

    plain = {}
    lines = []
    for k in keys:
        node = k[len(u"advancements.potato_s_t."):-len(u".description")]
        plain[node] = dict((loc, data[loc][k]) for loc in LOCALES)
        lines.append(u'    u"%s": {' % node)
        for loc in LOCALES:
            lines.append(u'        u"%s": %s,'
                         % (loc, json.dumps(data[loc][k], ensure_ascii=True)))
        lines.append(u'    },')

    io.open(os.path.join(HERE, u"_rzh_adv_now.txt"), u"w", encoding=u"ascii",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    with io.open(os.path.join(HERE, u"_rzh_adv_now.json"), u"w", encoding=u"utf-8",
                 newline=u"\n") as f:
        f.write(json.dumps(plain, ensure_ascii=False, indent=2) + u"\n")
    print(u"wrote _rzh_adv_now.txt / _rzh_adv_now.json  (%d 条)" % len(keys))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
