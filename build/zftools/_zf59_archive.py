# -*- coding: utf-8 -*-
"""_zf59_archive.py —— ZF59 归档（改前件在 zf59_pre\\ 根下，这里补新增 + 成品）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf59_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"build\\zftools\\check\\AlloyLayoutCheck.java",
    u"build\\zftools\\check\\AlloyLayoutCheck_zf59.java",
    u"build\\zftools\\_zf59_backup.py",
    u"build\\zftools\\_zf59_publish.py",
    u"build\\zftools\\_zf59_docs.py",
    u"build\\zftools\\_zf59_archive.py",
    u"build\\zftools\\_zf59_probe.txt",
    u"build\\zftools\\zf59_falsify.txt",
    u"build\\zftools\\_zf59_gates_summary.txt",
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
        u"ZF59 归档清单（新增文件 + 成品）\n"
        u"主题：等第四层摆完再成型 —— 判定把顶面那 10 格也纳入（要查 48 → 58）。\n"
        u"改前件在 zf59_pre\\ 根下（8 个：结构 java + 4 lang + _zf57_lang/_zf55_verify/_zf57_verify）。\n"
        u"成品 release\\PotatoST-0.10.jar SHA1 见其 .sha1；本轮作废上一版 9c917dad…。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
