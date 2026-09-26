# -*- coding: utf-8 -*-
u"""_zf127_mount.py —— 把探针挂到 `PotatoST` 构造器末尾（ZF127）

`PotatoST.java` 是 **LF**（`.gitattributes` 是 `* -text`）⇒ 按它自己的换行插。

跑法：
    python build\\zftools\\_zf127_mount.py
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MAIN = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"
ANCHOR = u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onPlayerLogin);\n\n    }\n"
HOOK = u"        Zf127Check.register();   // ← 临时探针（ZF127），跑完删\n"
fails, notes = [], []


def main():
    text = io.open(MAIN, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    if u"Zf127Check" in text:
        notes.append(u"已经挂过（幂等跳过）")
    else:
        a = ANCHOR.replace(u"\n", nl)
        if text.count(a) != 1:
            fails.append(u"锚点命中 %d 次（要 1 次）—— 停手" % text.count(a))
        else:
            new = a.replace(u"\n" + u"    }" + u"\n",
                            nl + HOOK.replace(u"\n", nl) + u"    }" + nl)
            io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(a, new, 1))
            notes.append(u"挂上 %s" % HOOK.strip())
    back = io.open(MAIN, encoding="utf-8", newline=u"").read()
    if u"Zf127Check.register();" not in back:
        fails.append(u"挂完看不到钩子")
    if back.count(u"Zf127Check") != 1:
        fails.append(u"Zf127Check 出现 %d 次（要 1 次）" % back.count(u"Zf127Check"))
    notes.append(u"PotatoST.java sha1 = %s" % hashlib.sha1(open(MAIN, "rb").read()).hexdigest()[:16])
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
