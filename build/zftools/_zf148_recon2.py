# -*- coding: utf-8 -*-
u"""_zf148_recon2.py —— ZF148 侦察②：组件 id / 物品模型机制 / 分类与条目加载路径。

只读。输出 UTF-8。
"""
import io, os, re, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
JAR = r"E:\PotatoST\libs\Patchouli-1.21.1-93-NEOFORGE.jar"
z = zipfile.ZipFile(JAR)


def strings(cls):
    raw = z.read(cls)
    return [m.group().decode(u"ascii") for m in re.finditer(rb"[ -~]{4,}", raw)]


def pr(s=u""):
    print(s)


pr(u"================ ① PatchouliDataComponents 里的常量串 ================")
for s in strings(u"vazkii/patchouli/common/item/PatchouliDataComponents.class"):
    pr(u"  " + s)

pr()
pr(u"================ ② 谁在用 ItemProperties / overrides（物品模型机制） ================")
for n in z.namelist():
    if not n.endswith(u".class"):
        continue
    raw = z.read(n)
    if b"ItemProperties" in raw or b"getModel" in raw or b"overrides" in raw:
        hits = []
        for nd in (b"ItemProperties", b"getModel", b"overrides", b"model"):
            if nd in raw:
                hits.append(nd.decode(u"ascii"))
        pr(u"  %-78s %s" % (n, hits))

pr()
pr(u"================ ③ client/book 加载器里的路径模板串 ================")
for cls in (u"vazkii/patchouli/client/book/BookContentsBuilder.class",
            u"vazkii/patchouli/client/book/BookContentResourceDirectLoader.class",
            u"vazkii/patchouli/client/book/BookContentResourceListenerLoader.class",
            u"vazkii/patchouli/common/book/BookFolderLoader.class",
            u"vazkii/patchouli/common/book/BookRegistry.class"):
    pr(u"---- %s ----" % cls)
    for s in strings(cls):
        if (u"patchouli_books" in s or u".json" in s or u"entries" in s or u"categories" in s
                or u"templates" in s or u"assets" in s or u"data" in s or u"%s" in s):
            pr(u"    " + s)

pr()
pr(u"================ ④ 页面类型注册名（patchouli:*） ================")
names = set()
for n in z.namelist():
    if u"/page/" in n and n.endswith(u".class") and u"$" not in n:
        names.add(n.split(u"/")[-1][:-6])
pr(u"  " + u", ".join(sorted(names)))

pr()
pr(u"================ ⑤ Book 类字段（书名/模型/版本等键的落地） ================")
raw = z.read(u"vazkii/patchouli/common/book/Book.class")
pr(u"  " + u" | ".join(s for s in strings(u"vazkii/patchouli/common/book/Book.class")
                      if len(s) < 40)[:3000])

z.close()
