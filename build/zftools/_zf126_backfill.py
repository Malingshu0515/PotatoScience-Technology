# -*- coding: utf-8 -*-
u"""_zf126_backfill.py —— 给 `zf126_pre` 补 4 份语言文件（**事后补账**，附证据）

**为什么会漏**：`_zf126_backup.py` 的清单里没有四份 lang —— 因为本轮**一个语言键都不加/不改**
（能量条用的是共享键 `gui.potato_s_t.energy`），我当时判断"不会碰它们所以不用抄"。
但 `_zf126_verify.py` 的 C5 要拿"改前件键集合"跟今天比 —— 没有改前件那条就红。
按本工程的老口径（§10 / zf114_pre._补说明.txt 的先例）：**补账 + 留证据**，而不是把判据改松。

证据（两条，都是"改前是什么"的权威来源）：
  ① `git status --short -- <四份>` 必须**空**（相对 HEAD 未改动）；
  ② 盘上 sha1 == `git rev-parse HEAD:<path>` 取出的 blob 的 sha1。

跑法：
    python build\\zftools\\_zf126_backfill.py
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
REL = [u"src/main/resources/assets/potato_s_t/lang/%s.json" % l
       for l in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")]

notes, fails = [], []


def sha1_bytes(b):
    return hashlib.sha1(b).hexdigest()


def git(*args):
    r = subprocess.run([GIT] + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return r.returncode, r.stdout


def main():
    lines = []
    for rel in REL:
        rc, out = git(u"status", u"--short", u"--", rel)
        clean = (rc == 0 and out.decode(u"utf-8", u"replace").strip() == u"")
        rc2, blob = git(u"show", u"HEAD:" + rel)
        disk = open(os.path.join(ROOT, rel.replace(u"/", os.sep)), "rb").read()
        # ② 盘上字节 == `git show HEAD:<path>` 那个 blob 的字节（直接比 sha1，不绕 rev-parse）
        same_as_head = (rc2 == 0 and sha1_bytes(blob) == sha1_bytes(disk))
        if not (clean and same_as_head):
            fails.append(u"%s：不是「相对 HEAD 未改」（clean=%s head=%s）—— 不许补账"
                         % (rel, clean, same_as_head))
            continue
        dst = os.path.join(BK, rel.replace(u"/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel.replace(u"/", os.sep)), dst)
        ok = sha1_bytes(open(dst, "rb").read()) == sha1_bytes(disk)
        if not ok:
            fails.append(u"%s：补进去的与盘上不一致" % rel)
            continue
        lines.append(u"%s  %s  （== HEAD 的 blob，且工作区未改）" % (sha1_bytes(disk), rel))
    if not fails:
        io.open(os.path.join(BK, u"_补说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
            u"ZF126 补账：四份语言文件（备份脚本清单里漏了它们）\n"
            u"时间：见文件时间戳；脚本：build/zftools/_zf126_backfill.py\n\n"
            u"为什么漏：本轮一个语言键都没加没改（能量条用共享键 gui.potato_s_t.energy），\n"
            u"         建备份时判断「不会碰」就没抄；后来 _zf126_verify.py 的 C5 要用它 ⇒ 补账。\n\n"
            u"证据（逐份）：\n  " + u"\n  ".join(lines) + u"\n")
        notes.append(u"补进 4 份语言改前件（每份都核过：工作区未改 + sha1 == HEAD 的 blob）")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
