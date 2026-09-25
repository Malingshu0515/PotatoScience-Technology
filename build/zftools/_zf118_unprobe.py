# -*- coding: utf-8 -*-
r"""_zf118_unprobe.py —— 跑完把探针卸干净（ZF118）

四步：① **先抄**存档到 `build\zftools\check\Zf118Check.java`（§10.1：先抄后删）；
② 从 `PotatoST.java` 里删掉挂载那一行；③ 删 `src` 里的探针源文件；
④ **逐字节**证明 `PotatoST.java` 回到 `zf118_pre` 那份
（这次改前件里**有**它 —— ZF117 漏过一次，本轮挂钩子前就先抄了）。
"""
import difflib
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
SRC = os.path.join(JAVA, "Zf118Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf118Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf118_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"\n        Zf118Check.register();   // ← 临时探针（ZF118），跑完删"

fails, notes = [], []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(SRC):
        shutil.copy2(SRC, ARCH)
        if sha(SRC) != sha(ARCH):
            fails.append(u"存档哈希不一致")
        else:
            notes.append(u"① 存档 %s（%d B，sha1 %s）" % (ARCH, os.path.getsize(ARCH), sha(ARCH)))
    else:
        notes.append(u"① src 里已经没有探针源文件（可能已经卸过）")

    text = io.open(MAIN, encoding="utf-8").read()
    if HOOK in text:
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(HOOK, u"", 1))
        notes.append(u"② 摘掉 PotatoST 里那一行挂载")
    elif u"Zf118Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf118Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf118Check.java")

    after = io.open(MAIN, encoding="utf-8").read()
    if u"Zf118Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf118Check")
    if os.path.exists(SRC):
        fails.append(u"探针源文件还在 src")
    if not os.path.exists(ARCH):
        fails.append(u"存档不在 check/")

    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    else:
        ok = sha(MAIN) == sha(BK)
        notes.append(u"④ PotatoST.java 与改前件逐字节一致：%s（%s）"
                     % (u"是" if ok else u"不是", sha(MAIN)[:16]))
        if not ok:
            cur = io.open(MAIN, encoding="utf-8").read().split(u"\n")
            old = io.open(BK, encoding="utf-8").read().split(u"\n")
            diff = [l for l in difflib.unified_diff(old, cur, u"改前", u"现在", lineterm=u"", n=1)]
            for l in diff[:30]:
                print(u"  " + l[:150])
            fails.append(u"PotatoST.java 没有回到改前状态")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
