# -*- coding: utf-8 -*-
u"""_zf91_knifecheck.py —— 上线前自检：ZF91 那几把刀的锚点必须**正好命中一次**。只读。"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
CHECKS = [
    (u"K33 北向 OBJ 的一个 vt 值", os.path.join(MB, "electric_blast_furnace_north.obj"),
     u"vt 0.378906 0.000000"),
    (u"K34 档案 §5 的 ZF91 行", os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF91 | **新建 `zf91_pre`**"),
    (u"K35 model JSON 的 flip_v 行", os.path.join(MB, "electric_blast_furnace_north.json"),
     u'"flip_v": false'),
    # K28 在 ZF91 里改了锚点（原来砍"只有 4 个 UV 点"，现在砍"删掉一条面"）——一并自检
    (u"K28 北向 OBJ 的第一条面", os.path.join(MB, "electric_blast_furnace_north.obj"),
     u"usemtl electric_blast_furnace\nf 2/1/1 1/2/1 3/3/1 4/4/1\n"),
]
fails = []
for label, p, anchor in CHECKS:
    if not os.path.exists(p):
        fails.append(u"%s：文件不在 %s" % (label, p))
        continue
    t = io.open(p, encoding="utf-8", errors="replace").read()
    n = t.count(anchor)
    print(u"  %-26s 命中 %d 次  %s" % (label, n, u"OK" if n == 1 else u"!! 必须正好 1 次"))
    if n != 1:
        fails.append(u"%s：命中 %d 次" % (label, n))
print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
