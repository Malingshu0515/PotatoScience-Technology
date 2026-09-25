# -*- coding: utf-8 -*-
u"""_zf89_texdump.py —— 把电力高炉 256×256 贴图分块放大（NEAREST）导出，供人眼细看

只读原贴图，只在 build/zftools 下写预览图。默认切 4 块，每块 128×128 放 2 倍。
用法: python _zf89_texdump.py [x0 y0 x1 y1 scale out.png]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def save(path, x0, y0, x1, y1, scale):
    w, h, ctype, px = _zf66_png.read_png(TEX)
    ow = (x1 - x0) * scale
    oh = (y1 - y0) * scale
    out = []
    for y in range(oh):
        sy = y0 + y // scale
        for x in range(ow):
            sx = x0 + x // scale
            if 0 <= sx < w and 0 <= sy < h:
                r, g, b, a = px[sy * w + sx]
            else:
                r, g, b, a = 255, 0, 255, 255
            out.append((r, g, b, 255 if a else 0))
    _zf66_png.write_png(path, ow, oh, out)
    print(u"%s  <- (%d,%d)-(%d,%d) x%d  %dx%d" %
          (os.path.basename(path), x0, y0, x1, y1, scale, ow, oh))


def main(argv):
    if len(argv) >= 7:
        save(argv[6], int(argv[1]), int(argv[2]), int(argv[3]), int(argv[4]),
             int(argv[5]))
        return
    d = os.path.dirname(os.path.abspath(__file__))
    # 四象限，各放大 2 倍
    save(os.path.join(d, "_zf89_ebf_tl.png"), 0, 0, 128, 128, 2)
    save(os.path.join(d, "_zf89_ebf_tr.png"), 128, 0, 256, 128, 2)
    save(os.path.join(d, "_zf89_ebf_bl.png"), 0, 128, 128, 256, 2)
    save(os.path.join(d, "_zf89_ebf_br.png"), 128, 128, 256, 256, 2)
    # 用户原稿 B 认的那块（左上 64x64），放大 4 倍
    save(os.path.join(d, "_zf89_ebf_tile64.png"), 0, 0, 64, 64, 4)


main(sys.argv)
