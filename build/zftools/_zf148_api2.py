# -*- coding: utf-8 -*-
u"""_zf148_api2.py —— ZF148 侦察⑨：专服上能不能读到创造栏内容 / 帕秋莉靠什么进物品栏。

① `CreativeModeTabs.tryRebuildTabContents` 在哪被调（专服启动时会建吗）；
② 帕秋莉 jar 里有没有 `BuildCreativeModeTabContentsEvent`（它就是靠这个把书塞进我们的物品栏的）。
"""
import io
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
SRC = r"E:\PotatoST\.gradle\repositories\ng_dummy_ng\net\neoforged\neoforge\21.1.235\neoforge-21.1.235-sources.jar"
PJ = r"E:\PotatoST\libs\Patchouli-1.21.1-93-NEOFORGE.jar"

z = zipfile.ZipFile(SRC)
names = z.namelist()
print(u"======== 谁调用 tryRebuildTabContents ========")
for n in names:
    if not n.endswith(u".java"):
        continue
    txt = z.read(n).decode(u"utf-8", u"replace")
    if u"tryRebuildTabContents" in txt:
        for i, ln in enumerate(txt.split(u"\n")):
            if u"tryRebuildTabContents" in ln:
                print(u"  %-64s %5d: %s" % (n.split(u"/")[-1], i + 1, ln.strip()))
z.close()

print(u"")
print(u"======== 帕秋莉里和创造栏有关的东西 ========")
z = zipfile.ZipFile(PJ)
for n in z.namelist():
    if not n.endswith(u".class"):
        continue
    raw = z.read(n)
    if b"CreativeModeTab" in raw or b"BuildCreativeModeTabContents" in raw:
        hits = []
        for nd in (b"BuildCreativeModeTabContents", b"CreativeModeTab", b"creativeTab",
                   b"accept", b"getDisplayItems"):
            if nd in raw:
                hits.append(nd.decode(u"ascii"))
        print(u"  %-78s %s" % (n, hits))
z.close()
