# -*- coding: utf-8 -*-
r"""_rzh_adv_survey.py —— 盘清全部成就的标题与说明（四语），并给出"长度体检"。

用途：成就润色/精简之前，先有一份**全量现状**，而不是凭印象挑几条改。
输出 `_rzh_adv_survey.txt`（UTF-8，脚本自己写 —— PowerShell 的 `>` 是 UTF-16）。

用法：`python build/zftools/_rzh_adv_survey.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_adv_survey.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]


def main():
    data = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            data[loc] = json.load(f)
    zh = data[u"zh_cn"]
    ids = sorted(set(re.match(u"advancements\\.potato_s_t\\.([a-z0-9_]+)\\.",
                              k).group(1)
                     for k in zh if k.startswith(u"advancements.")))

    L = [u"成就节点 %d 个；四语键集一致 = %s"
         % (len(ids), all(set(data[l]) == set(zh) for l in LOCALES[:4])), u""]

    L.append(u"%-28s %-16s %5s  %s" % (u"节点", u"中文标题", u"说明字数", u"说明首行"))
    L.append(u"-" * 110)
    total = 0
    for i in ids:
        k = u"advancements.potato_s_t.%s" % i
        t = zh.get(k + u".title", u"<缺>")
        de = zh.get(k + u".description", u"<缺>")
        total += len(de)
        first = de.split(u"\n")[0]
        L.append(u"%-28s %-16s %5d  %s" % (i, t, len(de), first[:64]))
    L.append(u"")
    L.append(u"说明总字数 %d，平均 %.1f 字/条" % (total, float(total) / max(1, len(ids))))

    # 四语长度对照（看哪条明显比中文长很多 —— 精简时优先看这些）
    L.append(u"")
    L.append(u"== 各语最长说明 TOP 12（按 en 字数）==")
    en = data[u"en_us"]
    rows = sorted(ids, key=lambda i: -len(en.get(u"advancements.potato_s_t.%s.description" % i, u"")))
    L.append(u"%-28s %5s %5s %5s %5s" % (u"节点", u"zh", u"en", u"ja", u"ru"))
    for i in rows[:12]:
        k = u"advancements.potato_s_t.%s.description" % i
        L.append(u"%-28s %5d %5d %5d %5d" % (i, len(zh.get(k, u"")), len(en.get(k, u"")),
                                             len(data[u"ja_jp"] .get(k, u"")),
                                             len(data[u"ru_ru"].get(k, u""))))

    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(L) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
