# -*- coding: utf-8 -*-
u"""_zf103_textures.py —— ZF103「星璨钢锭」的 16×16 物品贴图（用户素材优先）

背景：星璨钢锭（`potato_s_t:star_steel_ingot`）本轮是**盔甲修理材料**，
`models/item/star_steel_ingot.json` 的 layer0 指向 `potato_s_t:item/star_steel_ingot`。
缺这张图 ⇒ 背包里是紫黑格（`ModelCheck.py` 会报、游戏里不报错）。

两条来源，**用户的文件永远优先**：

  ① `build\\用户素材\\star_steel.png`（用户给的原始素材，任意尺寸/任意 PNG 变体）
     → 读出来、最近邻缩放到 16×16、归一成 RGBA，写到目标路径。
  ② 没有该文件 → **打印告警且不落盘**（不会用程序生成的图把用户素材的位置占掉）。
     要临时占位就显式加 `--placeholder`，那会画一张紫蓝发亮的锭子：
     形状直接借 `textures/item/titanium_ingot.png` 的 alpha（轮廓一致），
     颜色按"星璨"取深紫蓝底 + 亮蓝高光，与钛锭的钢灰分得开。

用法：
    python build/zftools/_zf103_textures.py                # 只看（报告会做什么）
    python build/zftools/_zf103_textures.py --write        # 有用户素材就写它
    python build/zftools/_zf103_textures.py --write --placeholder   # 没素材时写占位
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

USER_ASSET = r"E:\PotatoST\build\用户素材\star_steel.png"
OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\star_steel_ingot.png"
SHAPE_SOURCE = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\titanium_ingot.png"

# 占位配色：深紫蓝底 / 中间调 / 亮蓝高光（"星璨"= 夜里发亮的钢）
BASE = (54, 46, 96, 255)
MID = (86, 74, 150, 255)
LIGHT = (150, 190, 246, 255)
GLINT = (226, 240, 255, 255)


def to_rgba(img):
    u"""把 read_png 的结果归一成 (w, h, bytearray RGBA)。"""
    w, h = img[0], img[1]
    raw = img[2] if len(img) > 2 else img
    # PngRecolor.read_png 的返回形状在不同版本里可能是 (w,h,bytes) 或 (w,h,ch,bytes)
    if isinstance(raw, (bytes, bytearray)):
        pix = bytes(raw)
        ch = len(pix) // (w * h) if w * h else 0
    else:
        raise SystemExit(u"read_png 返回了看不懂的形状：%r" % (type(raw),))
    out = bytearray()
    for i in range(w * h):
        o = i * ch
        if ch >= 4:
            out += pix[o:o + 4]
        elif ch == 3:
            out += pix[o:o + 3] + b"\xff"
        elif ch == 2:
            out += bytes((pix[o], pix[o], pix[o], pix[o + 1]))
        elif ch == 1:
            out += bytes((pix[o], pix[o], pix[o], 255))
        else:
            raise SystemExit(u"无法识别的通道数：%d" % ch)
    return w, h, out


def resize_area(w, h, pix, nw=16, nh=16):
    u"""面积平均（box filter）缩放，alpha 加权。

    <p>为什么不是最近邻：用户素材是 160×160 的点阵放大稿，缩到 16×16 是 10:1，
    最近邻只能"挑一个像素代表 100 个"，边缘会掉锯齿；把 10×10 方块的**颜色按 alpha 加权平均**
    得到的轮廓更接近原画的观感。整数倍时它就是标准的 box filter，不引入插值糊。</p>
    """
    out = bytearray()
    for y in range(nh):
        y0 = y * h // nh
        y1 = max(y0 + 1, (y + 1) * h // nh)
        for x in range(nw):
            x0 = x * w // nw
            x1 = max(x0 + 1, (x + 1) * w // nw)
            r = g = b = a = n = 0
            for sy in range(y0, min(y1, h)):
                for sx in range(x0, min(x1, w)):
                    o = (sy * w + sx) * 4
                    av = pix[o + 3]
                    r += pix[o] * av
                    g += pix[o + 1] * av
                    b += pix[o + 2] * av
                    a += av
                    n += 1
            if a == 0 or n == 0:
                out += b"\x00\x00\x00\x00"
            else:
                out += bytes((r // a, g // a, b // a, a // n))
    return bytes(out)


def placeholder():
    u"""借钛锭的轮廓、换成紫蓝配色 —— 轮廓一致才看得出"这是同一类东西"。"""
    sw, sh, spix = to_rgba(read_png(SHAPE_SOURCE))
    if (sw, sh) != (16, 16):
        spix = resize_area(sw, sh, spix)
    out = bytearray()
    for y in range(16):
        for x in range(16):
            o = (y * 16 + x) * 4
            a = spix[o + 3]
            if a == 0:
                out += b"\x00\x00\x00\x00"
                continue
            # 用原图的亮度当"高度"：亮处 = 高光，暗处 = 底色
            lum = (spix[o] * 299 + spix[o + 1] * 587 + spix[o + 2] * 114) // 1000
            if lum >= 190:
                c = GLINT
            elif lum >= 130:
                c = LIGHT
            elif lum >= 80:
                c = MID
            else:
                c = BASE
            out += bytes((c[0], c[1], c[2], a))
    return bytes(out)


def main():
    write = "--write" in sys.argv
    allow_placeholder = "--placeholder" in sys.argv
    print(u"目标：%s" % OUT)
    print(u"用户素材：%s  %s" % (USER_ASSET, u"（存在）" if os.path.isfile(USER_ASSET) else u"（**不存在**）"))

    if os.path.isfile(USER_ASSET):
        w, h, pix = to_rgba(read_png(USER_ASSET))
        print(u"  读到 %d×%d" % (w, h))
        if (w, h) != (16, 16):
            pix = resize_area(w, h, pix)
            print(u"  → 面积平均缩放到 16×16")
        if write:
            write_png(OUT, 16, 16, pix)
            print(u"  [写出] %s  %d B" % (os.path.basename(OUT), os.path.getsize(OUT)))
        else:
            print(u"  （没写任何字节；加 --write 才落盘）")
        return 0

    if not allow_placeholder:
        print(u"")
        print(u"⚠ 用户素材不在 ⇒ **本轮什么都不写**（不用程序生成的图占掉那个位置）。")
        print(u"   要么把素材放到 %s，" % USER_ASSET)
        print(u"   要么显式加 --placeholder 先放一张紫蓝占位。")
        return 0

    pix = placeholder()
    print(u"  生成占位（借 titanium_ingot 的轮廓 + 紫蓝配色）")
    if write:
        write_png(OUT, 16, 16, pix)
        print(u"  [写出] %s  %d B" % (os.path.basename(OUT), os.path.getsize(OUT)))
    else:
        print(u"  （没写任何字节；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
