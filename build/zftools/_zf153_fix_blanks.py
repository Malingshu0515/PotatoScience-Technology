# -*- coding: utf-8 -*-
u"""_zf153_fix_blanks.py —— 把别人挂/摘探针留下的**多余空行**修掉（只动空白，别的一律不碰）

背景：另一条线在 14:13 挂着探针做反证、14:18 摘掉，`PotatoST.java` 里因此多出两行空行
（他们的挂载/摘除是"插 4 行、删 4 行"，中间的空白没对齐）。我的两处监听**完好**。

判据（只认这一种改动，且必须**正好一处**）：
    构造器收尾前应当是 `…onPlayerTick(event.getEntity()));\n\n    }`，
    现在多了两个空行 ⇒ 改回三个换行。
改完与"功能改完、探针未挂"基准（`check\\zf153_PotatoST_noprobe.java`）**逐字节相同**才算过。

跑法：python build\\zftools\\_zf153_fix_blanks.py
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
MAIN = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
BASE = os.path.join(ROOT, r"build\zftools\check\zf153_PotatoST_noprobe.java")

OLD = u")));\n\n\n\n    }\n"
NEW = u")));\n\n    }\n"


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


t = io.open(MAIN, encoding="utf-8").read()
n = t.count(OLD)
print(u"锚点（连续三个空行 + 收尾括号）出现 %d 次" % n)
if n == 1:
    io.open(MAIN, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    print(u"  [OK] 已修掉多余空行")
elif u")));\n\n    }\n" in t and n == 0:
    print(u"  [幂等] 没有多余空行")
else:
    print(u"  [STOP] 锚点异常，不动它（先看清是谁改的）")
    sys.exit(1)

base = io.open(BASE, encoding="utf-8").read()
now = io.open(MAIN, encoding="utf-8").read()
same = now == base
print(u"  [%s] 与基准逐字节相同（sha1 %s）" % (u"OK" if same else u"!!", sha(MAIN)))
if not same:
    import difflib
    for line in list(difflib.unified_diff(base.split(u"\n"), now.split(u"\n"),
                                          u"基准", u"现在", lineterm=u""))[:16]:
        print(u"      " + line)
sys.exit(0 if same else 1)
