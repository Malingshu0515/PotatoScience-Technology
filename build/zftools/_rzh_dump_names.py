# -*- coding: utf-8 -*-
r"""_rzh_dump_names.py —— 把四语的**物品/方块显示名**并排导出来，供人工过目。

为什么单独写：翻译线改「物品翻译」时，真正的判断材料是
    zh 原名 / en / ja / ru 四列并排
而不是逐份语言文件去翻。这个脚本只读，不改任何东西。

用法：
    python build/zftools/_rzh_dump_names.py            # 打印到屏幕
    python build/zftools/_rzh_dump_names.py --md       # 写成 markdown 表
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def load(loc):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)


def main():
    data = dict((loc, load(loc)) for loc in LOCALES)
    keys = [k for k in data[u"zh_cn"]
            if k.startswith(u"item.potato_s_t.") or k.startswith(u"block.potato_s_t.")]
    keys.sort()

    as_md = u"--md" in sys.argv
    out = []
    if as_md:
        out.append(u"| 键 | zh_cn | en_us | ja_jp | ru_ru |")
        out.append(u"|---|---|---|---|---|")
    for k in keys:
        short = k.split(u".", 2)[2]
        row = [data[loc].get(k, u"<缺>") for loc in LOCALES]
        if as_md:
            out.append(u"| `%s` | %s |" % (short, u" | ".join(row)))
        else:
            out.append(u"%-34s | %-14s | %-30s | %-22s | %s"
                       % (short, row[0], row[1], row[2], row[3]))
    text = u"\n".join(out)

    if as_md:
        p = os.path.join(ROOT, u"build", u"zftools", u"_rzh_names_table.md")
        with io.open(p, u"w", encoding=u"utf-8", newline=u"\n") as f:
            f.write(text + u"\n")
        print(u"wrote %s  (%d keys)" % (p, len(keys)))
    else:
        print(u"物品/方块显示名 %d 条：\n" % len(keys))
        print(text)


if __name__ == u"__main__":
    main()
