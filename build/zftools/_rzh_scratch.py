# -*- coding: utf-8 -*-
r"""_rzh_scratch.py —— 小工具集合：数命中、列键、比原版。只读，不写语言文件。

存在的理由：改语言前要先用**实测数字**确认"盘上现在是什么样"，而不是凭印象。
结论写 `_rzh_scratch.txt`（UTF-8，**不用 shell 重定向** —— PowerShell 的 `>`
会落成 UTF-16，read 工具直接拒读）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_scratch.txt")


def load(loc):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)


def main():
    lines = []
    ja = load(u"ja_jp")
    ru = load(u"ru_ru")

    lines.append(u"===== ja_jp：深层矿 / 原石 / 机器名现状 =====")
    for k in sorted(ja):
        v = ja[k]
        if (u"深層" in v) or (u"原石" in v) or (u"粗" in v and k.startswith((u"item.", u"block."))):
            lines.append(u"   %-46s %s" % (k.split(u".", 2)[-1] if k.count(u".") > 1 else k, v))

    lines.append(u"")
    lines.append(u"===== ru_ru：深层矿 / 原石 / 机器名现状 =====")
    for k in sorted(ru):
        v = ru[k]
        if (u"глубинн" in v.lower()) or (u"удн" in v) or (u"Необработанн" in v):
            lines.append(u"   %-46s %s" % (k.split(u".", 2)[-1] if k.count(u".") > 1 else k, v))

    lines.append(u"")
    lines.append(u"===== 其余 ru 候选 =====")
    for needle in (u"Нефтяное ведро", u"Разлагатель", u"Солесушилка", u"Микро-дробилка",
                   u"Тройная", u"Порт питания", u"подвесок"):
        hits = [(k, v) for k, v in ru.items() if needle in v]
        lines.append(u"   %-20s 命中 %d" % (needle, len(hits)))
        for k, v in hits[:6]:
            lines.append(u"        %s" % k)
            lines.append(u"        %s" % v.replace(u"\n", u"\\n")[:150])

    lines.append(u"")
    lines.append(u"===== ja 机器名候选 =====")
    for needle in (u"塩分解", u"容器換装", u"星儀図", u"オイルバケツ", u"制御器", u"チャンバー"):
        hits = [(k, v) for k, v in ja.items() if needle in v]
        lines.append(u"   %-16s 命中 %d" % (needle, len(hits)))
        for k, v in hits[:6]:
            lines.append(u"        %s = %s" % (k, v.replace(u"\n", u"\\n")[:120]))

    lines.append(u"")
    lines.append(u"===== 精确命中数（供 _rzh_fix_batch 的替换段用）=====")
    CASES = [
        (u"ja_jp", u"深層岩のコバルト鉱石"), (u"ja_jp", u"深層岩のマンガン鉱石"),
        (u"ja_jp", u"深層岩のニッケル鉱石"), (u"ja_jp", u"深層岩の銀鉱石"),
        (u"ja_jp", u"深層岩のチタン鉱石"), (u"ja_jp", u"深層岩のウラン鉱石"),
        (u"ja_jp", u"深層岩の鉄マンガン重石鉱石"),
        (u"ja_jp", u"深層コバルト鉱石"), (u"ja_jp", u"深層チタン鉱石"),
        (u"ja_jp", u"粗アルミニウム"), (u"ja_jp", u"粗コバルト"), (u"ja_jp", u"粗リチウム"),
        (u"ja_jp", u"粗マンガン"), (u"ja_jp", u"粗ニッケル"), (u"ja_jp", u"粗銀"),
        (u"ja_jp", u"粗チタン"), (u"ja_jp", u"粗タングステン"), (u"ja_jp", u"粗ウラン"),
        (u"ja_jp", u"粗ヴィブラニウム"), (u"ja_jp", u"粗鉄"), (u"ja_jp", u"粗銅"),
        (u"ja_jp", u"粗鉱"), (u"ja_jp", u"塩分解構築器"), (u"ja_jp", u"容器換装器"),
        (u"ja_jp", u"オイルバケツ"),
        (u"ru_ru", u"Кобальтовая руда в глубинном сланце"),
        (u"ru_ru", u"Марганцевая руда в глубинном сланце"),
        (u"ru_ru", u"Никелевая руда в глубинном сланце"),
        (u"ru_ru", u"Серебряная руда в глубинном сланце"),
        (u"ru_ru", u"Титановая руда в глубинном сланце"),
        (u"ru_ru", u"Урановая руда в глубинном сланце"),
        (u"ru_ru", u"Вольфрамитовая руда в глубинном сланце"),
        (u"ru_ru", u"глубинная кобальтовая руда"),
        (u"ru_ru", u"Необработанный алюминий"), (u"ru_ru", u"Необработанный кобальт"),
        (u"ru_ru", u"Необработанный литий"), (u"ru_ru", u"Необработанный марганец"),
        (u"ru_ru", u"Необработанный никель"), (u"ru_ru", u"Необработанное серебро"),
        (u"ru_ru", u"Необработанный титан"), (u"ru_ru", u"Необработанный вольфрам"),
        (u"ru_ru", u"Необработанный уран"), (u"ru_ru", u"Необработанный вибраниум"),
        (u"ru_ru", u"Нефтяное ведро"), (u"ru_ru", u"Разлагатель соли"),
        (u"ru_ru", u"Солесушилка"), (u"ru_ru", u"Микро-дробилка"),
        (u"ru_ru", u"Тройная полимерная литиевая батарея"),
        (u"ru_ru", u"Порт питания плавильни сплавов"),
        (u"ru_ru", u"Звёздный подвесок"),
    ]
    cache = {}
    for loc, needle in CASES:
        if loc not in cache:
            cache[loc] = load(loc)
        d = cache[loc]
        n = sum(v.count(needle) for v in d.values())
        ks = [k for k, v in d.items() if needle in v]
        lines.append(u"   %-6s %-40s %2d 次 / %d 键  %s"
                     % (loc, needle, n, len(ks), u", ".join(ks[:3])))

    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
