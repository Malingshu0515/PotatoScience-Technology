# -*- coding: utf-8 -*-
r"""_zf94_mirror.py —— 那对"格栅"瓦片是**镜像的一对**还是**两张不同的画**？（只读）

为什么要问：用户说"电力高炉的接线方块**对称一致**一下吧"。两根柱子现在只有 **东/西** 不一样
（一根是格栅、一根是素板），要改就先得决定"往哪边一致"：
  · 若东/西两张格栅是**同一个图案左右镜像**的一对 ⇒ 艺术家本来就是按"对称件"画的
    ⇒ 应该**镜像地**搬过去（#02 的东 = #01 的西、#02 的西 = #01 的东），这样从东西两侧看过去
    是同一幅镜像画；
  · 若两张只是"不一样的两张画" ⇒ 按"同一个方向用同一张"搬过去（两边完全一样）。

判据：把 B 与 A 逐像素比、再把 B 与 A 的**左右镜像**逐像素比，看哪一个为 0。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def tile(px, w, x0, y0, tw=16, th=16):
    return [px[(y0 + y) * w + x0 + x] for y in range(th) for x in range(tw)]


def cmp(a, b, tw=16, th=16):
    same = mir = 0
    for y in range(th):
        for x in range(tw):
            p, q = a[y * tw + x], b[y * tw + x]
            if p == q:
                same += 1
            r = b[y * tw + (tw - 1 - x)]
            if p == r:
                mir += 1
    return same, mir


def main():
    w, h, _, px = P.read_png(TEX)
    pairs = [
        (u"#01 东(47,144) vs #01 西(64,144)", (47, 144), (64, 144)),
        (u"#02 东(149,17) vs #02 西(149,34)", (149, 17), (149, 34)),
        (u"#01 东(47,144) vs #02 东(149,17)", (47, 144), (149, 17)),
        (u"#04 南(164,51) vs #04 北(164,68)", (164, 51), (164, 68)),
    ]
    for label, a, b in pairs:
        ta, tb = tile(px, w, *a), tile(px, w, *b)
        same, mir = cmp(ta, tb)
        verdict = (u"同一张画" if same == 256 else
                   (u"**左右镜像的一对**" if mir == 256 else
                    (u"不同（相同 %d/256，镜像后 %d/256）" % (same, mir))))
        print(u"%-42s ⇒ %s" % (label, verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
