# -*- coding: utf-8 -*-
"""_zf133_texture.py —— ZF133：把用户给的星璨钢斧贴图放到位（**原图直用，不转档**）

为什么这次不做任何处理：`星璨钢斧.png` 真解码出来就是 **16x16 RGBA / 256 像素**
（本工程物品贴图的规格），而且 62 个非透明像素、没有整张实心底 —— 直接拷即可。
（ZF66 / ZF122 那两次要转档，是因为素材是 32x32 或 JPEG。）

写盘后**立刻用真解码器读回来核对**（§4.92：只看文件头的检查不算数 ——
ZF122 的黑紫天空就是"IHDR 对、IDAT 只有一半"混过 `TextureCheck.py` 的）。

跑法：python build/zftools/_zf133_texture.py [--write]
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
import _zf66_png

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "用户素材", "星璨钢斧.png")
DST = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                   "textures", "item", "star_steel_axe.png")
MODEL = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                     "models", "item", "star_steel_axe.json")

WRITE = "--write" in sys.argv


def sha1(path):
    return hashlib.sha1(io.open(path, "rb").read()).hexdigest()


def sig(path):
    w, h, ctype, px = _zf66_png.read_png(path)
    opaque = sum(1 for p in px if p[3] > 0)
    return w, h, ctype, len(px), opaque


def main():
    print("源  : %s" % SRC)
    print("  sha1=%s" % sha1(SRC))
    sw, sh, sc, sn, sop = sig(SRC)
    print("  真解码 %dx%d ctype=%d pixels=%d 不透明=%d" % (sw, sh, sc, sn, sop))
    assert (sw, sh) == (16, 16), "素材不是 16x16，本轮的处理方式要重新想"
    assert sn == sw * sh, "素材 IDAT 与 IHDR 对不上"

    if WRITE:
        os.makedirs(os.path.dirname(DST), exist_ok=True)
        shutil.copyfile(SRC, DST)
        model = ('{\n  "parent": "minecraft:item/handheld",\n'
                 '  "textures": {\n    "layer0": "potato_s_t:item/star_steel_axe"\n  }\n}\n')
        io.open(MODEL, "w", encoding="utf-8", newline="\n").write(model)
        print("已写: %s" % DST)
        print("已写: %s" % MODEL)

    print("目标: %s （存在=%s）" % (DST, os.path.isfile(DST)))
    if os.path.isfile(DST):
        dw, dh, dc, dn, dop = sig(DST)
        print("  真解码 %dx%d ctype=%d pixels=%d 不透明=%d" % (dw, dh, dc, dn, dop))
        print("  sha1=%s" % sha1(DST))
        assert (dw, dh) == (16, 16) and dn == 256, "落盘后的贴图解不出来"
        assert dop == sop, "不透明像素数对不上（拷贝过程中被改过？）"
        print("  ✅ 与源图逐项一致（尺寸/像素数/不透明数）")
    print("模型: %s （存在=%s）" % (MODEL, os.path.isfile(MODEL)))
    if os.path.isfile(MODEL):
        print(io.open(MODEL, encoding="utf-8").read())


main()
