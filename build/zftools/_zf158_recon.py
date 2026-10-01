# -*- coding: utf-8 -*-
u"""_zf158_recon.py —— ZF158 侦察（只读）：热力金属那张图纸的现状 + 生成器表覆盖了哪些。

① 现在 `thermal_metal.json` 的形状（银在外、铜在中，用户要反过来）；
② 生成器表 `_zf45_recipes.py` 里 thermal_metal 那条（**表是那 35 份 JSON 的唯一来源**）；
③ 表里还写死"自家板当物品"的条目 —— ZF156 把配方改成 `#c:plates/*` 之后，表和盘**已经不一致**，
   这一轮必须一起跟平（不然谁跑一次 `--write` 就把上一轮的改动revert 了）。

跑法：python build\\zftools\\_zf158_recon.py [--write]
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
GEN = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")
OUT = os.path.join(ROOT, r"build\zftools\_zf158_recon.txt")
METALS = ["aluminum", "cobalt", "copper", "iron", "nickel", "silver", "steel"]
LINES = []


def say(s):
    LINES.append(s)
    print(s)


def main(argv):
    say(u"=========== ZF158 侦察 ===========")
    say(u"\n① 现在这张图纸：")
    d = json.loads(io.open(os.path.join(RECIPE, u"thermal_metal.json"), encoding="utf-8").read())
    for row in d[u"pattern"]:
        say(u"     " + row)
    say(u"   key = " + json.dumps(d[u"key"], ensure_ascii=False))
    say(u"   ⇒ 外圈（第 1、3 行）是 %s，中行是 %s"
        % (list(d[u"key"][d[u"pattern"][0][0]].values())[0], list(d[u"key"][d[u"pattern"][1][0]].values())[0]))

    say(u"\n② 生成器表里的 thermal_metal：")
    gen = io.open(GEN, encoding="utf-8").read()
    i = gen.find(u'name="thermal_metal"')
    say(u"   " + gen[max(0, i - 90):i + 200].replace(u"\n", u"\n   "))

    say(u"\n③ 表里还写死「自家板当物品」的条目（ZF156 之后应与盘上的 #c:plates/* 对齐）：")
    hits = [(m.start(), m.group(0)) for m in re.finditer(
        u'"[A-Z]": \\("item", "potato_s_t:(?:' + u"|".join(METALS) + u')_plate"\\)', gen)]
    for pos, text in hits:
        line = gen[:pos].count(u"\n") + 1
        say(u"     行 %d：%s" % (line, text))

    say(u"\n   对照：盘上现在用 #c:plates/* 的配方有几处、都是哪些：")
    tag_files = {}
    for dirpath, _d, filenames in os.walk(RECIPE):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            t = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            tags = re.findall(u'"tag": "c:plates/([a-z]+)"', t)
            if tags:
                tag_files[os.path.relpath(os.path.join(dirpath, fn), RECIPE)] = tags
    say(u"     %d 份 / %d 处：%s" % (len(tag_files), sum(len(v) for v in tag_files.values()),
                                     u", ".join(u"%s(%s)" % (k, u"+".join(v)) for k, v in sorted(tag_files.items()))))
    say(u"\n   这 %d 份里有几份在生成器表里（按 name= 找）：" % len(tag_files))
    for rel in sorted(tag_files):
        name = os.path.basename(rel)[:-5]
        in_gen = (u'name="%s"' % name) in gen
        say(u"     %-38s 表里%s" % (rel, u"有" if in_gen else u"**没有**"))

    say(u"\n=========== 侦察完 ===========")
    if u"--write" in argv:
        io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(LINES) + u"\n")
        print(u"（已写 %s）" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
