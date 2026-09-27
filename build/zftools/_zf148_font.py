# -*- coding: utf-8 -*-
u"""_zf148_font.py —— ZF148 侦察④：原版 uniform 字体里到底有没有 CJK 回退。

帕秋莉的书默认把正文换成 `minecraft:uniform`（Book.UNIFORM_FONT）。
如果那个字体定义里没有 unifont / 中日韩 provider，中文就会掉字 ⇒ 得开 book.json 的
`use_blocky_font`。这里直接翻客户端 jar 里的 font/uniform.json 定论。
"""
import glob
import io
import os
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOTS = [
    r"C:\Users\Administrator\.gradle\caches\modules-2\files-2.1",
    r"E:\PotatoST\.gradle",
    r"E:\PotatoST\.gradle.old_0913_044943",
]

cands = []
for root in ROOTS:
    if not os.path.isdir(root):
        continue
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(u".jar"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) < 8 * 1024 * 1024:
                    continue
            except OSError:
                continue
            cands.append(p)
print(u"候选大 jar = %d 个" % len(cands))

done = False
for p in cands:
    try:
        z = zipfile.ZipFile(p)
    except Exception:
        continue
    hit = [n for n in z.namelist() if n.endswith(u"font/uniform.json")]
    if hit:
        print(u"命中：%s" % p)
        print(u"---- %s ----" % hit[0])
        print(z.read(hit[0]).decode(u"utf-8", u"replace"))
        for extra in (u"font/default.json", u"font/include/unifont.json"):
            h2 = [n for n in z.namelist() if n.endswith(extra)]
            for x in h2:
                print(u"---- %s ----" % x)
                print(z.read(x).decode(u"utf-8", u"replace")[:1200])
        done = True
        break
    z.close()

if not done:
    print(u"没找到带 font/uniform.json 的 jar（候选里都没有）")
