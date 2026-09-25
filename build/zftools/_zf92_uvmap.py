# -*- coding: utf-8 -*-
r"""_zf92_uvmap.py —— 把贴图上"哪个像素块被哪个面用了"画成一张索引图 + 面清单

用途：用户说"某个小块的顶面和正面贴图对调一下"。要判断"对调"是不是真需要动模型，
得先看清：那一小块用的两个矩形在贴图上分别长什么样。

输出：
  · 一张 256x256 的索引图（每个被占用的像素涂成"面序号"的伪彩色），写到 build/zftools；
  · 指定序号的面的四角世界坐标 + 贴图矩形。
用法:
    python _zf92_uvmap.py            # 只打印每个元素的 6 个面 -> 贴图矩形（不落盘）
"""
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"
OUT = os.path.join(HERE, "_zf92_uvindex.png")
W = H = 256


def main():
    d = json.loads(io.open(BB, encoding="utf-8").read())
    els = d["elements"]
    tw, th, _, tex = P.read_png(TEX)
    px = [(20, 20, 24, 255)] * (W * H)
    # 每个元素一个色相，6 个面用明暗区分
    pal = [(230, 60, 60), (240, 150, 40), (240, 230, 60), (90, 220, 90),
           (70, 190, 230), (110, 110, 240), (220, 90, 200), (170, 220, 90),
           (250, 120, 160), (120, 240, 200)]
    occ = {}
    for ei, e in enumerate(els):
        col = pal[ei % len(pal)]
        for fi, (fk, f) in enumerate(sorted(e["faces"].items())):
            uvs = f["uv"]
            uu = [uvs[k][0] for k in f["vertices"]]
            vv = [uvs[k][1] for k in f["vertices"]]
            x0, x1 = int(round(min(uu))), int(round(max(uu)))
            y0, y1 = int(round(min(vv))), int(round(max(vv)))
            shade = 1.0 - 0.09 * fi
            c = (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade), 255)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if 0 <= x < W and 0 <= y < H:
                        px[y * W + x] = c
                        occ[(x, y)] = (ei, fi)
            # 只在贴图上有不透明像素的地方画
    P.write_png(OUT, W, H, px)
    print(u"索引图 -> %s" % OUT)

    # 统计每个元素占了多少像素、落在原贴图上有多少不透明像素
    print(u"\n== 每个元素的贴图占用 / 画了没画 ==")
    for ei, e in enumerate(els):
        rects = []
        for fk, f in sorted(e["faces"].items()):
            uvs = f["uv"]
            uu = [uvs[k][0] for k in f["vertices"]]
            vv = [uvs[k][1] for k in f["vertices"]]
            rects.append((int(min(uu)), int(min(vv)), int(max(uu)), int(max(vv))))
        tot = op = 0
        seen = set()
        for (x0, y0, x1, y1) in rects:
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if (x, y) in seen:
                        continue
                    seen.add((x, y))
                    tot += 1
                    if tex[y * tw + x][3]:
                        op += 1
        print(u"  #%02d %-14s 占 %5d 像素，其中画过 %5d，透明 %5d  矩形 %s"
              % (ei, (e.get("name") or u"")[:14], tot, op, tot - op,
                 u" ".join(u"(%d,%d)-(%d,%d)" % r for r in rects[:2])))


if __name__ == "__main__":
    main()
