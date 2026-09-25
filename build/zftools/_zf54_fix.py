# -*- coding: utf-8 -*-
"""_zf54_fix.py —— 删掉 ZF49 留下的旧版 findMaster（与新加的 3 参数版重名，编译报"已定义"）。"""
import io
import re

P = r"E:\PotatoST\src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java"
t = io.open(P, encoding="utf-8").read()
old = re.search(r"\n    /\*\* 找控制器：给接线口用（它自己不存数据，每次现找）。 \*/\n"
                r"    public static AlloySmelterBlockEntity findMaster\(Level level, BlockPos portPos\) \{.*?\n    \}\n",
                t, re.S)
if not old:
    print(u"没找到旧方法（可能已经删过）")
else:
    t = t[:old.start()] + u"\n" + t[old.end():]
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    print(u"已删除旧版 findMaster（%d 字符）" % (old.end() - old.start()))
    print(u"还剩几处 findMaster 定义：%d" % len(re.findall(r"static AlloySmelterBlockEntity findMaster", t)))
