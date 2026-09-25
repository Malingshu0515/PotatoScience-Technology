# -*- coding: utf-8 -*-
"""_zf63_archive.py —— ZF63 归档"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf63_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"build\\zftools\\check\\AlloyRecipeCheck.java",
    u"build\\zftools\\_zf63_backup.py",
    u"build\\zftools\\_zf63_publish.py",
    u"build\\zftools\\_zf63_docs.py",
    u"build\\zftools\\_zf63_archive.py",
    u"build\\zftools\\_zf63_probe_utf8.txt",
    u"build\\zftools\\zf63_falsify.txt",
    u"build\\zftools\\_zf63_gates_utf8.txt",
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
        u"ZF63 归档清单\n"
        u"主题：合金炉配方耗电 5800 → 800 FE/t（用户「行吧改成800 2的话就一次做一份吧」）。\n"
        u"一件总耗电 348 万 → 48 万 FE；并行保持「一次一份」。\n"
        u"成品 SHA1 见 release\\PotatoST-0.10.jar.sha1；本轮作废 ZF62 的 d62a8e42…。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
