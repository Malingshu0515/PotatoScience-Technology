# -*- coding: utf-8 -*-
u"""_zf128_unprobe.py —— 跑完把探针卸干净（ZF128）

四步：① **先抄存档**到 `check/Zf128Check.java`；② 删掉 `PotatoST` 里那一行钩子（**只删那一行**）；
③ 删 src 里的探针；④ 逐字节证明 `PotatoST.java` 回到改前件原样。

⚠ 这次的挂载/卸载是**严格互逆**的（ZF127 吃过"挂载吃掉一个空行"的亏，§4.108）：
  挂载脚本自己就断言过"删掉那一行 == 改前件"。

跑法：
    python build\\zftools\\_zf128_unprobe.py
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
SRC = os.path.join(JAVA, "Zf128Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf128Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf128_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"        Zf128Check.register();   // ← 临时探针（ZF128），跑完删\n"

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
    if hook in text:
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(hook, u"", 1))
        notes.append(u"② 删掉那一行钩子（只删那一行 —— 空行原样保留）")
    elif u"Zf128Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf128Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf128Check.java")

    after = io.open(MAIN, encoding="utf-8", newline=u"").read()
    if u"Zf128Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf128Check")
    if os.path.exists(SRC):
        fails.append(u"探针源文件还在 src")
    if not os.path.exists(ARCH):
        fails.append(u"存档不在 check/")

    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    elif sha(BK) == sha(MAIN):
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
