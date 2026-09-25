# -*- coding: utf-8 -*-
"""_zf62_archive.py —— ZF62 归档（改前件在 zf62_pre\\ 根下，这里补新增 + 成品）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf62_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"src\\main\\java\\com\\potatost\\mod\\AlloySmelterRecipes.java",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\item\\light_titanium_alloy.json",
    u"build\\zftools\\check\\AlloyRecipeCheck.java",
    u"build\\zftools\\_zf62_backup.py",
    u"build\\zftools\\_zf62_lang.py",
    u"build\\zftools\\_zf62_lang2.py",
    u"build\\zftools\\_zf62_gates.ps1",
    u"build\\zftools\\_zf62_gates_utf8.txt",
    u"build\\zftools\\_zf62_publish.py",
    u"build\\zftools\\_zf62_docs.py",
    u"build\\zftools\\_zf62_archive.py",
    u"build\\zftools\\_zf62_probe_utf8.txt",
    u"build\\zftools\\zf62_falsify.txt",
    u"build\\zftools\\zf62_falsify2.txt",
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
        rows.append(u"%-74s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF62 归档清单（新增文件 + 成品）\n"
        u"主题：合金冶炼炉的第一条配方 —— 铝锭+钛锭+银锭 → 1 轻质钛合金，30s、5800 FE/t（一件 348 万 FE）。\n"
        u"改前件在 zf62_pre\\ 根下（5 个）。成品 SHA1 见 release\\PotatoST-0.10.jar.sha1；作废上一版 2eda8966…。\n"
        u"探针 AlloyRecipeCheck.java 已按规矩先抄进 check\\ 再删 src。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
