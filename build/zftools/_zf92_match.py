# -*- coding: utf-8 -*-
r"""_zf92_match.py —— 把截图里某个面的像素"抠"成 16x16，再跟贴图库逐个比对，报最像的几张

这是为了回答一个靠肉眼定不了的问题：截图里那个方块的面，到底用的是哪张图/哪一块？
做法：给出该面的四个角（原图像素坐标，按 A左 B上 C右 D下 的顺时针顺序），
     用双线性插值采成 16x16；再对每个候选贴图（含 4 个旋转）做"只差一个亮度系数"的
     最小二乘拟合，报残差最小的前几名。亮度系数是必须的——游戏里面有朝向明暗。

用法:
    python _zf92_match.py <截图.png> xA yA xB yB xC yC xD yD
"""
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

BLOCKDIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
EBF = os.path.join(BLOCKDIR, "electric_blast_furnace.png")


def bilinear(px, w, h, fx, fy):
    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - x0, fy - y0
    out = []
    for c in range(3):
        v = 0.0
        for (dx, dy, wgt) in ((0, 0, (1 - tx) * (1 - ty)), (1, 0, tx * (1 - ty)),
                              (0, 1, (1 - tx) * ty), (1, 1, tx * ty)):
            xx = min(w - 1, max(0, x0 + dx))
            yy = min(h - 1, max(0, y0 + dy))
            v += px[yy * w + xx][c] * wgt
        out.append(v)
    return out


def sample_quad(px, w, h, corners, n=16):
    """corners = [(xA,yA),(xB,yB),(xC,yC),(xD,yD)]（A左 B上 C右 D下，顺时针）。
    贴图坐标 (u,v)：(0,0)=A, (1,0)=B, (1,1)=C, (0,1)=D。"""
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = corners
    grid = []
    for j in range(n):
        v = (j + 0.5) / n
        for i in range(n):
            u = (i + 0.5) / n
            fx = (1 - u) * (1 - v) * ax + u * (1 - v) * bx + u * v * cx + (1 - u) * v * dx
            fy = (1 - u) * (1 - v) * ay + u * (1 - v) * by + u * v * cy + (1 - u) * v * dy
            grid.append(bilinear(px, w, h, fx, fy))
    return grid


def rot_grid(g, n, k):
    out = [None] * (n * n)
    for y in range(n):
        for x in range(n):
            if k == 0:
                sx, sy = x, y
            elif k == 1:
                sx, sy = y, n - 1 - x
            elif k == 2:
                sx, sy = n - 1 - x, n - 1 - y
            else:
                sx, sy = n - 1 - y, x
            out[y * n + x] = g[sy * n + sx]
    return out


def fit(a, b):
    """返回 (残差, 亮度系数)：最小化 |a - k*b|"""
    num = sum(a[i][c] * b[i][c] for i in range(len(a)) for c in range(3))
    den = sum(b[i][c] * b[i][c] for i in range(len(a)) for c in range(3))
    if den <= 0:
        return 1e9, 0.0
    k = num / den
    r = 0.0
    for i in range(len(a)):
        for c in range(3):
            d = a[i][c] - k * b[i][c]
            r += d * d
    return math.sqrt(r / (len(a) * 3)), k


def grid_from(px, w, h, x0, y0, n=16):
    return [list(px[(y0 + y) * w + (x0 + x)][:3]) for y in range(n) for x in range(n)]


def main(argv):
    shot = argv[0]
    coords = [float(v) for v in argv[1:9]]
    corners = [(coords[i], coords[i + 1]) for i in range(0, 8, 2)]
    sw, sh, _, spx = P.read_png(shot)
    g = sample_quad(spx, sw, sh, corners)
    print(u"从 %s 采到 16x16；四角 %s" % (os.path.basename(shot), corners))
    print(u"采样格中心色（左上 8x8 预览，格式 #RRGGBB）：")
    for y in range(0, 8):
        print(u"   " + u" ".join(u"%02X%02X%02X" % tuple(int(c) for c in g[y * 16 + x]) for x in range(8)))

    cands = []
    for name in sorted(os.listdir(BLOCKDIR)):
        if not name.endswith(".png"):
            continue
        path = os.path.join(BLOCKDIR, name)
        w, h, _, px = P.read_png(path)
        if w == 16 and h == 16:
            cands.append((name, 0, 0, px, w, h))
    # 高炉贴图里 114 个面用到的矩形（按 16x16 的只取整格）
    import json
    BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
    if os.path.exists(BB):
        d = json.loads(open(BB, encoding="utf-8").read())
        w, h, _, px = P.read_png(EBF)
        seen = set()
        for e in d["elements"]:
            for fk, f in e["faces"].items():
                uu = [f["uv"][k][0] for k in f["vertices"]]
                vv = [f["uv"][k][1] for k in f["vertices"]]
                x0, y0 = int(min(uu)), int(min(vv))
                if int(max(uu)) - x0 == 16 and int(max(vv)) - y0 == 16 and (x0, y0) not in seen:
                    seen.add((x0, y0))
                    cands.append((u"高炉贴图(%d,%d)" % (x0, y0), x0, y0, px, w, h))

    results = []
    for name, x0, y0, px, w, h in cands:
        cg = grid_from(px, w, h, x0, y0)
        for k in range(4):
            for mi in range(2):
                # ⚠ 第一版只试了 4 个旋转，没试镜像：四角顺序要是给反了，整块就是镜像的，
                #   任何旋转都对不上（当时最像的残差 20.7 其实一个都不像，就是这么来的）。
                gg = rot_grid(cg, 16, k)
                if mi:
                    gg = [gg[y * 16 + (15 - x)] for y in range(16) for x in range(16)]
                r, kk = fit(g, gg)
                results.append((r, name, k, mi, kk))
    results.sort()
    print(u"\n最像的 12 个（残差 = 只差一个亮度系数时的均方根误差；rot=旋转次数 mir=是否镜像）：")
    for r, name, k, mi, kk in results[:12]:
        print(u"   %6.2f  %-28s rot=%d mir=%d  亮度×%.2f" % (r, name, k, mi, kk))
    print(u"\n高炉贴图那 16 张 16x16 瓦片的排名：")
    ebf = [x for x in results if x[1].startswith(u"高炉")]
    for i, (r, name, k, mi, kk) in enumerate(ebf[:8]):
        print(u"   #%d  %6.2f  %-24s rot=%d mir=%d  亮度×%.2f" % (i + 1, r, name, k, mi, kk))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
