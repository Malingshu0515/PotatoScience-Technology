# -*- coding: utf-8 -*-
r"""_zf92_bbfaces.py —— 把 .bbmodel 的 114 个面摊平成表：世界四角、法线、贴图矩形

为什么要这张表：用户说"高炉上某个小方块（接线块？）**顶面和正面贴图对调了**"。
模型是 Free/mesh，UV 是逐顶点的，所以"这个面用了贴图哪一块"是可以**直接算出来**的，
不需要靠猜或靠眼睛。把候选元素的面列出来，再跟贴图上那块区域长什么样对一下，就能定位。

用法:
    python _zf92_bbfaces.py                  # 全部 19 个元素的面表（含世界包围盒）
    python _zf92_bbfaces.py --near 1.0 2.0   # 只看 Y 世界坐标落在 [1.0,2.0] 的元素（"小方块"）
"""
import io
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
RES = 256.0


def rot_xyz(rx, ry, rz):
    """XYZ 顺序（R = Rx·Ry·Rz）—— ZF91 用镜像元素对实测过：XYZ 误差 0.000000，ZYX 误差 252.11"""
    ax, ay, az = (math.radians(v) for v in (rx, ry, rz))
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    # Rx·Ry·Rz
    return (
        (cy * cz, -cy * sz, sy),
        (sx * sy * cz + cx * sz, -sx * sy * sz + cx * cz, -sx * cy),
        (-cx * sy * cz + sx * sz, cx * sy * sz + sx * cz, cx * cy),
    )


def apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def main(argv):
    near = None
    if "--near" in argv:
        i = argv.index("--near")
        near = (float(argv[i + 1]), float(argv[i + 2]))
    d = json.loads(io.open(BB, encoding="utf-8").read())
    els = d.get("elements", [])
    print(u"resolution=%s  model_format=%s  元素数=%d"
          % (d.get("resolution"), d.get("meta", {}).get("model_format"), len(els)))
    for i, e in enumerate(els):
        o = e["origin"]
        rot = e.get("rotation") or [0, 0, 0]
        m = rot_xyz(*rot)
        vs = e.get("vertices", {})
        wp = {k: tuple(o[j] + apply(m, v)[j] for j in range(3)) for k, v in vs.items()}
        xs = [p[0] for p in wp.values()]
        ys = [p[1] for p in wp.values()]
        zs = [p[2] for p in wp.values()]
        name = e.get("name") or u""
        if near and not (near[0] <= min(ys) and max(ys) <= near[1] + 0.0001 and min(ys) >= near[0] - 0.0001):
            continue
        print(u"\n== #%02d %s  origin=%s rot=%s  世界 X %.2f..%.2f Y %.2f..%.2f Z %.2f..%.2f"
              % (i, name, o, rot, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
        faces = e.get("faces", {})
        for fk in sorted(faces.keys()):
            f = faces[fk]
            keys = f["vertices"]
            uvs = f.get("uv", {})
            corners = [wp[k] for k in keys]
            # 世界法线（用前三顶点叉积）
            a, b, c = corners[0], corners[1], corners[2]
            u1 = [b[j] - a[j] for j in range(3)]
            u2 = [c[j] - a[j] for j in range(3)]
            n = [u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0]]
            ln = math.sqrt(sum(q * q for q in n)) or 1.0
            n = [q / ln for q in n]
            uu = [uvs[k][0] for k in keys]
            vv = [uvs[k][1] for k in keys]
            # Blockbench UV 是像素、左上原点；转成我们的纹理像素矩形
            x0, x1 = min(uu), max(uu)
            y0, y1 = min(vv), max(vv)
            up = u"上" if n[1] > 0.9 else (u"下" if n[1] < -0.9 else
                                           (u"北" if n[2] < -0.9 else (u"南" if n[2] > 0.9 else
                                                                      (u"西" if n[0] < -0.9 else (u"东" if n[0] > 0.9 else u"斜")))))
            print(u"   %-4s n=(%5.2f,%5.2f,%5.2f) %s  贴图像素 x %6.1f..%-6.1f y %6.1f..%-6.1f"
                  % (fk, n[0], n[1], n[2], up, x0, x1, y0, y1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
