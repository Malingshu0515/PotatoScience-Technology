# -*- coding: utf-8 -*-
"""_zf64_backup.py —— ZF64（JEI 说明行删除 / 合金炉进度箭头 / 运行时循环音效）改前备份"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf64_pre"

FILES = [
    r"src\main\java\com\potatost\mod\MachineRecipes.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
    r"src\main\java\com\potatost\mod\AlloySmelterMenu.java",
    r"src\main\java\com\potatost\mod\client\AlloySmelterScreen.java",
    r"src\main\java\com\potatost\mod\sound\ModSounds.java",
    r"src\main\resources\assets\potato_s_t\sounds.json",
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
        print(u"  [%s] %-62s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))
    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
