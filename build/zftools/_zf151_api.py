# -*- coding: utf-8 -*-
u"""_zf151_api.py —— ZF151 侦察②：`requiresCorrectToolForDrops` 到底卡在哪一步。

要点：它是不是**真的**卡住"掉落"（而不是只影响"能不能采"）——
这决定了"空手挖也掉落"要不要去掉那两个接线口上的这个标志。
"""
import io
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
SRC = r"E:\PotatoST\.gradle\repositories\ng_dummy_ng\net\neoforged\neoforge\21.1.235\neoforge-21.1.235-sources.jar"

z = zipfile.ZipFile(SRC)
names = [n for n in z.namelist() if n.endswith(u".java")]
print(u"======== 谁调用 canHarvestBlock / isCorrectToolForDrops ========")
for n in names:
    txt = z.read(n).decode(u"utf-8", u"replace")
    if u"canHarvestBlock" in txt or u"isCorrectToolForDrops" in txt:
        for i, ln in enumerate(txt.split(u"\n")):
            if u"canHarvestBlock" in ln or u"isCorrectToolForDrops" in ln:
                s = ln.strip()
                if s.startswith(u"//") or s.startswith(u"*"):
                    continue
                print(u"  %-46s %5d | %s" % (n.split(u"/")[-1], i + 1, s[:120]))

print(u"")
print(u"======== BlockBehaviour 里这两处定义 ========")
txt = z.read(u"net/minecraft/world/level/block/state/BlockBehaviour.java").decode(u"utf-8", u"replace")
lines = txt.split(u"\n")
for i, ln in enumerate(lines):
    if u"requiresCorrectToolForDrops" in ln and (u"public " in ln or u"protected " in ln):
        for j in range(max(0, i - 14), min(len(lines), i + 3)):
            print(u"  %5d | %s" % (j + 1, lines[j].rstrip()[:140]))
        print(u"  ---")
z.close()
