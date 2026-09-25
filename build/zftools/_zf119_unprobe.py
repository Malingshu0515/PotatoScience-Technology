# -*- coding: utf-8 -*-
r"""_zf119_unprobe.py —— 跑完把探针卸干净（ZF119）

⚠ `PotatoST.java` 本轮**漏进了** `_zf119_backup.py` 的常规清单（ZF117 之后**第二次**栽在这里）
   ⇒ 现在按 `zf119_pre\\_补说明.txt` 走事后补账（等级 ①：git blob，与盘上逐字节相同）。

四步：① 先抄存档到 `check/Zf119Check.java`；② 摘掉钩子；③ 删 src 里的探针；
④ 逐字节证明 `PotatoST.java` 回到改前件（那一份是补进去的，见 `_补说明.txt`）。
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
SRC = os.path.join(JAVA, "Zf119Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf119Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf119_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"\n        Zf119Check.register();   // ← 临时探针（ZF119），跑完删"

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
    elif u"Zf119Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf119Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf119Check.java")

    after = io.open(MAIN, encoding="utf-8").read()
    if u"Zf119Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf119Check")
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
            for l in list(difflib.unified_diff(old, cur, u"改前", u"现在", lineterm=u"", n=1))[:30]:
                print(u"  " + l[:150])
            fails.append(u"PotatoST.java 没有回到改前状态")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
