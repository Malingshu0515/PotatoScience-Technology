# -*- coding: utf-8 -*-
u"""_zf107_unprobe.py —— 跑完把探针卸干净（ZF107）

两步：① 删 `Zf107Check.java`；② 从 `PotatoST.java` 里删掉那一行挂载。
然后**逐字节**证明 `PotatoST.java` 回到了改前件的样子（本轮的探针挂载是本轮**唯一**
碰过它的改动 ⇒ 卸掉之后必须与 `zf107_pre` 那份完全一致）。不一致就报 FAIL，绝不"看着差不多"。
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf107Check.java")
MAIN = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
BK = r"C:\PotatoST救援\zf107_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"\n\n        Zf107Check.register();   // ← 临时探针（ZF107），跑完删"

fails = []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(PROBE):
        os.remove(PROBE)
        print(u"  删掉探针源文件 Zf107Check.java")
    elif u"Zf107Check" in io.open(MAIN, encoding="utf-8").read():
        fails.append(u"探针源文件不见了，但 PotatoST 里还挂着它")

    text = io.open(MAIN, encoding="utf-8").read()
    if HOOK in text:
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(HOOK, u"", 1))
        print(u"  摘掉 PotatoST 里那一行挂载")
    elif u"Zf107Check" not in text:
        print(u"  PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf107Check，但找不到那一行的原样文本 —— 别再瞎删")

    after = io.open(MAIN, encoding="utf-8").read()
    if u"Zf107Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf107Check")
    if os.path.exists(PROBE):
        fails.append(u"探针源文件还在")
    # 逐字节回到改前
    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    else:
        ok = sha(MAIN) == sha(BK)
        print(u"  PotatoST.java 与改前件逐字节一致：%s（%s）" % (u"是" if ok else u"不是", sha(MAIN)[:16]))
        if not ok:
            cur = io.open(MAIN, encoding="utf-8").read().split(u"\n")
            old = io.open(BK, encoding="utf-8").read().split(u"\n")
            import difflib
            diff = [l for l in difflib.unified_diff(old, cur, u"改前", u"现在", lineterm=u"", n=1)]
            print(u"  ---- 差异 %d 行 ----" % len(diff))
            for l in diff[:40]:
                print(u"  " + l[:150])
            fails.append(u"PotatoST.java 没有回到改前状态")
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
