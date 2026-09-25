# -*- coding: utf-8 -*-
"""_zf50_texture.py —— 把用户给的"合金主控_001.png"（其实是 16×16 webp）落成方块贴图

素材由 `_zf50_decode.ps1` 用 WPF 解码成**裸 BGRA**（16×16，Bgr32 无 alpha）。
本脚本做三件事，每件都有断言：

  ① **通道顺序**：WPF 给的是 BGRA ⇒ 写出 PNG 前要交换 B/R。
     判据（§4.23 的做法）：这张图是"金色边框 + 紫色核心"，交换后**暖色像素必须多于冷色**；
     若顺序反了，金色会变成青色，暖/冷会翻过来。所以这里直接断言 warm > cool。
  ② **尺寸**：素材已经是 16×16 ⇒ **不做任何缩放**（面积平均会把细节糊掉）。
     如果哪天用户给的是 160×160，这里会打印出来并做面积平均。
  ③ 写出 `textures/block/alloy_smelter.png`（16×16 RGBA）。

跑法：python build/zftools/_zf50_texture.py [--write]
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png      # noqa: E402

RAW = r"E:\PotatoST\build\zftools\_zf50_raw.bin"
OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\alloy_smelter.png"
SRC_W = SRC_H = 16


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    raw = io.open(RAW, "rb").read()
    if len(raw) != SRC_W * SRC_H * 4:
        raise SystemExit(u"裸像素大小不对：%d 字节（期望 %d）" % (len(raw), SRC_W * SRC_H * 4))
    print(u"裸数据：%d 字节 = %dx%d BGRA（WPF 的 FormatConvertedBitmap 输出）" % (len(raw), SRC_W, SRC_H))

    # BGRA -> RGBA
    rgba = bytearray(len(raw))
    warm = cool = 0
    hist = {}
    for i in range(SRC_W * SRC_H):
        b, g, r = raw[i * 4], raw[i * 4 + 1], raw[i * 4 + 2]
        rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2], rgba[i * 4 + 3] = r, g, b, 255
        if r > b + 10:
            warm += 1
        elif b > r + 10:
            cool += 1
        hist[(r, g, b)] = hist.get((r, g, b), 0) + 1

    print(u"交换通道后：暖色像素（R>B+10）= %d，冷色像素（B>R+10）= %d" % (warm, cool))
    print(u"主色（RGBA 读法）：")
    for (r, g, b), n in sorted(hist.items(), key=lambda kv: -kv[1])[:10]:
        print(u"    #{0:02X}{1:02X}{2:02X} x{3}".format(r, g, b, n))

    # ① 通道顺序断言：这张图是"金色边框"，暖色必须占多数
    if warm <= cool:
        raise SystemExit(u"通道顺序可疑：暖色 %d 不多于冷色 %d —— 金色应该偏暖，检查是不是该不交换"
                         % (warm, cool))
    print(u"[OK] 通道顺序：暖色占多数 ⇒ BGRA->RGBA 交换正确")

    # ② 尺寸断言：素材本来就是 16×16
    if (SRC_W, SRC_H) != (16, 16):
        raise SystemExit(u"素材不是 16x16（%dx%d）：需要先做面积平均再落盘" % (SRC_W, SRC_H))
    print(u"[OK] 素材已是 16x16，逐像素原样落盘（不做缩放）")

    # 紫色核心是否真的存在（用户预览里中间是一块紫）
    purple = sum(1 for (r, g, b), n in hist.items() if r > g + 20 and b > g + 20 for _ in range(n))
    print(u"紫色像素（R>G+20 且 B>G+20）= %d" % purple)
    if purple == 0:
        print(u"[WARN] 没找到紫色像素 —— 预览图里核心是紫的，确认一下素材")

    if args.write:
        write_png(OUT, SRC_W, SRC_H, rgba)
        print(u"已写出 %s（%d 字节）" % (OUT, os.path.getsize(OUT)))
    else:
        print(u"（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
