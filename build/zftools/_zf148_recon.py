# -*- coding: utf-8 -*-
u"""_zf148_recon.py —— ZF148 侦察①：帕秋莉 jar 内部结构 / 书路径规则 / 组件名 / 自带 mod 元数据。

只读，不写工程任何文件。输出走 stdout（UTF-8）。
"""
import io, os, re, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

JAR = r"E:\PotatoST\libs\Patchouli-1.21.1-93-NEOFORGE.jar"
NEEDLES = [b"patchouli_books", b"assets/%s/patchouli_books", b"data/%s/patchouli_books",
           b"book.json", b"categories", b"entries"]


def pr(s=u""):
    print(s)


z = zipfile.ZipFile(JAR)
names = z.namelist()

pr(u"================ ① 顶层与 data/assets 树 ================")
tops = sorted(set(n.split(u"/")[0] for n in names))
pr(u"顶层：" + u", ".join(tops))
for top in (u"data", u"assets"):
    prefix = top + u"/"
    sub = sorted(set(n[len(prefix):].split(u"/")[0] for n in names if n.startswith(prefix)))
    pr(u"%s/ 下一层（%d）：%s" % (top, len(sub), u", ".join(sub)))

pr()
pr(u"================ ② book 包里的类 ================")
for n in sorted(x for x in names if x.startswith(u"vazkii/patchouli/common/book/")):
    pr(u"  " + n)

pr()
pr(u"================ ③ 类文件里的路径字符串（哪些类提到 patchouli_books） ================")
hits = {}
for n in names:
    if not n.endswith(u".class"):
        continue
    raw = z.read(n)
    found = [nd.decode(u"ascii") for nd in NEEDLES[:1] if nd in raw]
    if found:
        hits[n] = found
for n in sorted(hits):
    pr(u"  %s  -> %s" % (n, hits[n]))
pr(u"  合计 %d 个类提到 patchouli_books" % len(hits))

pr()
pr(u"================ ④ 路径拼接模板（含 %s / .json 的常量串） ================")
tmpl = set()
for n in names:
    if not n.endswith(u".class"):
        continue
    for m in re.finditer(rb"[ -~]{4,}", z.read(n)):
        s = m.group().decode(u"ascii")
        if (u"patchouli_books" in s or u"book.json" in s or (u"%s" in s and u"book" in s.lower())):
            tmpl.add((n, s))
for n, s in sorted(tmpl):
    pr(u"  %-72s | %s" % (n.split(u"/")[-1], s))
pr(u"  合计 %d 条" % len(tmpl))

pr()
pr(u"================ ⑤ 帕秋莉自己的 mods.toml ================")
for cand in (u"META-INF/neoforge.mods.toml", u"META-INF/mods.toml"):
    if cand in names:
        pr(u"---- %s ----" % cand)
        pr(z.read(cand).decode(u"utf-8", u"replace"))

pr()
pr(u"================ ⑥ 自带资源里和 book 沾边的 ================")
for n in sorted(x for x in names if u"book" in x.lower() and not x.endswith(u".class")):
    pr(u"  " + n)

z.close()
