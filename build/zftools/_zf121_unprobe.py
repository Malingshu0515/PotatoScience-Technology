# -*- coding: utf-8 -*-
u"""_zf121_unprobe.py —— 跑完把探针卸干净（ZF121）

四步：① 先抄存档到 `check/Zf121Check.java`；② 摘掉 `PotatoST` 里那一行钩子；
③ 删 src 里的探针；④ 逐字节证明 `PotatoST.java` 回到**预期状态**。

⚠ 这里的"预期状态"不是改前件原样：ZF121 本来就改了 `PotatoST.java` 一行注释（㉗ 那条）。
   所以判据是「改前件 + ZF121 那一处补丁」—— 由 `_zf121_java.py` 的 N3 定义，脚本里重新算一遍。

跑法：
    python build\\zftools\\_zf121_unprobe.py
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
SRC = os.path.join(JAVA, "Zf121Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf121Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf121_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"        Zf121Check.register();   // ← 临时探针（ZF121），跑完删\n"

OLD_LINE = u"        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物）\n"
NEW_LINE = (u"        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物；"
            u"ZF121 起消耗槽也能手放）\n")

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
    elif u"Zf121Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf121Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf121Check.java")

    after = io.open(MAIN, encoding="utf-8").read()
    if u"Zf121Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf121Check")
    if os.path.exists(SRC):
        fails.append(u"探针源文件还在 src")
    if not os.path.exists(ARCH):
        fails.append(u"存档不在 check/")

    # ---- ④ 与「改前件 + ZF121 那一处补丁」逐字节比 ----
    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    else:
        want = io.open(BK, encoding="utf-8").read().replace(OLD_LINE, NEW_LINE, 1)
        cur = io.open(MAIN, encoding="utf-8").read()
        ok = hashlib.sha1(cur.encode("utf-8")).hexdigest() \
            == hashlib.sha1(want.encode("utf-8")).hexdigest()
        notes.append(u"④ PotatoST.java == 改前件 + ㉗ 注释那一处补丁：%s（%s）"
                     % (u"是" if ok else u"不是", sha(MAIN)[:16]))
        if not ok:
            diff = difflib.unified_diff(want.split(u"\n"), cur.split(u"\n"),
                                        u"预期", u"现在", lineterm=u"", n=1)
            for l in list(diff)[:30]:
                print(u"  " + l[:150])
            fails.append(u"PotatoST.java 没有回到预期状态")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
