# -*- coding: utf-8 -*-
u"""_zf77_backup.py —— ZF77 改前件（海洋油田改到浅海近岸）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf77_pre"
FILES = [
    r"src\main\java\com\potatost\mod\SaltyRiverBiomeSource.java",
    r"src\main\resources\data\potato_s_t\worldgen\biome\ocean_oilfield.json",
    r"docs\开发档案.md",
    r"build\zftools\_zf75_verify.py",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
    r"run\server\server.properties",
]
fails = []


def sha1(p):
    h = hashlib.sha1()
    with io.open(p, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    print(u"本轮改前件 %d 个" % len(FILES))
    for rel in FILES:
        src, dst = os.path.join(PROJ, rel), os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        if os.path.isfile(dst):
            print(u"  [SKIP] %s 已在" % rel)
            continue
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        if a != b:
            fails.append(u"哈希不一致: %s" % rel)
        print(u"  [%s] %-56s %s" % (u"OK" if a == b else u"FAIL", rel, a[:12]))
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
