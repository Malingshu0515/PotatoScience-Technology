# -*- coding: utf-8 -*-
"""_zf55_backup.py —— ZF55（合金炉判定改成"外壳成型制"）改前备份

§10 备份规矩：动第一个字节之前先把要改的文件抄一份、核对哈希。
ZF55 改的是"判定 + 文案"，与本轮之前的 ZF49~ZF54 是不同的一批文件改动，
所以单开一个 zf55_pre 目录，不去蹭 zf49_pre。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf55_pre"

FILES = [
    r"src\main\java\com\potatost\mod\AlloySmelterStructure.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlock.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
    r"src\main\java\com\potatost\mod\AlloySmelterPortBlock.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % src)
            continue
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-72s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))

    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
