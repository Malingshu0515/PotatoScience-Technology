# -*- coding: utf-8 -*-
"""_zf57_backup.py —— ZF57（合金炉换新图纸）改前备份

用户这一版图纸（逐字）：
  图例：耐热金属块=1 一般金属块=2 加热装置=3 高炉=4（接线块/散热装置/合金炉主控 写全名，【】=空）
  第1层 2222 / 2332 / 2332 / 2332 / 2222
  第2层 接线块 1 1 接线块 / 4 空空 4 ×3 / 散热装置 1 1 合金炉主控
  第3层 1111 / 1001 / 1001 / 1001 / 1111
  第4层 0110 ×4 排（只写了 4 排）
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf57_pre"

FILES = [
    r"src\main\java\com\potatost\mod\AlloySmelterStructure.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf52_verify.py",
    r"build\zftools\_zf55_verify.py",
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
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-66s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))

    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
