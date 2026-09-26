# -*- coding: utf-8 -*-
u"""_zf126_backfill2.py —— 给 `zf126_pre` 补 `PotatoST.java`（**第二次补账**，附证据）

**为什么又漏**：探针要往 `PotatoST` 构造器末尾挂一行 `Zf126Check.register();`，
而 `_zf126_backup.py` 的清单里**没有它** —— 这是本工程**第三次**犯同一个错
（ZF117、ZF119 都记过；档案 §9 里那两轮的"补说明"就是前两次）。

**补法（等级①证据：改前是什么由提交回答）**：
  ① 现在盘上的 `PotatoST.java` **已经卸掉钩子**（`_zf126_unprobe.py` 跑过）；
  ② 它的字节 == `git show HEAD:<path>` 那个 blob 的字节（HEAD 就是 ZF125 那次提交）；
  ⇒ 所以"直接把现在这份抄进改前件"与"抄一份真正的改前件"是同一个东西，且**可验证**。

跑法：
    python build\\zftools\\_zf126_backfill2.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
BK = r"C:\PotatoST救援\zf126_pre"
REL = u"src/main/java/com/potatost/mod/PotatoST.java"

notes, fails = [], []


def sha1_bytes(b):
    return hashlib.sha1(b).hexdigest()


def git(*args):
    r = subprocess.run([GIT] + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return r.returncode, r.stdout


def main():
    path = os.path.join(ROOT, REL.replace(u"/", os.sep))
    disk = open(path, "rb").read()
    rc, blob = git(u"show", u"HEAD:" + REL)
    rc2, st = git(u"status", u"--short", u"--", REL)
    if rc != 0:
        fails.append(u"git show HEAD:%s 失败" % REL)
    elif sha1_bytes(blob) != sha1_bytes(disk):
        fails.append(u"盘上这份 != HEAD 的 blob（%s / %s）—— 说明钩子还没卸干净或后来又改过，不许补账"
                     % (sha1_bytes(blob)[:12], sha1_bytes(disk)[:12]))
    elif u"Zf126Check" in disk.decode(u"utf-8"):
        fails.append(u"盘上这份里还有 Zf126Check —— 先把钩子卸干净")
    else:
        dst = os.path.join(BK, REL.replace(u"/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(path, dst)
        if sha1_bytes(open(dst, "rb").read()) != sha1_bytes(disk):
            fails.append(u"补进改前件的字节与盘上不一致")
        else:
            notes.append(u"补进 %s（sha1 %s == HEAD 的 blob；工作区对该路径无改动：%s）"
                         % (REL, sha1_bytes(disk)[:16], st.decode(u"utf-8", u"replace").strip() or u"是"))
            with io.open(os.path.join(BK, u"_补说明2.txt"), "w", encoding="utf-8",
                         newline=u"\n") as f:
                f.write(u"ZF126 第二次补账：PotatoST.java（探针挂载点）\n"
                        u"脚本：build/zftools/_zf126_backfill2.py\n\n"
                        u"为什么漏：探针要往它的构造器末尾挂 Zf126Check.register()，\n"
                        u"         而 _zf126_backup.py 的清单里没有它（本工程第三次犯，见 ZF117/ZF119）。\n\n"
                        u"证据：现在盘上这份**已经卸掉钩子**，其字节 == git HEAD 的 blob\n"
                        u"      ⇒ 它就是改前件，可逐字节复算（sha1 %s）。\n" % sha1_bytes(disk))
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
