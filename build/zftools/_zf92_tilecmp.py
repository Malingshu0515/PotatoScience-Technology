# -*- coding: utf-8 -*-
r"""_zf92_tilecmp.py —— 高炉贴图里那些 16x16 瓦片，两两之间是不是同一张画（逐像素比）

用途：判断"艺术家本来想画成什么样"。如果 A 瓦片和 B 瓦片是同一张画的两个副本，
说明这两个面本来就该长一样 —— 那么模型里一个把 A 当顶面、另一个把 A 当底面，就必有一个是错的。

用法:
    python _zf92_tilecmp.py [容差]      # 默认容差 0（完全一致）
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

BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def main(argv):
    tol = int(argv[0]) if argv else 0
    d = json.loads(io.open(BB, encoding="utf-8").read())
    w, h, _, px = P.read_png(TEX)
    tiles = {}
    for ei, e in enumerate(d["elements"]):
        for fk, f in e["faces"].items():
            uu = [f["uv"][k][0] for k in f["vertices"]]
            vv = [f["uv"][k][1] for k in f["vertices"]]
            x0, y0 = int(min(uu)), int(min(vv))
            x1, y1 = int(max(uu)), int(max(vv))
            if x1 - x0 == 16 and y1 - y0 == 16:
                tiles.setdefault((x0, y0), []).append(ei)
    keys = sorted(tiles)
    print(u"16x16 瓦片 %d 张；逐对比较（容差 %d）：" % (len(keys), tol))

    def tile(k):
        x0, y0 = k
        return [px[(y0 + y) * w + x0 + x] for y in range(16) for x in range(16)]

    def diff(a, b):
        n = mx = 0
        for p, q in zip(a, b):
            dd = max(abs(p[i] - q[i]) for i in range(4))
            if dd > tol:
                n += 1
                mx = max(mx, dd)
        return n, mx

    ts = {k: tile(k) for k in keys}
    groups = []
    used = set()
    for i, k in enumerate(keys):
        if k in used:
            continue
        grp = [k]
        used.add(k)
        for k2 in keys[i + 1:]:
            if k2 in used:
                continue
            n, mx = diff(ts[k], ts[k2])
            if n == 0:
                grp.append(k2)
                used.add(k2)
        groups.append(grp)
    print(u"\n完全相同的瓦片分组成 %d 组：" % len(groups))
    for g in groups:
        if len(g) > 1:
            print(u"  %s   ← 同一张画" % u"  ".join(u"(%d,%d)" % k for k in g))
        else:
            print(u"  (%d,%d)  单独（元素 %s）" % (g[0][0], g[0][1], tiles[g[0]]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
