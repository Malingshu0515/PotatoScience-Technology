# -*- coding: utf-8 -*-
"""_zf92_dbg.py —— 相机变换排查：顶点到底投到哪去了（一次性诊断用）

用法:
    python _zf92_dbg.py                      # 默认两组相机
    python _zf92_dbg.py cx cy cz yaw pitch   # 指定一组
"""
import io
import math
import sys

OBJ = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"
W, H, FOV = 1066, 600, 70.0

vs = []
for raw in io.open(OBJ, encoding="utf-8", errors="replace"):
    t = raw.split()
    if t and t[0] == "v":
        vs.append(tuple(float(x) for x in t[1:4]))
xs = [v[0] for v in vs]
ys = [v[1] for v in vs]
zs = [v[2] for v in vs]
print(u"OBJ 包围盒 X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f  顶点 %d"
      % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), len(vs)))
print(u"模型中心 (%.2f, %.2f, %.2f)"
      % ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, (min(zs) + max(zs)) / 2.0))


def probe(cx, cy, cz, yaw, pitch):
    ry, rp = math.radians(yaw), math.radians(pitch)
    fx, fy, fz = math.sin(ry) * math.cos(rp), -math.sin(rp), math.cos(ry) * math.cos(rp)
    rx, rz = -math.cos(ry), math.sin(ry)
    ux = 0.0 * fz - rz * fy
    uy = rz * fx - rx * fz
    uz = rx * fy - 0.0 * fx
    focal = (H / 2.0) / math.tan(math.radians(FOV) / 2.0)
    print(u"\n--- 相机 (%.2f,%.2f,%.2f) yaw %.0f pitch %.0f ---" % (cx, cy, cz, yaw, pitch))
    print(u"前=(%.3f,%.3f,%.3f) 右=(%.3f,·,%.3f) 上=(%.3f,%.3f,%.3f) 焦距=%.1f"
          % (fx, fy, fz, rx, rz, ux, uy, uz, focal))
    print(u"正交性 前·右=%.4f 前·上=%.4f 右·上=%.4f"
          % (fx * rx + fz * rz, fx * ux + fy * uy + fz * uz, rx * ux + rz * uz))
    ds = []
    for p in vs:
        dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
        ds.append(dx * fx + dy * fy + dz * fz)
    print(u"深度 min=%.2f max=%.2f  在前的顶点=%d/%d" % (min(ds), max(ds), sum(1 for q in ds if q > 0.05), len(vs)))
    if min(ds) > 0:
        sxs, sys_ = [], []
        for p in vs:
            dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
            zc = dx * fx + dy * fy + dz * fz
            xc = dx * rx + dz * rz
            yc = dx * ux + dy * uy + dz * uz
            sxs.append(W / 2.0 + xc / zc * focal)
            sys_.append(H / 2.0 - yc / zc * focal)
        inside = sum(1 for i in range(len(sxs)) if 0 <= sxs[i] <= W and 0 <= sys_[i] <= H)
        print(u"投影 x %.0f..%.0f  y %.0f..%.0f  落在画面内 %d" % (min(sxs), max(sxs), min(sys_), max(sys_), inside))


if len(sys.argv) >= 6:
    probe(*[float(v) for v in sys.argv[1:6]])
else:
    for args in [(5.5, 2.2, 5.5, 130.0, -18.0), (5.5, 2.2, 5.5, 40.0, -18.0),
                 (0.5, 2.5, 9.0, 180.0, -10.0), (9.0, 2.5, 0.5, 90.0, -10.0)]:
        probe(*args)
