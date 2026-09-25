# -*- coding: utf-8 -*-
u"""_zf108_textures.py —— ZF108：合金冶炼炉的两张贴图（16×16，程序生成）

用户原话：「你看看您不能发挥一下 简单画一下合金冶炼炉的材质（不用太好 凑活都可以）现在的太丑了谢谢啦」

**画的是什么**
  · `alloy_smelter.png`        —— 主控（未成型时的方块）+ **12 块外壳** + 物品图标都用它（`cube_all`）
  · `alloy_smelter_formed.png` —— 成型后的多方块机体（4 个 OBJ 用，见 `_zf108_reuv.py`）

**为什么以前丑**（量过，不是感觉）：
  · 旧 `alloy_smelter.png` 有 **228 种颜色**，而本工程好看的机器贴图都是 **5~19 色**的平涂像素画
    （微型粉碎机侧面 8 色、燃烧反应室 6 色）—— 旧图是糊的（放大后像噪声）；
  · 成型后的机体**根本没有自己的贴图**：`alloy_smelter.mtl` 借的是 `heat_resistant_metal_block`；
  · 更糟的是那 4 个 OBJ 只有 **4 个唯一 `vt`** ⇒ 贴图上 4×4 像素的一小块被**放大铺满每一个面**
    （所以借谁都看不出来）—— 这两件事 `_zf108_reuv.py` 一起修。

**配色**（照本工程机器家族的实测色值，不自己发明）：
  微型粉碎机侧面 `#4a4a52` / 深 `#34363b` / 亮 `#6e6e78` / 高光 `#9aa2ac`；
  热色沿用燃烧反应室那支 `#c46022`（熔融金属），亮一档 `#e8912f`。

用法：
    python build/zftools/_zf108_textures.py            # 只打印 + 生成预览图，不写正式贴图
    python build/zftools/_zf108_textures.py --write    # 真写
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
PREVIEW = r"E:\PotatoST\build\zftools\_zf108_preview.png"

# 图例：. 基色  # 深框  @ 最暗（凹槽内）  + 亮边  * 高光（铆钉）  o 熔融  O 熔融亮
PAL = {
    ".": (0x4a, 0x4a, 0x52, 255),
    "#": (0x34, 0x36, 0x3b, 255),
    "@": (0x23, 0x23, 0x2a, 255),
    "+": (0x6e, 0x6e, 0x78, 255),
    "*": (0x9a, 0xa2, 0xac, 255),
    "o": (0xc4, 0x60, 0x22, 255),
    "O": (0xe8, 0x91, 0x2f, 255),
}

# 主控 / 外壳：上下亮边 + 四角铆钉 + 中间一道熔融炉栅 + 下面一个小出料口
SMELTER = [
    "++++++++++++++++",
    "#*##........##*#",
    "#..............#",
    "#..............#",
    "#..@@@@@@@@@@..#",
    "#..@o@o@o@o@@..#",
    "#..@O@O@O@O@@..#",
    "#..@o@o@o@o@@..#",
    "#..@@@@@@@@@@..#",
    "#..............#",
    "#.....@@@@.....#",
    "#.....@oo@.....#",
    "#..............#",
    "#*##........##*#",
    "################",
    "@@@@@@@@@@@@@@@@",
]

# 成型后的机体：一整面（会被铺在每个面上）—— 中间一个发光观察窗，四角铆钉
# ⚠ 这一张**上下镜像对称**（第 r 行 == 第 15−r 行）：老 OBJ 借的是均色贴图，
#   它的 v 到底是正着还是反着**从来没被证实过**；做成镜像对称之后，
#   "翻不翻"这个问题就不存在了（校验里有一条断言盯这一点）。
FORMED = [
    "++++++++++++++++",
    "#..............#",
    "#..............#",
    "#..@@@@@@@@@@..#",
    "#..@........@..#",
    "#..@........@..#",
    "#..@........@..#",
    "#..@.OOOOOO.@..#",
    "#..@.OOOOOO.@..#",
    "#..@........@..#",
    "#..@........@..#",
    "#..@........@..#",
    "#..@@@@@@@@@@..#",
    "#..............#",
    "#..............#",
    "++++++++++++++++",
]


def to_rgba(grid):
    out = bytearray()
    for row in grid:
        for ch in row:
            out += bytes(PAL[ch])
    return bytes(out)


def check_grid(name, grid):
    assert len(grid) == 16, u"%s：行数 %d ≠ 16" % (name, len(grid))
    for i, row in enumerate(grid):
        assert len(row) == 16, u"%s：第 %d 行 %d 列 ≠ 16" % (name, i, len(row))
        for ch in row:
            assert ch in PAL, u"%s：第 %d 行有未知字符 %r" % (name, i, ch)


def upscale(grid, k):
    u"""最近邻放大 k 倍（预览用：看得清每个像素）"""
    out = []
    for row in grid:
        big = u"".join(ch * k for ch in row)
        for _ in range(k):
            out.append(big)
    return out


def main():
    write = "--write" in sys.argv
    fail = 0
    for name, grid in ((u"alloy_smelter", SMELTER), (u"alloy_smelter_formed", FORMED)):
        try:
            check_grid(name, grid)
        except AssertionError as e:
            print(u"  [FAIL] %s" % e)
            fail += 1
            continue
        colors = len(set(u"".join(grid)))
        print(u"  [OK]   %-24s 16×16，用色 %d 种" % (name + u".png", colors))

    # ---- 预览图：1× 原图 + 6× 放大，并排 ----
    k = 6
    a, b = upscale(SMELTER, k), upscale(FORMED, k)
    W = 16 * k * 2 + 12
    H = 16 * k
    grid = []
    for y in range(H):
        row = []
        for x in range(W):
            if x < 16 * k:
                ch = a[y][x]
            elif x < 16 * k + 12:
                ch = u"#"
            else:
                ch = b[y][x - 16 * k - 12]
            row.append(PAL.get(ch, (0, 0, 0, 255)))
        grid.append(row)
    flat = bytearray()
    for row in grid:
        for c in row:
            flat += bytes(c)
    write_png(PREVIEW, W, H, bytes(flat))
    print(u"  预览图（左 = 主控/外壳，右 = 成型机体，6× 最近邻）：%s" % PREVIEW)

    if write:
        for name, grid in ((u"alloy_smelter", SMELTER), (u"alloy_smelter_formed", FORMED)):
            p = os.path.join(OUT, name + u".png")
            old = os.path.getsize(p) if os.path.exists(p) else -1
            write_png(p, 16, 16, to_rgba(grid))
            # 写-读往返自证（本工程老规矩）
            import struct
            b = open(p, "rb").read()
            w, h = struct.unpack(">II", b[16:24])
            assert (w, h) == (16, 16), u"%s 写出来不是 16×16" % name
            print(u"  [写出] %-24s 16×16  %d B（原来 %d B）" % (name + u".png",
                                                              os.path.getsize(p), old))
    else:
        print(u"\n（没写任何正式贴图；加 --write 才落盘）")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
