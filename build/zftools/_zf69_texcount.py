# -*- coding: utf-8 -*-
"""_zf69_texcount.py —— 数一数 textures/ 下还剩几张贴图不是 16×16（老占位色块）

档案 §9 里写死过「23 张老占位色块是 160×160」。ZF69 这轮用户自己换掉了
光伏原件那张（160×160 → 16×16）⇒ 这个数字必须跟着改，否则文档就是在骗人。
这里独立数一遍（只读文件头，不靠 TextureCheck 的输出）。
"""
import importlib.util
import io
import os
import struct
import sys

ROOT = r"E:\PotatoST"
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures")

fails = []
rows = []
total = 0

for dirpath, dirnames, filenames in os.walk(TEX):
    for fn in sorted(filenames):
        if not fn.lower().endswith(".png"):
            continue
        total += 1
        p = os.path.join(dirpath, fn)
        data = io.open(p, "rb").read()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            fails.append(u"不是真 PNG: %s" % p)
            continue
        w, h = struct.unpack(">II", data[16:24])
        rel = os.path.relpath(p, TEX).replace("\\", "/")
        if (w, h) != (16, 16):
            rows.append((rel, w, h))

print(u"贴图总数 = %d" % total)
print(u"不是 16x16 的 = %d" % len(rows))
groups = {}
for rel, w, h in rows:
    groups.setdefault((w, h), []).append(rel)
for k in sorted(groups, key=lambda k: -len(groups[k])):
    print(u"    %-12s %d 张" % (u"%dx%d" % k, len(groups[k])))
    if k != (160, 160):
        for rel in groups[k]:
            print(u"          " + rel)
print(u"其中 160x160 的老占位色块 = %d" % len(groups.get((160, 160), [])))
for rel in groups.get((160, 160), []):
    print(u"          " + rel)
print(u"不是真 PNG 的 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
