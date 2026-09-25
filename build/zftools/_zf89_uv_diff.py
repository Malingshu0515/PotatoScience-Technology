# -*- coding: utf-8 -*-
u"""_zf89_uv_diff.py —— 把用户原稿 model.obj（两个版本）与仓库里 4 份成品 OBJ 的 UV 摊开比

只读。回答："UV 是被我们的烘焙脚本弄丢的，还是用户原稿本来就是 0..1 满贴图？"
"""
import io
import os
import sys

FILES = [
    (u"用户原稿 A", r"C:\Users\Administrator\.dsh\attachments\v1\files\4c\4cfdb0359b91bfe97943d66fcb198fd4c80ef0d8e5f3a7a68dc7ff1789fe990a\model.obj"),
    (u"用户原稿 B", r"C:\Users\Administrator\.dsh\attachments\v1\files\7f\7fe4cd0e9bb58442f9771d72becddabbddd3c4cca44df4fbb403404e8df6dea4\model.obj"),
]
BLK = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
for n in ("north", "south", "east", "west"):
    FILES.append((u"成品 " + n, os.path.join(BLK, "electric_blast_furnace_%s.obj" % n)))


def scan(path):
    vs = vts = vns = fs = 0
    uv = set()
    head = []
    for i, raw in enumerate(io.open(path, "r", encoding="utf-8", errors="replace")):
        if i < 4:
            head.append(raw.rstrip())
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs += 1
        elif t[0] == "vt":
            vts += 1
            uv.add((float(t[1]), float(t[2])))
        elif t[0] == "vn":
            vns += 1
        elif t[0] == "f":
            fs += 1
    return vs, vts, vns, fs, uv, head


for name, path in FILES:
    if not os.path.exists(path):
        print(u"%s: 文件不在 %s" % (name, path))
        continue
    vs, vts, vns, fs, uv, head = scan(path)
    print(u"=== %s ===" % name)
    print(u"  %s  (%d 字节)" % (os.path.basename(path), os.path.getsize(path)))
    for h in head:
        print(u"  | " + h)
    print(u"  v=%d vt=%d vn=%d f=%d   不同 UV 点: %d" % (vs, vts, vns, fs, len(uv)))
    if len(uv) <= 12:
        print(u"  UV 点全表: %s" % sorted(uv))
    else:
        su = sorted(uv)
        print(u"  u 范围 %.4f..%.4f  v 范围 %.4f..%.4f" %
              (su[0][0], su[-1][0], min(p[1] for p in su), max(p[1] for p in su)))
        print(u"  前 8 个: %s ... 后 8 个: %s" % (su[:8], su[-8:]))
    print(u"")
