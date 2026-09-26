# -*- coding: utf-8 -*-
u"""_zf139_unprobe.py —— 摘掉 ZF139 的探针（§10：探针不许跟着提交上车）

三件事：
  ① 把 `src\\main\\java\\com\\potatost\\mod\\Zf139Check.java` **先抄进**
     `build\\zftools\\check\\Zf139Check.java`（留档，探针报告才是可复核的）**再从 src 删掉**；
  ② 从 `PotatoST.java` 里删掉那三行（注释 + `Zf139Check.register();` + 一个空行）；
  ③ **自证互逆**：摘完之后的 `PotatoST.java` 必须与改前件**逐字节相同**。

⚠ 第 ③ 步是 ZF127 那一跤换来的（§4.108）：那次挂载吃掉了构造器前面一个空行，
   卸载时怎么都回不到原样，最后只能手工补。本轮挂载插的是一行独立的 `register()`，
   卸载按"整块删"来做，并且**用改前件当判据**而不是靠肉眼。

跑法：
    python build\\zftools\\_zf139_unprobe.py
    python build\\zftools\\_zf139_unprobe.py --keep-src   # 只抄不删（调试用）
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
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
CHECK = os.path.join(ROOT, r"build\zftools\check")
PRE = os.path.join(r"C:\PotatoST救援", "zf139_pre")
JAVA = os.path.join(SRC, u"Zf139Check.java")
POT = os.path.join(SRC, u"PotatoST.java")

BLOCK = (u"\n        // ⚠⚠ 临时探针（ZF139）：振金套加强的端到端取证，"
         u"跑完由 _zf139_unprobe.py 删掉\n        Zf139Check.register();\n")

fails, notes = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    keep = u"--keep-src" in argv

    # ---- ① 留档 ----
    if os.path.exists(JAVA):
        os.makedirs(CHECK, exist_ok=True)
        shutil.copy2(JAVA, os.path.join(CHECK, u"Zf139Check.java"))
        if sha1(JAVA) != sha1(os.path.join(CHECK, u"Zf139Check.java")):
            fails.append(u"留档哈希不一致")
        else:
            notes.append(u"  [留档] build/zftools/check/Zf139Check.java（与源逐字节相同）")
        if not keep:
            os.remove(JAVA)
            notes.append(u"  [删除] src/main/java/com/potatost/mod/Zf139Check.java")
    else:
        notes.append(u"  [已做过] 源里没有 Zf139Check.java")

    # ---- ② 摘挂载 ----
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf139Check" in text:
        if text.count(BLOCK) != 1:
            fails.append(u"PotatoST.java 里那段挂载块命中 %d 次（应为 1）" % text.count(BLOCK))
        else:
            io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(text.replace(BLOCK, u"", 1))
            notes.append(u"  [摘除] PotatoST.java 的那三行")
    else:
        notes.append(u"  [已做过] PotatoST.java 里没有 Zf139Check")

    # ---- ③ 自证互逆 ----
    pre_pot = os.path.join(PRE, r"src\main\java\com\potatost\mod\PotatoST.java")
    if not os.path.exists(pre_pot):
        fails.append(u"改前件里没有 PotatoST.java，没法自证（%s）" % pre_pot)
    elif sha1(POT) != sha1(pre_pot):
        now = io.open(POT, encoding=u"utf-8", newline=u"").read().split(u"\n")
        old = io.open(pre_pot, encoding=u"utf-8", newline=u"").read().split(u"\n")
        diff = [u"+ %s" % l for l in now if l not in old][:4] + \
               [u"- %s" % l for l in old if l not in now][:4]
        fails.append(u"摘完之后与改前件**不是**逐字节相同 ⇒ 卸载不是严格互逆。差异：%s"
                     % u" ／ ".join(diff))
    else:
        notes.append(u"  [自证] 摘完之后 PotatoST.java 与改前件逐字节相同（挂载/卸载严格互逆）")

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
