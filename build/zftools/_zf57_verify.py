# -*- coding: utf-8 -*-
"""_zf57_verify.py —— 图纸必须**逐格等于用户原话**

ZF57 用户重画了一版合金炉（并且把主控挪到了最前排的**最右列**）。
这个脚本把用户那条消息**逐字抄成 SPEC**，再和 `AlloySmelterStructure.java` 的 LAYERS 逐格比 ——
期望值来自用户的话，不是从代码里反推的（§4.27）。

用户的图例：耐热金属块=1 一般金属块=2 加热装置=3 高炉=4（接线块/散热装置/合金炉主控 他写的是全名，【】=空）

另外把三件事一起钉住：
  ① 控制器坐标（CTRL_Y/J/I）必须等于"图纸里那个 C 所在的格"（**不写死数字**）；
  ② 介绍图里的编号必须和**方块自己的名字**对得上（四语言各查一遍）；
  ③ 判定要查的 48 格在图纸里必须都有方块（照图纸搭的人才激活得了）。
"""
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod",
                    "AlloySmelterStructure.java")
LANGDIR = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang")
WIDTH, DEPTH, HEIGHT = 4, 5, 4
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")

# ── 用户 ZF57 原话（逐行抄；右边是内部字符）──────────────────────────────
#   第1层：【2】【2】【2】【2】 /【2】【3】【3】【2】×3 /【2】【2】【2】【2】
#   第2层：【接线块】【1】【1】【接线块】 /【4】【】【】【4】×3 /【散热装置】【1】【1】【合金炉主控】
#   第3层：【1】【1】【1】【1】 /【1】【】【】【1】×3 /【1】【1】【1】【1】
#   第4层：【】【1】【1】【】×5 排（ZF58 用户补全：5 排都要，ZF57 时他只写了 4 排）
SPEC = [
    ["MMMM", "MHHM", "MHHM", "MHHM", "MMMM"],
    ["WRRW", "B..B", "B..B", "B..B", "SRRC"],
    ["RRRR", "R..R", "R..R", "R..R", "RRRR"],
    [".RR.", ".RR.", ".RR.", ".RR.", ".RR."],
]

# 介绍图里的编号 → 方块（要和 lang 里那个方块自己的名字对得上）
LEGEND = [
    ("1", "block.potato_s_t.heat_resistant_metal_block"),
    ("2", "block.potato_s_t.common_metal_block"),
    ("3", "block.potato_s_t.heater"),
    ("5", "block.potato_s_t.wiring_block"),
    ("6", "block.potato_s_t.heat_sink"),
    ("7", "block.potato_s_t.alloy_smelter"),
]

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def read(path):
    return io.open(path, encoding="utf-8").read()


def java_layers():
    text = read(JAVA)
    rows = re.findall(r'"([MHRWBCPK S.]{4})"\s*,', text)
    rows = [r for r in rows if len(r) == 4 and all(c in "MHRWBCPKS." for c in r)]
    if len(rows) != 20:
        raise SystemExit(u"从 Java 里抠出 %d 行图案，应该是 20 行" % len(rows))
    return [rows[i * 5:(i + 1) * 5] for i in range(4)]


def main():
    # ---------- ① 图纸逐格 ----------
    print(u"① 图纸 vs 用户原话（逐格）")
    layers = java_layers()
    for y in range(4):
        for j in range(5):
            want = SPEC[y][j]
            got = layers[y][j]
            if want != got:
                check(False, u"第 %d 层 第 %d 排：用户 %s / 代码 %s" % (y + 1, j + 1, want, got))
    check(all(SPEC[y][j] == layers[y][j] for y in range(4) for j in range(5)),
          u"4 层 × 5 排 = 20 行全部一致")
    check(SPEC[3] == [".RR."] * 5, u"第 4 层是 5 排【空·耐热·耐热·空】（ZF58 用户补全的第 5 排）")

    # ---------- ② 控制器坐标 = 图纸里 C 的格 ----------
    print(u"\n② 控制器在图纸里的格")
    ctrl = [(y, j, i) for y in range(4) for j in range(5) for i in range(4)
            if SPEC[y][j][i] == "C"]
    check(len(ctrl) == 1, u"图纸里正好一个主控（%s）" % (ctrl or u"没有"))
    if len(ctrl) == 1:
        y, j, i = ctrl[0]
        my = re.search(r"CTRL_Y\s*=\s*(\d+)", read(JAVA)).group(1)
        mj = re.search(r"CTRL_J\s*=\s*(\d+)", read(JAVA)).group(1)
        mi = re.search(r"CTRL_I\s*=\s*(\d+)", read(JAVA)).group(1)
        check((int(my), int(mj), int(mi)) == (y, j, i),
              u"CTRL_Y/J/I = (%s, %s, %s)，图纸里 C 在 (%d, %d, %d)" % (my, mj, mi, y, j, i))
        check(i == WIDTH - 1, u"主控在最右列（i=%d）而不是最左列" % i)

    # ---------- ③ 判定要查的格在图纸里都有方块 ----------
    print(u"\n③ 判定要查的 58 格")
    missing = []
    for y in range(HEIGHT):
        for j in range(DEPTH):
            for i in range(WIDTH):
                required = (y == 0
                            or (y <= HEIGHT - 2 and (j in (0, DEPTH - 1) or i in (0, WIDTH - 1)))
                            or (y == HEIGHT - 1 and layers[y][j][i] != "."))
                if required and layers[y][j][i] == ".":
                    missing.append((y, j, i))
    check(not missing, u"要查的格里没有空格（空的：%s）" % (missing or u"无"))

    # ---------- ④ 介绍图的编号 vs 方块名字 ----------
    print(u"\n④ 介绍图的图例（四语言）")
    for code in LANGS:
        data = json.loads(read(os.path.join(LANGDIR, code + ".json")))
        tip = data["tooltip.potato_s_t.alloy_smelter"]
        legend = u"\n".join(tip.split("\n")[:3])
        bad = []
        for digit, key in LEGEND:
            name = data.get(key)
            if name is None:
                bad.append(u"%s(缺键 %s)" % (digit, key))
            elif (digit + u" " + name) not in legend:
                bad.append(u"%s->%s" % (digit, name))
        check(not bad, u"%s 图例里 1/2/3/5/6/7 都对着方块自己的名字（不对的：%s）"
                       % (code, bad or u"无"))
    data = json.loads(read(os.path.join(LANGDIR, "zh_cn.json")))
    tip = data["tooltip.potato_s_t.alloy_smelter"]
    check(u"4 高炉" in tip, u"中文图例里 4 = 高炉")
    check(u"0 空" in tip, u"中文图例里 0 = 空")
    rows = [l for l in tip.split("\n") if re.fullmatch(r"[0-9]{4}\|[0-9]{4}", l)]
    check(len(rows) == 10, u"介绍里 10 行数字图（数到 %d）" % len(rows))

    print(u"\n------------------------------")
    print(u"失败项 = %d" % len(fails))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
