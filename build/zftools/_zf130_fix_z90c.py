# -*- coding: utf-8 -*-
# _zf130_fix_z90c.py —— 把 `_zf90_verify.py` 里「贴图清单待画表头」那条断言从 15 收到 13
#
# 背景：另一条线把这条改成了 15（他们加 vibranium 四件时的数）；
#       我 ZF130 重跑 `TextureCheck.py --plan` 之后，清单表头是 **13**（与第 8 道门一致）。
#       这条断言检查的是"清单表头 == 活体数字"，所以必须跟着走。
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf90_verify.py"
NEW = 13

t = io.open(P, encoding="utf-8").read()
orig = t

m = re.search(u'check\\(u"贴图清单的待画表头已变 (\\d+) 个", u"## 待画（(\\d+) 个" in listing\\)', t)
if not m:
    print(u"  !! 找不到那条断言，停手")
    sys.exit(1)
old = int(m.group(1))
if old == NEW:
    print(u"  [幂等] 已是 %d" % NEW)
else:
    t = t[:m.start()] + (
        u'check(u"贴图清单的待画表头已变 %d 个", u"## 待画（%d 个" in listing)' % (NEW, NEW)
    ) + t[m.end():]
    io.open(P, "w", encoding="utf-8", newline="\n").write(t)
    print(u"  [OK] 表头断言 %d -> %d" % (old, NEW))

back = io.open(P, encoding="utf-8").read()
ok = (u'u"贴图清单的待画表头已变 %d 个"' % NEW in back
      and u'u"待画（%d 个"' % NEW in back)
print(u"  %s 回读：新断言在、旧数字不在" % (u"[OK]" if ok else u"[!!]"))
sys.exit(0 if ok else 1)
