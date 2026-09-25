# -*- coding: utf-8 -*-
u"""_zf74_backup.py —— ZF74 改前件（给流体挂 c: 通用标签 + 让气体判定认标签）

§10：动手前先抄一份并核哈希。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf74_pre"

FILES = [
    r"src\main\java\com\potatost\mod\ModFluids.java",
    r"docs\开发档案.md",
    r"docs\v0.11规划.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf72_verify.py",
    r"build\zftools\_zf72_vanilla_evidence.py",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    print(u"本轮改前件 %d 个" % len(FILES))
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        if os.path.isfile(dst):
            a, b = sha1(src), sha1(dst)
            print(u"  [%s] %-52s 改前件已在，不覆盖" % (u"SKIP" if a == b else u"KEEP", rel))
            continue
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-52s %s  %d B" % (u"OK" if ok else u"FAIL", rel, a[:12],
                                          os.path.getsize(dst)))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
