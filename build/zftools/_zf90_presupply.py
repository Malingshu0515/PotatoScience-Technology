# -*- coding: utf-8 -*-
u"""_zf90_presupply.py —— 给 zf90_pre 补一份改前件：`TextureCheck.py`（照 ZF78/ZF83/ZF89 先例）

为什么补：本轮后半段发现 `TextureCheck.py --plan` 有两个真问题（清单表把「模型名」当成贴图名、
整份覆盖会冲掉手写小节），要改它 —— 而它不在最初那份快照里。**必须在动它之前**补进来。

做法：从盘上拷进快照，逐个核 sha1；再写一份 `_补说明.txt` 说明来源与原因。
⚠ 不要重跑 `_zf90_backup.py`（它现在会在根已存在时直接中止，正是为了防"把改后状态覆盖进快照"）。
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
BK = r"C:\PotatoST救援\zf90_pre"
FILES = [r"build\zftools\TextureCheck.py"]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    lines = [u"zf90_pre 补账说明（§10）", u"",
             u"一、为什么补：本轮要改 `build/zftools/TextureCheck.py`（清单表把「模型名」当贴图名 +",
             u"    整份覆盖会冲掉手写小节），它不在最初那份 9→13 份快照里 ⇒ 动它之前先抄一份。", u"",
             u"二、来源：改前的盘上原文（拷贝后逐份核 sha1）。", u""]
    ok = 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
            print(u"  [OK]   %s  %s…（%d 字节）" % (rel, after[:8], os.path.getsize(dst)))
    io.open(os.path.join(BK, u"_补说明.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"补账 %d 份 → %s\\_补说明.txt" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
