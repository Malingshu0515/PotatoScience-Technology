# -*- coding: utf-8 -*-
"""_zf52_verify.py —— 核对"介绍里的摆放图"与**代码里的结构**逐格一致

这是这轮唯一真正重要的断言：工具提示是给人看的，**画错一格就等于骗人**。
做法：把 `AlloySmelterStructure.java` 里的 4 个图层字符串抠出来当**唯一权威**，
再把四语言工具提示里的数字图解析回 4×5×4 网格，逐格比。

数字记法（ZF57 起按**用户自己的编号**）：0 空 / 1 耐热金属块 / 2 一般金属块 / 3 加热装置 /
         4 高炉 / 5 接线块 / 6 散热装置 / 7 合金炉主控
"""
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang")
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod", "AlloySmelterStructure.java")

DIGIT = {"1": "R", "2": "M", "3": "H", "4": "B", "5": "W", "6": "S", "7": "C", "0": "."}

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def java_layers():
    """从 Java 源码里抠出 4 个图层的字符串行（**权威**）。"""
    text = io.open(JAVA, encoding="utf-8").read()
    rows = re.findall(r'"([MHRWBCPK S.]{4})"\s*,', text.replace(" ", " "))
    # 只保留纯图案行（4 个字符、字符都在图例里）
    rows = [r for r in rows if len(r) == 4 and all(c in "MHRWBCPKS." for c in r)]
    if len(rows) != 20:
        raise SystemExit(u"从 Java 里抠出 %d 行，应该是 20 行" % len(rows))
    return [rows[i * 5:(i + 1) * 5] for i in range(4)]


def tooltip_grid(value):
    """把工具提示里的两列数字图解析成 4 层 × 5 行 × 4 列。"""
    left, right = [], []
    for line in value.split("\n"):
        if "|" not in line:
            continue
        a, b = line.split("|", 1)
        if re.fullmatch(r"[0-9]{4}", a.strip()) and re.fullmatch(r"[0-9]{4}", b.strip()):
            left.append(a.strip())
            right.append(b.strip())
    if len(left) != 10 or len(right) != 10:
        raise SystemExit(u"数字行数不对：左 %d 右 %d（各应为 10）" % (len(left), len(right)))
    layers = []
    for k in range(2):
        layers.append(left[k * 5:(k + 1) * 5])
        layers.append(right[k * 5:(k + 1) * 5])
    return layers


def main():
    layers = java_layers()
    print(u"Java 里的图案（权威）：")
    for y, rows in enumerate(layers):
        print(u"   第 %d 层  %s" % (y + 1, " / ".join(rows)))

    langs = {c: json.loads(io.open(os.path.join(LANG, c + ".json"), encoding="utf-8").read())
             for c in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
    base = set(langs["zh_cn"])
    for c, d in langs.items():
        check(set(d) == base, u"%s 键集与 zh_cn 一致" % c)

    for c, d in langs.items():
        tip = d["tooltip.potato_s_t.alloy_smelter"]
        grid = tooltip_grid(tip)
        ok = True
        for y in range(4):
            for j in range(5):
                want = layers[y][j]
                got = "".join(DIGIT[ch] for ch in grid[y][j])
                if want != got:
                    ok = False
                    print(u"         !! %s 第 %d 层 第 %d 行：图里 %s / 代码 %s" % (c, y + 1, j + 1, got, want))
        check(ok, u"%s 的介绍图与 AlloySmelterStructure 逐格一致（4 层 × 5 行）" % c)
        check(u"32768" in tip, u"%s 介绍里仍写着储能 32768 FE" % c)
        check(len(tip.split("\n")) <= 20, u"%s 介绍 %d 行（≤20 行，不至于糊满屏幕）" % (c, len(tip.split("\n"))))

    print(u"\n------------------------------")
    print(u"失败项 = %d" % len(fails))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
