# -*- coding: utf-8 -*-
r"""_zf91_render.py —— 把烘好的 OBJ 用软件光栅器渲成一张预览图（等距视角，看得见就算数）

不是"渲染器"级别的正确性证明（游戏里的光照/朝向以实机为准），而是给用户**先看一眼**：
  · 每个面按 OBJ 的 vt 采样贴图；
  · 画家算法（按面心深度排序）+ 背面剔除；
  · 面法线的简单方向光，方便看出形体。
只读入参，只往 build/zftools 写预览图。
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png")
OUT = os.path.join(HERE, "_zf91_preview.png")
W, H = 900, 1000


def parse_obj(p):
    vs, vts, faces = [], [], []
    for raw in io.open(p, encoding="utf-8", errors="replace"):
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "vt":
            vts.append(tuple(float(x) for x in t[1:3]))
        elif t[0] == "f":
            faces.append([(int(a.split("/")[0]) - 1, int(a.split("/")[1]) - 1) for a in t[1:]])
    return vs, vts, faces


def main(argv):
    facing = argv[1] if len(argv) > 1 else "north"
    yaw = float(argv[2]) if len(argv) > 2 else 35.0
    pitch = float(argv[3]) if len(argv) > 3 else 22.0
    src = os.path.join(MB, "electric_blast_furnace_%s.obj" % facing)
    vs, vts, faces = parse_obj(src)
    tw, th, _, tex = _zf66_png.read_png(TEX)
    print(u"读入 %s：v=%d vt=%d f=%d；贴图 %dx%d" % (os.path.basename(src), len(vs), len(vts), len(faces), tw, th))

    # 相机：模型中心 -> 屏幕；等距（正交）+ 绕 Y 的 yaw、绕 X 的 pitch
    cx = (min(v[0] for v in vs) + max(v[0] for v in vs)) / 2.0
    cy = (min(v[1] for v in vs) + max(v[1] for v in vs)) / 2.0
    cz = (min(v[2] for v in vs) + max(v[2] for v in vs)) / 2.0
    scale = 150.0
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cb, sb = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    light = (0.35, 0.86, -0.37)

    def proj(p):
        x, y, z = p[0] - cx, p[1] - cy, p[2] - cz
        x, z = x * ca + z * sa, -x * sa + z * ca          # yaw
        y, z = y * cb - z * sb, y * sb + z * cb           # pitch
        return (W / 2 + x * scale, H / 2 - y * scale, z)

    buf = [(26, 26, 30)] * (W * H)
    zbuf = [1e9] * (W * H)

    quads = []
    for f in faces:
        pp = [proj(vs[i]) for i, _ in f]
        # 背面剔除（屏幕空间有向面积）
        area = sum((pp[k][0] * pp[(k + 1) % len(pp)][1] - pp[(k + 1) % len(pp)][0] * pp[k][1])
                   for k in range(len(pp))) / 2.0
        if area >= 0:
            continue
        depth = sum(q[2] for q in pp) / len(pp)
        a, b, c = vs[f[0][0]], vs[f[1][0]], vs[f[2][0]]
        u1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        u2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0])
        ln = math.sqrt(sum(q * q for q in n)) or 1.0
        n = tuple(q / ln for q in n)
        # 法线朝观察者一侧（因为背面已剔除，取绝对值更稳）
        shade = 0.55 + 0.45 * abs(sum(n[i] * light[i] for i in range(3)))
        quads.append((depth, pp, f, shade))
    quads.sort(key=lambda q: -q[0])            # 远的先画

    for depth, pp, f, shade in quads:
        uv = [vts[t] for _, t in f]
        # ⚠ 第一版只按三角形 (a,b,c) 光栅化 ⇒ 每个四边形**只画了一半**（预览图上那些三角缺口就是这个）。
        #   改成拆成两个三角形 (0,1,2) 与 (0,2,3)，各自插值 UV。
        tris = [(0, 1, 2), (0, 2, 3)] if len(pp) >= 4 else [(0, 1, 2)]
        for (ia, ib, ic) in tris:
            ax, ay = pp[ia][0], pp[ia][1]
            bx, by = pp[ib][0], pp[ib][1]
            cx2, cy2 = pp[ic][0], pp[ic][1]
            det = (bx - ax) * (cy2 - ay) - (cx2 - ax) * (by - ay)
            if abs(det) < 1e-9:
                continue
            uva, uvb, uvc = uv[ia], uv[ib], uv[ic]
            x0, x1 = max(0, int(min(ax, bx, cx2))), min(W - 1, int(max(ax, bx, cx2)) + 1)
            y0, y1 = max(0, int(min(ay, by, cy2))), min(H - 1, int(max(ay, by, cy2)) + 1)
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    w0 = ((bx - px) * (cy2 - py) - (cx2 - px) * (by - py)) / det
                    w1 = ((cx2 - px) * (ay - py) - (ax - px) * (cy2 - py)) / det
                    w2 = 1.0 - w0 - w1
                    if w0 < -0.002 or w1 < -0.002 or w2 < -0.002:
                        continue
                    u = w0 * uva[0] + w1 * uvb[0] + w2 * uvc[0]
                    v = w0 * uva[1] + w1 * uvb[1] + w2 * uvc[1]
                    tx = min(tw - 1, max(0, int(u * tw)))
                    ty = min(th - 1, max(0, int(v * th)))
                    r, g, b, al = tex[ty * tw + tx]
                    if al == 0:
                        continue
                    i = py * W + px
                    if depth < zbuf[i]:
                        zbuf[i] = depth
                        buf[i] = (int(r * shade), int(g * shade), int(b * shade))
    _zf66_png.write_png(OUT, W, H, [(r, g, b, 255) for r, g, b in buf])
    print(u"预览图 → %s（%s 朝向，yaw %.0f° pitch %.0f°）" % (os.path.basename(OUT), facing, yaw, pitch))


main(sys.argv)
