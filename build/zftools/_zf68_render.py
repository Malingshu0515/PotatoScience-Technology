# -*- coding: utf-8 -*-
"""_zf68_render.py —— 把 OBJ 用纯 Python 画成 PNG（本机没有 Blender/Pillow，只能自己画）

为什么要它：用户给的是 Blockbench 导出的模型，**光看数字看不出哪面是正面**（ZF58 那次"模型偏 3 格"
就是数字看走眼）。先用几张平面图把它看明白，再决定怎么烘到方块空间里。

画法：正交投影 + 画家算法（按面心深度排序）+ 平面着色（法线点乘光照）+ 描边。

用法:
    python _zf68_render.py <model.obj> --out <png> [--view iso|front|back|left|right|top] [--scale 60]
    python _zf68_render.py <model.obj> --out <png> --sheet        # 六视图拼一张
"""
import argparse
import io
import math
import struct
import sys
import zlib


def read_obj(path):
    vs, fcs = [], []
    cur = []
    for line in io.open(path, encoding="utf-8", errors="replace"):
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append((float(t[1]), float(t[2]), float(t[3])))
        elif t[0] == "f":
            idx = []
            for part in t[1:]:
                idx.append(int(part.split("/")[0]) - 1)
            fcs.append(idx)
    return vs, fcs


def normalize(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def face_normal(vs, idx):
    a, b, c = vs[idx[0]], vs[idx[1]], vs[idx[2]]
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return normalize((u[1] * w[2] - u[2] * w[1],
                      u[2] * w[0] - u[0] * w[2],
                      u[0] * w[1] - u[1] * w[0]))


VIEWS = {
    "iso":   ((1.0, 0.75, 1.0), "X+ Y+ Z+ 等轴"),
    "iso2":  ((-1.0, 0.75, -1.0), "X- Y+ Z- 等轴"),
    "front": ((0.0, 0.0, 1.0), "从 +Z 看"),
    "back":  ((0.0, 0.0, -1.0), "从 -Z 看"),
    "left":  ((-1.0, 0.0, 0.0), "从 -X 看"),
    "right": ((1.0, 0.0, 0.0), "从 +X 看"),
    "top":   ((0.0, 1.0, 0.0), "从 +Y 看"),
}


def render(vs, fcs, view, scale, size):
    eye = normalize(VIEWS[view][0])
    up = (0.0, 1.0, 0.0) if abs(eye[1]) < 0.99 else (0.0, 0.0, 1.0)
    # 相机基
    right = normalize((eye[2] * up[1] - eye[1] * up[2],
                       eye[0] * up[2] - eye[2] * up[0],
                       eye[1] * up[0] - eye[0] * up[1]))
    up2 = (eye[1] * right[2] - eye[2] * right[1],
           eye[2] * right[0] - eye[0] * right[2],
           eye[0] * right[1] - eye[1] * right[0])
    light = normalize((0.45, 0.85, 0.3))

    cx = sum(v[0] for v in vs) / len(vs)
    cy = sum(v[1] for v in vs) / len(vs)
    cz = sum(v[2] for v in vs) / len(vs)

    def project(p):
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        sx = sum(d[i] * right[i] for i in range(3))
        sy = sum(d[i] * up2[i] for i in range(3))
        sz = sum(d[i] * eye[i] for i in range(3))
        return (size / 2.0 + sx * scale, size / 2.0 - sy * scale, sz)

    polys = []
    for idx in fcs:
        pts = [project(vs[i]) for i in idx]
        depth = sum(p[2] for p in pts) / len(pts)
        n = face_normal(vs, idx)
        lam = max(0.0, sum(n[i] * light[i] for i in range(3)))
        shade = 0.35 + 0.65 * lam
        base = (176, 186, 196)
        col = tuple(int(c * shade) for c in base)
        polys.append((depth, [p[:2] for p in pts], col))
    polys.sort(key=lambda t: t[0])

    img = [[(248, 248, 250) for _ in range(size)] for _ in range(size)]
    for _, pts, col in polys:
        fill_poly(img, pts, col)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            line(img, a, b, (40, 40, 46))
    return img


def fill_poly(img, pts, col):
    size = len(img)
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            (x1, y1_) = pts[i]
            (x2, y2_) = pts[(i + 1) % n]
            if (y1_ <= y < y2_) or (y2_ <= y < y1_):
                t = (y - y1_) / (y2_ - y1_)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[k])), min(size - 1, int(xs[k + 1])) + 1):
                img[y][x] = col


def line(img, a, b, col):
    size = len(img)
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        t = i / float(n)
        x = int(a[0] + (b[0] - a[0]) * t)
        y = int(a[1] + (b[1] - a[1]) * t)
        if 0 <= x < size and 0 <= y < size:
            img[y][x] = col


def write_png(path, rows):
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for px in row:
            raw += bytes(px)

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    io.open(path, "wb").write(png)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("--out", required=True)
    ap.add_argument("--view", default="iso")
    ap.add_argument("--scale", type=float, default=60.0)
    ap.add_argument("--size", type=int, default=520)
    args = ap.parse_args(argv)

    vs, fcs = read_obj(args.obj)
    if not vs:
        print("没读到顶点")
        return 2
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [v[2] for v in vs]
    print("顶点 %d 面 %d" % (len(vs), len(fcs)))
    print("bbox X[%.3f,%.3f] Y[%.3f,%.3f] Z[%.3f,%.3f]" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    img = render(vs, fcs, args.view, args.scale, args.size)
    write_png(args.out, img)
    print("写出 %s（视图 %s：%s）" % (args.out, args.view, VIEWS[args.view][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
