# -*- coding: utf-8 -*-
"""_zf150_audit_del.py —— **复查** ZF135 删掉的 4 个文件是否真有等价副本（只读）

删之前我的判据是"内容 sha1 完全相同"（`_zf135_dedupe.py`）。这里**独立复算一遍**，
因为这是撤销不掉的唯一依据：

  对 `zf135_pre/` 里那 4 个被删的文件，逐个算 sha1，
  去**整个工程**里找**同 sha1** 的活文件；找不到就是真丢了。

顺带把 `_zf141_verify.py` / `_zf89_verify.py` / `_zf90_verify.py` 崩掉时
**实际打开的那个路径**也复现出来（从它们的表里拼），看它现在在不在。
"""
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
PRE = os.path.join(ROOT, r"build\zftools\zf135_pre")
USERART = os.path.join(ROOT, r"build\用户素材")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


print(u"== ① 被删的 4 个：现在工程里还有没有同 sha1 的活文件 ==")
# 建全工程 sha1 索引（只扫资源目录 + 用户素材，够用且快）
index = {}
for base in (os.path.join(ROOT, r"src\main\resources"), USERART):
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                index.setdefault(sha1(p), []).append(p)
            except Exception:
                pass

for f in sorted(os.listdir(PRE)):
    p = os.path.join(PRE, f)
    if not os.path.isfile(p):
        continue
    h = sha1(p)
    hits = index.get(h, [])
    tag = u"✅ 有等价副本" if hits else u"❌ 只剩备份"
    print(u"  %-22s %s" % (f, tag))
    for x in hits[:4]:
        print(u"        %s" % (x.replace(ROOT + os.sep, u"")))

print(u"\n== ② 崩掉那 3 份门**实际打开**的路径，现在在不在 ==")
CHECKS = [
    ("_zf141_verify.py", u"星璨钢剑", None),
    ("_zf89_verify.py", u"gasoline", None),
    ("_zf90_verify.py", u"diesel", None),
]
for fn, hint, _ in CHECKS:
    p = os.path.join(ROOT, "build", "zftools", fn)
    t = io.open(p, encoding="utf-8").read()
    print(u"\n  --- %s（含 %s 的行）---" % (fn, hint))
    for i, ln in enumerate(t.split(u"\n"), 1):
        if hint in ln and (u"USER" in ln or u"用户素材" in ln or u".png" in ln):
            print(u"    %4d: %s" % (i, ln.strip()[:110]))

print(u"\n== ③ 用户素材目录现在的完整清单（找线索）==")
for f in sorted(os.listdir(USERART)):
    if os.path.isfile(os.path.join(USERART, f)):
        print(u"  %-42s %d B" % (f, os.path.getsize(os.path.join(USERART, f))))
