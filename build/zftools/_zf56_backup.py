# -*- coding: utf-8 -*-
"""_zf56_backup.py —— ZF56（模型跟成型状态走）改前备份

用户原话：「不是主控变成4x5x4是合金炉！合金炉成型后模型！」
⇒ 改 `AlloySmelterBlock`（加 formed 方块状态）、`AlloySmelterBlockEntity`（成型时切状态）、
  `blockstates/alloy_smelter.json`（两种变体），另加 ZF54 那个校验脚本要跟着改。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf56_pre"

FILES = [
    r"src\main\java\com\potatost\mod\AlloySmelterBlock.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
    r"src\main\resources\assets\potato_s_t\blockstates\alloy_smelter.json",
    r"build\zftools\_zf54_verify.py",
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
        print(u"  [%s] %-70s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))

    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
