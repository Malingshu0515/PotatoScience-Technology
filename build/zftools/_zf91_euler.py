# -*- coding: utf-8 -*-
r"""_zf91_euler.py —— 给欧拉角顺序定案（只关心带两个非零分量的那两个元素）

`_zf91_bake.py` 第一版用"随便找一对镜像元素"来定顺序 ⇒ 两个顺序误差一模一样（选错了对），
定不了案。真正该看的是这一对：
    #09  origin [0, 58, -13]  rotation [ 10, -90, 0]
    #10  origin [0, 58,  13]  rotation [-10, -90, 0]
它们关于 Z=0 平面互为镜像 ⇒ 把 #09 的世界顶点按 z→−z 镜像后，应当与 #10 的顶点**逐点吻合**。
吻合得好的那个顺序才是 Blockbench 用的顺序。
只读。
"""
import io
import json
import math
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"


def ax(a, i):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    if i == 0:
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if i == 1:
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rot(rx, ry, rz, order):
    Rx, Ry, Rz = ax(rx, 0), ax(ry, 1), ax(rz, 2)
    return mul(mul(Rx, Ry), Rz) if order == "XYZ" else mul(mul(Rz, Ry), Rx)


def world(pts, origin, rotation, order):
    m = rot(rotation[0], rotation[1], rotation[2], order)
    out = []
    for v in pts:
        p = [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]
        out.append(tuple(p[i] + origin[i] for i in range(3)))
    return out


d = json.loads(io.open(BB, encoding="utf-8").read())
els = [e for e in d.get("elements", []) if e.get("type") == "mesh"]
# 按 origin 找那一对
pair = None
for a in els:
    for b in els:
        oa, ob = a.get("origin"), b.get("origin")
        if oa == [0, 58, -13] and ob == [0, 58, 13]:
            pair = (a, b)
if pair is None:
    print(u"没找到 [0,58,-13] / [0,58,13] 那一对，改成按 rotation 找")
    cand = [e for e in els if e.get("rotation", [0, 0, 0])[0] != 0]
    for e in cand:
        print(u"  非零 X 分量：origin=%s rot=%s" % (e.get("origin"), e.get("rotation")))
    sys.exit(1)

a, b = pair
print(u"配对：")
print(u"  A origin=%s rotation=%s  顶点 %d 个" % (a["origin"], a["rotation"], len(a["vertices"])))
print(u"  B origin=%s rotation=%s  顶点 %d 个" % (b["origin"], b["rotation"], len(b["vertices"])))
va = list(a["vertices"].values())
vb = list(b["vertices"].values())

for order in ("XYZ", "ZYX"):
    wa = world(va, a["origin"], a["rotation"], order)
    wb = world(vb, b["origin"], b["rotation"], order)
    ma = sorted((round(p[0], 4), round(p[1], 4), round(-p[2], 4)) for p in wa)
    mb = sorted((round(p[0], 4), round(p[1], 4), round(p[2], 4)) for p in wb)
    err = sum(max(abs(x - y) for x, y in zip(p, q)) for p, q in zip(ma, mb))
    print(u"\n顺序 %s：镜像后逐点误差合计 = %.6f" % (order, err))
    for p, q in zip(ma, mb):
        d3 = max(abs(x - y) for x, y in zip(p, q))
        print(u"    %-28s vs %-28s  最大分量差 %.4f" % (p, q, d3))
