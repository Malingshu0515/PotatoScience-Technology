# -*- coding: utf-8 -*-
r"""_zf94_knife.py —— 给反证找**唯一**锚点：北向 OBJ 里"第二根柱子的东面"那条 `f` 行

背景：ZF94 之后两根柱子的东/西用的是**同一个 UV 矩形** ⇒ 那些 `vt` 行的文本**重复出现**，
`_zf78_falsify.py` 要求锚点命中**正好 1 次** ⇒ 不能拿 `vt` 行当锚点。
`f` 行每条都是唯一的，所以改"某个顶点指向哪个 vt"就能把那一面的 UV 改坏。

用法:
    python _zf94_knife.py
"""
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OBJ = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"
# ⚠ 第一版这张表写错了（把 −Z 当成"东"）—— 那张表必须与 `_zf94_verify.py` 的 BACK 一致。
#   数据来源：北向 OBJ 里两根柱子（面组 1/2）的六面实测 —— 金框在 −Z（结构正面）、
#   深灰在 +Z（背面）、格栅在 ±X。写错只会让**打印的标签**不对（锚点照旧按 `f` 行取）。
BACK = {(0, 0, -1): u"南", (0, 0, 1): u"北", (-1, 0, 0): u"东", (1, 0, 0): u"西"}


def main():
    lines = open(OBJ, "rb").read().decode("utf-8").splitlines()
    vs, vts, faces = [], [], []
    for i, raw in enumerate(lines):
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "vt":
            vts.append(tuple(float(x) for x in t[1:3]))
        elif t[0] == "f":
            faces.append((i, [(int(a.split("/")[0]) - 1, int(a.split("/")[1]) - 1) for a in t[1:]]))
    # 第二根柱子 = 面组 2（每 6 面一组，文件顺序 = 工程 elements 顺序）
    for n, (lineno, f) in enumerate(faces):
        if n // 6 != 2:
            continue
        a, b, c = vs[f[0][0]], vs[f[1][0]], vs[f[2][0]]
        u1 = [b[i] - a[i] for i in range(3)]
        u2 = [c[i] - a[i] for i in range(3)]
        nrm = (u1[1] * u2[2] - u1[2] * u2[1], u1[2] * u2[0] - u1[0] * u2[2], u1[0] * u2[1] - u1[1] * u2[0])
        ln = math.sqrt(sum(q * q for q in nrm)) or 1.0
        nrm = tuple(round(q / ln, 4) for q in nrm)
        lab = BACK.get((int(nrm[0]), int(nrm[1]), int(nrm[2])), u"?")
        us = [vts[t][0] for _, t in f]
        vv = [vts[t][1] for _, t in f]
        rect = (round(min(us) * 256), round(min(vv) * 256),
                round((max(us) - min(us)) * 256), round((max(vv) - min(vv)) * 256))
        print(u"第 %4d 行  面组#2 %-3s 法线 %s  矩形 %s" % (lineno + 1, lab, nrm, rect))
        print(u"           %s" % lines[lineno])
    return 0


if __name__ == "__main__":
    sys.exit(main())
