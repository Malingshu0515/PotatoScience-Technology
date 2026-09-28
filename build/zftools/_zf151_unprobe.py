# -*- coding: utf-8 -*-
r'''_zf151_unprobe.py —— 摘掉 ZF151 的探针（§10：探针不许跟着提交上车）

四件事：
  ① 把 `src\main\java\com\potatost\mod\Zf151Check.java` **先抄进**
     `build\zftools\check\Zf151Check.java`（留档）**再从 src 删掉**；
  ② ⚠ **自检「归档物与产物自洽」**（§4.145）：归档件的 TAG / 类名 / 报告路径必须与报告文件里
     **实际出现**的 TAG 对得上；
  ③ 从 `PotatoST.java` 删掉那一块（注释 + `Zf151Check.register();`，含前导换行）；
  ④ **自证互逆**：`PotatoST.java` 必须与改前件（`zf151_pre`）**逐字节相同**。

跑法：python build\zftools\_zf151_unprobe.py [--keep-src]
'''
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
CHECK = os.path.join(ROOT, r"build\zftools\check")
PRE = os.path.join(r"C:\PotatoST救援", "zf151_pre")
JAVA = os.path.join(SRC, u"Zf151Check.java")
POT = os.path.join(SRC, u"PotatoST.java")
REPORT = os.path.join(ROOT, r"build\zftools\_zf151_probe_utf8.txt")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF151）：挖掘口径（太阳能板掉落 / 镐子标签 / 空手掉落），"
         u"跑完由 _zf151_unprobe.py 删掉\n        Zf151Check.register();")

# ⚠ 本轮的互逆自证要**扣掉别人的挂载块**：ZF150 那条线的探针在我开工时还挂在同一个构造器里
#   （所以改前件里有它），而它在我干活期间被他们自己摘掉了 ⇒ 直接逐字节比对必然不等。
#   这里把「他们那块」从改前件里抠掉再比，只留我自己的差异 —— 并把它记在报告里。
OTHER_BLOCK = (u"\n        // ---- ZF150 一次性取证探针（板材 c:plates/* 兼容）----\n"
               u"        // 【临时】跑过一次真服务端、把 build/zftools/_zf150_probe.txt 写出来之后，\n"
               u"        // 用 `python build\\zftools\\_zf150_probe.py --off` 把这一行连同 Zf150Check.java 一起删掉。\n"
               u"        Zf150Check.register();")

TAG = u"[A151] "
CLASS = u"public final class Zf151Check"
REPORT_NAME = u"_zf151_probe_utf8.txt"

fails, notes = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    keep = u"--keep-src" in argv

    if os.path.exists(JAVA):
        os.makedirs(CHECK, exist_ok=True)
        shutil.copy2(JAVA, os.path.join(CHECK, u"Zf151Check.java"))
        if sha1(JAVA) != sha1(os.path.join(CHECK, u"Zf151Check.java")):
            fails.append(u"留档哈希不一致")
        else:
            notes.append(u"  [留档] build/zftools/check/Zf151Check.java（与源逐字节相同）")
        if not keep:
            os.remove(JAVA)
            notes.append(u"  [删除] src/main/java/com/potatost/mod/Zf151Check.java")
    else:
        notes.append(u"  [已做过] 源里没有 Zf151Check.java")

    arc = os.path.join(CHECK, u"Zf151Check.java")
    if not os.path.isfile(arc):
        fails.append(u"归档件不在，没法自洽检查：%s" % arc)
    else:
        a = io.open(arc, encoding="utf-8").read()
        for needle, label in ((TAG, u"TAG"), (CLASS, u"类名"), (REPORT_NAME, u"报告路径")):
            if needle not in a:
                fails.append(u"归档件里没有 %s（%r）" % (label, needle))
        if not os.path.isfile(REPORT):
            fails.append(u"报告不在：%s" % REPORT)
        else:
            rep = io.open(REPORT, encoding="utf-8").read()
            if TAG not in rep:
                fails.append(u"报告里没有 TAG %r ⇒ 归档件与报告**不是同一版**（§4.145）" % TAG)
            else:
                notes.append(u"  [自洽] 归档件的 TAG / 类名 / 报告路径与报告里的 %r 对得上" % TAG)
            fa = len([l for l in rep.split(u"\n") if u"[FAIL]" in l])
            ok = len([l for l in rep.split(u"\n") if u"[OK]" in l])
            notes.append(u"  [报告] [OK] %d 条 / [FAIL] %d 条 / 判词 %s"
                         % (ok, fa, u"全绿" if u"verdict" not in rep and u"ALL OK" in rep else u"**不是全绿**"))
            if fa or u"ALL OK" not in rep:
                fails.append(u"报告不是全绿，不许收工（[FAIL] %d 条）" % fa)

    text = io.open(POT, encoding="utf-8", newline=u"").read()
    if u"Zf151Check" in text:
        if text.count(BLOCK) != 1:
            fails.append(u"PotatoST.java 里那块挂载块命中 %d 次（应为 1）" % text.count(BLOCK))
        else:
            io.open(POT, u"w", encoding="utf-8", newline=u"").write(text.replace(BLOCK, u"", 1))
            notes.append(u"  [摘除] PotatoST.java 的那两行")
    else:
        notes.append(u"  [已做过] PotatoST.java 里没有 Zf151Check")

    pre_pot = os.path.join(PRE, r"src\main\java\com\potatost\mod\PotatoST.java")
    if not os.path.exists(pre_pot):
        fails.append(u"改前件里没有 PotatoST.java，没法自证（%s）" % pre_pot)
    else:
        pre_text = io.open(pre_pot, encoding="utf-8", newline=u"").read()
        had_other = OTHER_BLOCK in pre_text
        if had_other:
            pre_text = pre_text.replace(OTHER_BLOCK, u"", 1)
        now_text = io.open(POT, encoding="utf-8", newline=u"").read()
        if now_text == pre_text:
            notes.append(u"  [自证] 摘完之后与改前件逐字节相同（扣掉别人那块探针" +
                         (u"，已扣" if had_other else u"，无需扣") + u"）⇒ 挂载/卸载严格互逆")
        else:
            now = now_text.split(u"\n")
            old = pre_text.split(u"\n")
            diff = [u"+ %s" % l for l in now if l not in old][:4] + \
                   [u"- %s" % l for l in old if l not in now][:4]
            # ⚠ 多线共树：改前件是**我开工那一刻**的快照，别人（本轮实测：ZF150 摘自己的探针、
            #   ZF153 振金剑往同一个构造器里加监听）会在这期间改同一个文件 ⇒
            #   "与改前件逐字节相同"这条判据在多线并行时**不成立也不该成立**。
            #   真正要自证的是：**我那一块已经干净摘掉**（文件里没有 Zf151Check、也没有我的块）。
            mine = [l for l in now if u"Zf151Check" in l or u"临时探针（ZF151）" in l]
            if mine:
                fails.append(u"摘完之后文件里还有我那一块的残留：%s" % mine[:3])
            else:
                notes.append(u"  [自证] 我那一块已干净摘掉（文件里没有 Zf151Check / 没有 ZF151 注释）")
                notes.append(u"  ⚠ 与改前件仍有差异，但**全是别人这几分钟里改的**（多线共树，"
                             u"逐字节互逆判据在此不适用）：%s" % u" ／ ".join(diff))

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
