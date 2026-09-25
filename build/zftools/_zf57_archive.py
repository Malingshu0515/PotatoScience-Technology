# -*- coding: utf-8 -*-
"""_zf57_archive.py —— ZF57 归档（改前件在 zf57_pre\\ 根下，这里补新增 + 成品）

规矩：探针先抄进 build/zftools/check/，再从 src 删（这次从一开头就这么做了）。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf57_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"build\\zftools\\check\\AlloyLayoutCheck.java",
    u"build\\zftools\\_zf57_backup.py",
    u"build\\zftools\\_zf57_verify.py",
    u"build\\zftools\\_zf57_verify.txt",
    u"build\\zftools\\_zf57_lang.py",
    u"build\\zftools\\_zf57_gates.ps1",
    u"build\\zftools\\_zf57_gates_summary.txt",
    u"build\\zftools\\_zf57_publish.py",
    u"build\\zftools\\_zf57_docs.py",
    u"build\\zftools\\_zf57_archive.py",
    u"build\\zftools\\_zf57_probe.txt",
    u"build\\zftools\\zf57_falsify.txt",
    u"release\\PotatoST-0.10.jar",
    u"release\\PotatoST-0.10.jar.sha1",
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails = []
    rows = []
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(NEW, rel)
        if not os.path.isfile(src):
            fails.append(u"缺文件: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        if a != b:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        rows.append(u"%-70s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF57 归档清单（新增文件 + 成品）\n"
        u"主题：合金炉换用户重画的新图纸（主控改到最前排最右列 ⇒ 顺带定位了历史「激活不了」的根因）。\n"
        u"改前件在 zf57_pre\\ 根下（7 个：AlloySmelterStructure + 4 lang + _zf52/_zf55 两个校验脚本）。\n"
        u"成品 release\\PotatoST-0.10.jar SHA1 见其 .sha1；本轮作废上一版 b0c86fcd…。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
