# -*- coding: utf-8 -*-
u"""_zf127_unprobe.py —— 跑完把探针卸干净（ZF127）

四步：① **先抄存档**到 `check/Zf127Check.java`；② 摘掉 `PotatoST` 里那一行钩子（连它前面那个空行）；
③ 删 src 里的探针；④ 逐字节证明 `PotatoST.java` 回到改前件原样（§10.1：先抄再从 src 删）。

跑法：
    python build\\zftools\\_zf127_unprobe.py
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
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
SRC = os.path.join(JAVA, "Zf127Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf127Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf127_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"        Zf127Check.register();   // ← 临时探针（ZF127），跑完删\n"

fails, notes = [], []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(SRC):
        shutil.copy2(SRC, ARCH)
        if sha(SRC) != sha(ARCH):
            fails.append(u"存档哈希不一致")
        else:
            notes.append(u"① 存档 %s（%d B，sha1 %s）" % (ARCH, os.path.getsize(ARCH), sha(ARCH)[:16]))
    else:
        notes.append(u"① src 里已经没有探针源文件（可能已经卸过）")

    text = io.open(MAIN, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    hook = HOOK.replace(u"\n", nl)
    hook_pad = nl + hook
    if hook_pad in text:
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(hook_pad, u"", 1))
        notes.append(u"② 摘掉钩子（连它前面那个空行一起）")
    elif u"Zf127Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf127Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf127Check.java")

    after = io.open(MAIN, encoding="utf-8", newline=u"").read()
    if u"Zf127Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf127Check")
    if os.path.exists(SRC):
        fails.append(u"探针源文件还在 src")
    if not os.path.exists(ARCH):
        fails.append(u"存档不在 check/")

    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    else:
        if sha(BK) == sha(MAIN):
            notes.append(u"④ PotatoST.java == 改前件（逐字节，sha1 %s）" % sha(MAIN)[:16])
        else:
            fails.append(u"PotatoST.java 没有回到改前件（改前 %s / 现在 %s）"
                         % (sha(BK)[:16], sha(MAIN)[:16]))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
