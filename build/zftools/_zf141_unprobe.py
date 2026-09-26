# -*- coding: utf-8 -*-
r'''_zf141_unprobe.py —— 摘掉 ZF141 的探针（§10：探针不许跟着提交上车）

四件事：
  ① 把 `src\main\java\com\potatost\mod\Zf141Check.java` **先抄进**
     `build\zftools\check\Zf141Check.java`（留档 —— 探针报告才是可复核的）**再从 src 删掉**；
  ② ⚠ **自检「归档物与产物自洽」**（§4.145，本轮新立的规矩）：归档件的
     **TAG / 类名 / 报告路径** 必须与报告文件里**实际出现**的 TAG 对得上 ——
     上一轮（ZF139）就是因为中途改过轮号，归档的是 `Zf138Check`、报告却是 `[A139]`，
     两边对不上而没人发现。这里当场断言，不一致就报错（**不自动改文件**）。
  ③ 从 `PotatoST.java` 里删掉那两行（注释 + `Zf141Check.register();`，含前导换行）；
  ④ **自证互逆**：摘完之后 `PotatoST.java` 必须与改前件（`zf141_pre`）**逐字节相同**。

跑法：
    python build\zftools\_zf141_unprobe.py
    python build\zftools\_zf141_unprobe.py --keep-src   # 只抄不删（调试用）
'''
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
PRE = os.path.join(r"C:\PotatoST救援", "zf141_pre")
JAVA = os.path.join(SRC, u"Zf141Check.java")
POT = os.path.join(SRC, u"PotatoST.java")
REPORT = os.path.join(ROOT, r"build\zftools\_zf141_probe_utf8.txt")

BLOCK = (u"\n        // ⚠⚠ 临时探针（ZF141）：星璨钢工具补齐的端到端取证，"
         u"跑完由 _zf141_unprobe.py 删掉\n        Zf141Check.register();")

TAG = u"[A141] "
CLASS = u"public final class Zf141Check"
REPORT_NAME = u"_zf141_probe_utf8.txt"

fails, notes = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    keep = u"--keep-src" in argv

    # ---- ① 留档 ----
    if os.path.exists(JAVA):
        os.makedirs(CHECK, exist_ok=True)
        shutil.copy2(JAVA, os.path.join(CHECK, u"Zf141Check.java"))
        if sha1(JAVA) != sha1(os.path.join(CHECK, u"Zf141Check.java")):
            fails.append(u"留档哈希不一致")
        else:
            notes.append(u"  [留档] build/zftools/check/Zf141Check.java（与源逐字节相同）")
        if not keep:
            os.remove(JAVA)
            notes.append(u"  [删除] src/main/java/com/potatost/mod/Zf141Check.java")
    else:
        notes.append(u"  [已做过] 源里没有 Zf141Check.java")

    # ---- ② 归档物与产物自洽（§4.145）----
    arc = os.path.join(CHECK, u"Zf141Check.java")
    if not os.path.isfile(arc):
        fails.append(u"归档件不在，没法自洽检查：%s" % arc)
    else:
        a = io.open(arc, encoding="utf-8").read()
        if TAG not in a:
            fails.append(u"归档件里没有 TAG %r" % TAG)
        if CLASS not in a:
            fails.append(u"归档件里没有 %r" % CLASS)
        if REPORT_NAME not in a:
            fails.append(u"归档件的报告路径不是 %s" % REPORT_NAME)
        if not os.path.isfile(REPORT):
            fails.append(u"报告不在：%s" % REPORT)
        else:
            rep = io.open(REPORT, encoding="utf-8").read()
            if TAG not in rep:
                fails.append(u"报告里没有 TAG %r ⇒ 归档件与报告**不是同一版**（§4.145）" % TAG)
            else:
                notes.append(u"  [自洽] 归档件的 TAG / 类名 / 报告路径与报告里的 %r 对得上" % TAG)

    # ---- ③ 摘挂载 ----
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf141Check" in text:
        if text.count(BLOCK) != 1:
            fails.append(u"PotatoST.java 里那段挂载块命中 %d 次（应为 1）" % text.count(BLOCK))
        else:
            io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(text.replace(BLOCK, u"", 1))
            notes.append(u"  [摘除] PotatoST.java 的那两行")
    else:
        notes.append(u"  [已做过] PotatoST.java 里没有 Zf141Check")

    # ---- ④ 自证互逆 ----
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
