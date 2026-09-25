# -*- coding: utf-8 -*-
r"""_zf92_view.py —— 按"游戏里的相机"渲一张高炉预览（透视投影），用于跟用户截图逐块对照

ZF91 那张预览是正交等距图，只能看"贴图有没有落到该落的地方"，看不出"实机视角下哪块是哪个零件"。
这里按 MC 的透视相机来：给定 相机位置 / yaw / pitch / fov / 分辨率，出图。

用法:
    python _zf92_view.py <out.png> <cx> <cy> <cz> <yaw> <pitch> [fov] [W] [H] [facing]
角度的正负沿用 MC：yaw=0 朝 +Z(南)，pitch=0 平视，pitch>0 朝下。
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402


def parse_obj(p):
    """⚠ 不能 import _zf91_render —— 那个脚本把 main(sys.argv) 写在模块级，一 import 就跑它自己的 main。"""
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MB = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def main(argv):
    out = argv[0]
    cx, cy, cz = (float(v) for v in argv[1:4])
    if argv[4] == "--look":            # 直接给目标点，免得手算 yaw/pitch（第一版就是这么算错方向的）
        tx, ty, tz = (float(v) for v in argv[5:8])
        dx, dy, dz = tx - cx, ty - cy, tz - cz
        yaw = math.degrees(math.atan2(dx, dz))
        pitch = -math.degrees(math.atan2(dy, math.sqrt(dx * dx + dz * dz)))
        rest = argv[8:]
    else:
        yaw, pitch = float(argv[4]), float(argv[5])
        rest = argv[6:]
    fov = float(rest[0]) if len(rest) > 0 else 70.0
    W = int(rest[1]) if len(rest) > 1 else 1066
    H = int(rest[2]) if len(rest) > 2 else 600
    facing = rest[3] if len(rest) > 3 else "north"
    # 可换 OBJ 目录：用来把"改前 / 改后"两份模型渲成同一机位的对照图
    objdir = MB
    for i, a in enumerate(sys.argv):
        if a == "--objdir":
            objdir = sys.argv[i + 1]
    src = os.path.join(objdir, "electric_blast_furnace_%s.obj" % facing)
    vs, vts, faces = parse_obj(src)
    tw, th, _, tex = P.read_png(TEX)

    ry, rp = math.radians(yaw), math.radians(pitch)
    # MC: yaw 0 => +Z(南)，yaw 增大朝 -X(西)；pitch>0 朝下
    # ⚠ ZF92 第一版把 sin 的符号写反了：forward 指到相机背后 ⇒ 152 个顶点全在背面，渲染出来是一张空图。
    fx, fy, fz = math.sin(ry) * math.cos(rp), -math.sin(rp), math.cos(ry) * math.cos(rp)
    rx, rz = -math.cos(ry), math.sin(ry)          # 右 = (0,1,0) × forward 的水平分量
    # 上 = 右 × 前（三分量叉积，别拿 ry 去凑 z—— 那是弧度，第一版就是这么写错的）
    ux = 0.0 * fz - rz * fy
    uy = rz * fx - rx * fz
    uz = rx * fy - 0.0 * fx
    focal = (H / 2.0) / math.tan(math.radians(fov) / 2.0)

    def cam(p):
        dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
        zc = dx * fx + dy * fy + dz * fz          # 深度
        xc = dx * rx + dz * rz
        yc = dx * ux + dy * uy + dz * uz
        return xc, yc, zc

    buf = [(24, 26, 32)] * (W * H)
    zbuf = [1e9] * (W * H)
    light = (-0.35, 0.86, -0.37)
    quads = []
    for f in faces:
        cs = [cam(vs[i]) for i, _ in f]
        if any(q[2] <= 0.05 for q in cs):
            continue
        pp = [(W / 2.0 + q[0] / q[2] * focal, H / 2.0 - q[1] / q[2] * focal, q[2]) for q in cs]
        a, b, c = vs[f[0][0]], vs[f[1][0]], vs[f[2][0]]
        u1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        u2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0])
        ln = math.sqrt(sum(q * q for q in n)) or 1.0
        n = tuple(q / ln for q in n)
        shade = 0.62 + 0.38 * abs(sum(n[i] * light[i] for i in range(3)))
        quads.append((sum(q[2] for q in pp) / len(pp), pp, f, shade))
    quads.sort(key=lambda q: -q[0])

    for depth, pp, f, shade in quads:
        uv = [vts[t] for _, t in f]
        tris = [(0, 1, 2), (0, 2, 3)] if len(pp) >= 4 else [(0, 1, 2)]
        for (ia, ib, ic) in tris:
            ax, ay = pp[ia][0], pp[ia][1]
            bx, by = pp[ib][0], pp[ib][1]
            cx2, cy2 = pp[ic][0], pp[ic][1]
            det = (bx - ax) * (cy2 - ay) - (cx2 - ax) * (by - ay)
            if abs(det) < 1e-9:
                continue
            uva, uvb, uvc = uv[ia], uv[ib], uv[ic]
            zs = (pp[ia][2], pp[ib][2], pp[ic][2])
            x0, x1 = max(0, int(min(ax, bx, cx2))), min(W - 1, int(max(ax, bx, cx2)) + 1)
            y0, y1 = max(0, int(min(ay, by, cy2))), min(H - 1, int(max(ay, by, cy2)) + 1)
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    w0 = ((bx - px) * (cy2 - py) - (cx2 - px) * (by - py)) / det
                    w1 = ((cx2 - px) * (ay - py) - (ax - px) * (cy2 - py)) / det
                    w2 = 1.0 - w0 - w1
                    if w0 < -0.002 or w1 < -0.002 or w2 < -0.002:
                        continue
                    z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
                    i = py * W + px
                    if z >= zbuf[i]:
                        continue
                    u = w0 * uva[0] + w1 * uvb[0] + w2 * uvc[0]
                    v = w0 * uva[1] + w1 * uvb[1] + w2 * uvc[1]
                    tx = min(tw - 1, max(0, int(u * tw)))
                    ty = min(th - 1, max(0, int(v * th)))
                    r, g, b, al = tex[ty * tw + tx]
                    if al == 0:
                        continue
                    zbuf[i] = z
                    buf[i] = (int(r * shade), int(g * shade), int(b * shade))
    P.write_png(out, W, H, [(r, g, b, 255) for r, g, b in buf])
    print(u"→ %s  (%dx%d) 相机 (%.2f,%.2f,%.2f) yaw %.1f pitch %.1f fov %.0f  %s"
          % (os.path.basename(out), W, H, cx, cy, cz, yaw, pitch, fov, facing))


if __name__ == "__main__":
    main(sys.argv[1:])
