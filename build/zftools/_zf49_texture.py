# -*- coding: utf-8 -*-
"""_zf49_texture.py —— 合金冶炼炉控制器正面的贴图（16×16）

用户没给素材。这台机器的其它面**直接复用现成的两张**（顶面 = 耐热金属块、侧面 = 一般金属块），
只有正面需要一张新的：深色金属框 + 琥珀色炉膛观察窗 + 两侧铆钉。

只写一张 PNG，其余靠复用 —— 少一张贴图就少一处要维护的美术。
（第一版这里用了 `"…".replace("D","D")[:16]` 这种截断写法，结果两行的宽度是错的；
 现在每行都写全 16 个字符，并断言宽度。）
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png      # noqa: E402

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\alloy_smelter_front.png"
S = 16

# 图例：B=金属底 D=暗缝 L=高光 G=炉火（琥珀） 2=炉火暗部 R=铆钉
ROWS = [
    "BBBBBBBBBBBBBBBB",
    "BDDDDDDDDDDDDDDB",
    "BDLLLLLLLLLLLLDB",
    "BDLBBBBBBBBBBLDB",
    "BDLBGGGGGGGGBLDB",
    "BDLBGGGGGGGGBLDB",
    "BDLB22222222BLDB",
    "BDLBGGGGGGGGBLDB",
    "BDLB22222222BLDB",
    "BDLBGGGGGGGGBLDB",
    "BDLBGGGGGGGGBLDB",
    "BDLBBBBBBBBBBLDB",
    "BDLLLLLLLLLLLLDB",
    "BDDDDDDDDDDDDDDB",
    "BRBBBBBBBBBBBBRB",
    "BBBBBBBBBBBBBBBB",
]
PALETTE = {
    "B": (0x6E, 0x72, 0x78, 255),      # 金属底（与一般金属块同档灰）
    "D": (0x3C, 0x3F, 0x44, 255),      # 暗缝
    "L": (0x8E, 0x93, 0x9A, 255),      # 高光
    "G": (0xE8, 0x9A, 0x2B, 255),      # 炉火
    "2": (0xC2, 0x6A, 0x18, 255),      # 炉火暗部
    "R": (0x54, 0x58, 0x5E, 255),      # 铆钉
}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    rgba = bytearray(S * S * 4)
    for y, row in enumerate(ROWS):
        if len(row) != S:
            raise SystemExit(u"第 %d 行是 %d 列，应为 %d：%r" % (y, len(row), S, row))
        for x, ch in enumerate(row):
            p = (y * S + x) * 4
            rgba[p:p + 4] = bytes(PALETTE[ch])
    print(u"合金冶炼炉正面 %dx%d，%d 行全部 16 列" % (S, S, len(ROWS)))
    if args.write:
        write_png(OUT, S, S, rgba)
        print(u"已写出 %s（%d 字节）" % (OUT, os.path.getsize(OUT)))
    else:
        print(u"（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
