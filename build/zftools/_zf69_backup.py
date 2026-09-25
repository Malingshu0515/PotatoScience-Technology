# -*- coding: utf-8 -*-
"""_zf69_backup.py —— ZF69 改前件（散热装置配方：加热装置围一圈青金石）

⚠ §10：**在动第一个字节之前**抄一份并核哈希。
本轮改的是「配方生成器表 + 档案」，配方 JSON 由生成器重写，
所以把 recipe/ 下**全部** JSON 都留档 —— 重跑生成器后要拿它们证明
「除新增的那一份，其余文件一个字节都没动」（ZF47 的复现性论证）。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf69_pre"

FILES = [
    r"build\zftools\_zf45_recipes.py",
    r"docs\开发档案.md",
    # 旧成品（本轮出新品后作废，留档以便回滚）
    r"release\PotatoST-0.10.jar",
    r"release\PotatoST-0.10.jar.sha1",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def recipe_files():
    d = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
    return [os.path.join(r"src\main\resources\data\potato_s_t\recipe", n)
            for n in sorted(os.listdir(d)) if n.endswith(".json")]


def main():
    files = FILES + recipe_files()
    print(u"本轮改前件 %d 个（其中配方 JSON %d 份）" % (len(files), len(files) - len(FILES)))
    for rel in files:
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
        print(u"  [%s] %-72s %s  %d B" % (u"OK" if ok else u"FAIL", rel, a[:12], os.path.getsize(dst)))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(files), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
