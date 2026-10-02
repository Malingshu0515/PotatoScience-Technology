# -*- coding: utf-8 -*-
u"""_zf168_keybg.py —— 两张物品图的"透明底"重做：**从边界泛洪**抠近白背景

第一版只抠"与四角**颜色完全相同**"的像素：铝罐抠掉 45/256（背景干净），
可乐只抠掉 **4/256** —— 因为 JPEG 的白底被压缩成了一大片"近白但不完全相同"的像素
（四角各是 (243,247,250)/(252,255,255)/(255,252,255)…）⇒ 物品栏里会看到一块白方块。

改法（这也是像素画抠图的常规做法）：
  ① 把"近白"（min(r,g,b) ≥ 235）当**候选背景**；
  ② 只抠**与画布边界连通**的那些（四邻域泛洪）；
  ③ 内部的白（罐身高光、可乐标签的白字）**保住**。
源图用归档在 `build/用户素材/` 的那两张 JPEG（原字节），幂等可重跑。
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from PIL import Image

ROOT = r"E:\PotatoST"
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
SRC = os.path.join(ROOT, r"build\用户素材")
PAIRS = [(u"empty_aluminum_can.jpg", u"empty_aluminum_can.png"),
         (u"cola.jpg", u"cola.png")]
NEAR_WHITE = 235

fails = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def main():
    for src_name, png_name in PAIRS:
        src = os.path.join(SRC, src_name)
        if not os.path.exists(src):
            check(u"%s 在（归档的 JPEG 源）" % src_name, False)
            continue
        im = Image.open(src).convert("RGBA")
        px = im.load()
        w, h = im.size
        seen = [[False] * h for _ in range(w)]
        stack = []
        for x in range(w):
            stack += [(x, 0), (x, h - 1)]
        for y in range(h):
            stack += [(0, y), (w - 1, y)]
        cleared = 0
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= w or y >= h or seen[x][y]:
                continue
            seen[x][y] = True
            r, g, b, a = px[x, y]
            if min(r, g, b) < NEAR_WHITE:
                continue
            px[x, y] = (r, g, b, 0)
            cleared += 1
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        opaque = sum(1 for y in range(h) for x in range(w) if px[x, y][3] == 255)
        dst = os.path.join(TEX, png_name)
        im.save(dst, "PNG")
        back = Image.open(dst)
        check(u"%s：泛洪抠掉 %d 像素、剩下不透明 %d / %d（读回 %s %dx%d，%d 字节）"
              % (png_name, cleared, opaque, w * h, back.format, back.width, back.height,
                 os.path.getsize(dst)),
              cleared > 0 and opaque > 0 and back.format == "PNG")
        print(u"      sha1 = %s" % hashlib.sha1(open(dst, "rb").read()).hexdigest())

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
