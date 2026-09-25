# -*- coding: utf-8 -*-
u"""_zf81_backfill.py —— 补一份 PotatoST.java 进 zf81_pre（**事后补记**，照 ZF33 先例）

实情：本轮 zf81_pre 收 17 份时**漏了 `PotatoST.java`**，而它后来被加了探针挂钩（又摘掉了）。
现在补一份进去，并在 `_说明.txt` 里写清楚这一份是**事后**抄的、依据是什么：
  · 与 `zf80_pre` 的那一份**逐字节相同**（SHA1 6777bcfa…）⇒ 挂钩确实摘干净了、
    内容与本轮动手前一致（ZF80 之后没有任何东西再动过这个文件）。
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
REL = r"src\main\java\com\potatost\mod\PotatoST.java"
CUR = os.path.join(ROOT, REL)
REF = os.path.join(r"C:\PotatoST救援\zf80_pre", REL)
BK = r"C:\PotatoST救援\zf81_pre"
DST = os.path.join(BK, REL)

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


cur = sha1(CUR)
ref = sha1(REF) if os.path.exists(REF) else None
print(u"当前 PotatoST.java        = %s" % cur)
print(u"zf80_pre 里的同一份（基准） = %s" % ref)
if ref is None:
    fails.append(u"没有基准可比（zf80_pre 里缺 PotatoST.java）")
elif cur != ref:
    fails.append(u"与基准不同 ⇒ 不能当「改前件」补，先查清楚")
else:
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    shutil.copy2(CUR, DST)
    if sha1(DST) != cur:
        fails.append(u"拷贝后哈希不一致")
    else:
        print(u"[OK] 已补进 zf81_pre（逐字节相同）")

note = os.path.join(BK, u"_说明.txt")
io.open(note, "w", encoding="utf-8", newline=u"\n").write(
    u"""ZF81 备份说明（含一处事后补记）

① 17 份改前件是**动手前**抄的，清单见 `_sha1.txt`。

② `src\\main\\java\\com\\potatost\\mod\\PotatoST.java` 这一份是**事后补记**（照 ZF33 先例）：
   本轮动手前漏抄了它，而它随后被加了 ZF81 探针挂钩、又摘掉了。
   补记依据：它与 `zf80_pre` 里的同一份**逐字节相同**（SHA1 %s），
   即"挂钩摘干净了、内容与本轮动手前一致"（ZF80 之后没有别的东西动过它）。
""" % cur)

print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
