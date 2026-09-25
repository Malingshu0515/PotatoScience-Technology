# -*- coding: utf-8 -*-
"""_zf60_backup.py —— ZF60（用户给的 7 张贴图：磁铁/铁粉/钛矿/深层钛矿/粗钛/钛粉/钛锭）改前备份

会动的文件：
  · 2 张**已有占位贴图**（magnet / iron_powder）—— 会被覆盖
  · 5 个物品 + 2 个方块模型 —— 现在借用原版铁/火药贴图，要改成指向自己的贴图
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf60_pre"
TEX_ITEM = r"src\main\resources\assets\potato_s_t\textures\item"
MOD_ITEM = r"src\main\resources\assets\potato_s_t\models\item"
MOD_BLOCK = r"src\main\resources\assets\potato_s_t\models\block"

FILES = [
    TEX_ITEM + r"\magnet.png",
    TEX_ITEM + r"\iron_powder.png",
    MOD_ITEM + r"\magnet.json",
    MOD_ITEM + r"\iron_powder.json",
    MOD_ITEM + r"\raw_titanium.json",
    MOD_ITEM + r"\titanium_powder.json",
    MOD_ITEM + r"\titanium_ingot.json",
    MOD_BLOCK + r"\titanium_ore.json",
    MOD_BLOCK + r"\deepslate_titanium_ore.json",
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
        print(u"  [%s] %-58s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))

    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
