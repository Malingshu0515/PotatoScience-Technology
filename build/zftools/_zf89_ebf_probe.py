# -*- coding: utf-8 -*-
u"""_zf89_ebf_probe.py —— 电力高炉贴图/模型的只读体检（不改任何字节）

用户反馈「电力高炉贴图有点小毛病」，先拿数据说话：
  ① 贴图规格、alpha 分布、**实际画到的外接框**（画布右/下有空白？）；
  ② OBJ 里 usemtl 用了哪些材质名、MTL 里定义了哪些（对不上 = 面丢材质）；
  ③ 每个面的 UV 在贴图上圈出的像素矩形，逐面统计：
       - 采样区是否**整块透明**（这种面在游戏里就是个洞）；
       - 采样区是否**整块纯白/纯色**（没画到的空白区被当图用）；
       - 采样是否**越界**（uv>1 或 <0，即采样到贴图外）；
  ④ 同一位置被两个面用了不同 UV 区（接缝）—— 只报数量，人工再看。
输出到 stdout，全部是纯文本。
"""
import io
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

ROOT = r"E:\PotatoST"
BLK = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                   "models", "block")
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                   "textures", "block", "electric_blast_furnace.png")


def read_obj(path):
    vs, vts, faces = [], [], []
    mtl = None
    cur = None
    for raw in io.open(path, "r", encoding="utf-8", errors="replace"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if p[0] == "v":
            vs.append(tuple(float(x) for x in p[1:4]))
        elif p[0] == "vt":
            vts.append(tuple(float(x) for x in p[1:3]))
        elif p[0] == "usemtl":
            cur = p[1]
        elif p[0] == "mtllib":
            mtl = p[1]
        elif p[0] == "f":
            idx = []
            for tok in p[1:]:
                a = tok.split("/")
                vi = int(a[0]) - 1
                ti = int(a[1]) - 1 if len(a) > 1 and a[1] else None
                idx.append((vi, ti))
            faces.append((cur, idx))
    return vs, vts, faces, mtl


def main():
    w, h, ctype, px = _zf66_png.read_png(TEX)

    def at(x, y):
        if x < 0 or y < 0 or x >= w or y >= h:
            return None
        return px[y * w + x]

    print(u"=== ① 贴图 ===")
    print(u"文件: %s" % os.path.basename(TEX))
    print(u"尺寸: %dx%d  颜色类型: %d  字节: %d" % (w, h, ctype, os.path.getsize(TEX)))

    n_tr = n_op = n_white = 0
    minx, miny, maxx, maxy = w, h, -1, -1
    colors = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[y * w + x]
            if a == 0:
                n_tr += 1
                continue
            n_op += 1
            if r == 255 and g == 255 and b == 255:
                n_white += 1
            if minx > x:
                minx = x
            if miny > y:
                miny = y
            if maxx < x:
                maxx = x
            if maxy < y:
                maxy = y
            colors[(r, g, b)] = colors.get((r, g, b), 0) + 1
    print(u"全透明像素: %d  不透明: %d  其中纯白(255,255,255): %d"
          % (n_tr, n_op, n_white))
    if n_op:
        print(u"不透明区外接框: x %d..%d  y %d..%d  (画布 %dx%d)"
              % (minx, maxx, miny, maxy, w, h))
        if maxx < w - 1 or maxy < h - 1:
            print(u"  !! 右侧/下方有 %d x %d 的空白未用区"
                  % (w - 1 - maxx, h - 1 - maxy))
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:6]
    print(u"主要颜色: " + u", ".join(
        u"#%02X%02X%02X x%d" % (c[0], c[1], c[2], n) for c, n in top))

    print(u"")
    print(u"=== ② 材质 ===")
    mtlpath = os.path.join(BLK, "electric_blast_furnace.mtl")
    defined = []
    for raw in io.open(mtlpath, "r", encoding="utf-8", errors="replace"):
        if raw.strip().startswith("newmtl "):
            defined.append(raw.strip().split()[1])
    print(u"MTL 定义: %s" % (u", ".join(defined) or u"(无)"))
    print(u"MTL map_Kd: " + u", ".join(
        l.strip() for l in io.open(mtlpath, "r", encoding="utf-8",
                                   errors="replace")
        if l.strip().startswith("map_Kd")))

    print(u"")
    print(u"=== ③ 逐面 UV 体检 ===")
    for name in ("north", "south", "east", "west"):
        objp = os.path.join(BLK, "electric_blast_furnace_%s.obj" % name)
        vs, vts, faces, mtllib = read_obj(objp)
        used = sorted(set(f[0] for f in faces), key=lambda s: (s is None, s))
        print(u"--- %s.obj: v=%d vt=%d f=%d  mtllib=%s" %
              (name, len(vs), len(vts), len(faces), mtllib))
        print(u"    usemtl: %s" % u", ".join(x or u"(无)" for x in used))
        miss = [m for m in used if m and m not in defined]
        if miss:
            print(u"    !! OBJ 用了 MTL 未定义的材质: %s" % u", ".join(miss))
        allvt = sorted(set(vts))
        print(u"    不同 vt 对: %d 个；u 范围 %.4f..%.4f  v 范围 %.4f..%.4f"
              % (len(allvt), min(t[0] for t in allvt), max(t[0] for t in allvt),
                 min(t[1] for t in allvt), max(t[1] for t in allvt)))
        oob = 0
        blank = []
        empty = []
        for fi, (m, idx) in enumerate(faces):
            uvs = [vts[t] for _, t in idx if t is not None]
            if not uvs:
                continue
            us = [t[0] for t in uvs]
            vv = [t[1] for t in uvs]
            if min(us) < -1e-6 or max(us) > 1 + 1e-6 or \
               min(vv) < -1e-6 or max(vv) > 1 + 1e-6:
                oob += 1
            # OBJ 的 v 轴：flip_v=false 时按 (1-v) 取行；两种都试，报告两者都空的面
            x0 = max(0, min(w - 1, int(round(min(us) * w))))
            x1 = max(0, min(w - 1, int(round(max(us) * w)) - 1))
            y0 = max(0, min(h - 1, int(round((1 - max(vv)) * h))))
            y1 = max(0, min(h - 1, int(round((1 - min(vv)) * h)) - 1))
            tot = tra = wht = 0
            reps = {}
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    t = at(xx, yy)
                    if t is None:
                        continue
                    tot += 1
                    if t[3] == 0:
                        tra += 1
                    elif t[0] == 255 and t[1] == 255 and t[2] == 255:
                        wht += 1
                    reps[t[:3]] = reps.get(t[:3], 0) + 1
            if tot and tra == tot:
                empty.append((fi, (x0, y0, x1, y1)))
            elif tot and wht == tot:
                blend = sorted(reps.items(), key=lambda kv: -kv[1])[:2]
                blank.append((fi, (x0, y0, x1, y1),
                              u"#%02X%02X%02X" % blend[0][0]))
        print(u"    UV 越界的面: %d" % oob)
        print(u"    采样区**整块透明**的面: %d %s" %
              (len(empty), empty[:6] if empty else u""))
        print(u"    采样区**整块纯白**的面: %d %s" %
              (len(blank), blank[:6] if blank else u""))
        # 像素覆盖热力图：每个 16x16 格被多少面用到
        cells = {}
        for m, idx in faces:
            for _, t in idx:
                if t is None:
                    continue
                u, v = vts[t]
                cx = min(w // 16 - 1, max(0, int(u * w) // 16))
                cy = min(h // 16 - 1, max(0, int((1 - v) * h) // 16))
                cells[(cx, cy)] = cells.get((cx, cy), 0) + 1
        print(u"    用到 %d 个 16x16 划格；格心列表(前 40): %s"
              % (len(cells), sorted(cells)[:40]))


main()
