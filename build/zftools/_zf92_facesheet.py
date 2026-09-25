# -*- coding: utf-8 -*-
r"""_zf92_facesheet.py —— 把指定元素的面从贴图上抠出来拼成一张对照表（放大 8 倍）

用户说"某个小方块的**顶面和正面贴图对调一下**"。要判断"该不该调、怎么调"，先得看清
那个方块现在六个面各用的哪张图长什么样。把候选元素的 6 个面并排贴出来最直观。

用法:
    python _zf92_facesheet.py <out.png> <元素序号,逗号分隔> [放大倍数]
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
# ⚠ 面键名每个元素都不一样（#01/#02 是 QpQPdgCV…，#03/#04 是 i8atXuFb…），
#   千万不要按键名硬认方向。这里按**世界法线**分类（ZF92 第一版就是按键名写的，结果四行全错位）。
DIRS = [(u"上", (0, 1, 0)), (u"下", (0, -1, 0)), (u"北", (0, 0, -1)), (u"南", (0, 0, 1)),
        (u"东", (1, 0, 0)), (u"西", (-1, 0, 0))]


def rot_xyz(rx, ry, rz):
    """XYX 顺序（R = Rx·Ry·Rz）—— ZF91 用镜像元素对实测过：XYZ 误差 0.000000，ZYX 误差 252.11"""
    import math
    ax, ay, az = (math.radians(v) for v in (rx, ry, rz))
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    return ((cy * cz, -cy * sz, sy),
            (sx * sy * cz + cx * sz, -sx * sy * sz + cx * cz, -sx * cy),
            (-cx * sy * cz + sx * sz, cx * sy * sz + sx * cz, cx * cy))


def face_normal(e, f):
    import math
    o = e["origin"]
    m = rot_xyz(*(e.get("rotation") or [0, 0, 0]))
    vv = e.get("vertices", {})
    w = []
    for k in f["vertices"][:3]:
        loc = vv[k]
        w.append([o[j] + sum(m[j][t] * loc[t] for t in range(3)) for j in range(3)])
    u1 = [w[1][j] - w[0][j] for j in range(3)]
    u2 = [w[2][j] - w[0][j] for j in range(3)]
    n = [u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0]]
    ln = math.sqrt(sum(q * q for q in n)) or 1.0
    return [q / ln for q in n]


def pick_faces(e):
    """返回 {方向名: face}，方向由世界法线定。"""
    got = {}
    for fk, f in e["faces"].items():
        n = face_normal(e, f)
        for name, d in DIRS:
            if sum(n[i] * d[i] for i in range(3)) > 0.9:
                got[name] = f
    return got


def main(argv):
    out = argv[0]
    idxs = [int(v) for v in argv[1].split(",")]
    scale = int(argv[2]) if len(argv) > 2 else 8
    d = json.loads(io.open(BB, encoding="utf-8").read())
    tw, th, _, tex = P.read_png(TEX)
    cell = 24 * scale
    W = cell * 6
    H = cell * len(idxs)
    print(u"对照表 %dx%d（每格 %dpx = 面外接矩形上限 24 像素 × %d）" % (W, H, cell, scale))
    buf = [(30, 32, 38, 255)] * (W * H)
    for row, ei in enumerate(idxs):
        e = d["elements"][ei]
        faces = pick_faces(e)
        for col, (label, _d) in enumerate(DIRS):
            f = faces.get(label)
            if not f:
                continue
            uvs = f["uv"]
            uu = [uvs[k][0] for k in f["vertices"]]
            vv = [uvs[k][1] for k in f["vertices"]]
            x0, x1 = int(round(min(uu))), int(round(max(uu)))
            y0, y1 = int(round(min(vv))), int(round(max(vv)))
            fw, fh = x1 - x0, y1 - y0
            for oy in range(fh * scale):
                for ox in range(fw * scale):
                    r, g, b, a = tex[(y0 + oy // scale) * tw + (x0 + ox // scale)]
                    px = col * cell + ox
                    py = row * cell + oy
                    if 0 <= px < W and 0 <= py < H:
                        buf[py * W + px] = (r, g, b, 255) if a else (255, 0, 255, 255)
            print(u"  元素 #%02d 面 %-4s 贴图 x %3d..%-3d y %3d..%-3d  尺寸 %2dx%-2d"
                  % (ei, label, x0, x1, y0, y1, fw, fh))
    # 每格画白边
    for row in range(len(idxs)):
        for col in range(7):
            x = min(W - 1, col * cell)
            for y in range(row * cell, min(H, (row + 1) * cell)):
                buf[y * W + x] = (255, 255, 255, 255)
    for row in range(len(idxs) + 1):
        y = min(H - 1, row * cell)
        for x in range(W):
            buf[y * W + x] = (255, 255, 255, 255)
    P.write_png(out, W, H, buf)
    print(u"→ %s（列序：上 下 北 南 东 西）" % out)


if __name__ == "__main__":
    main(sys.argv[1:])
