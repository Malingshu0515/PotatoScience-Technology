# -*- coding: utf-8 -*-
"""_zf66_backup.py —— ZF66 改前件（钛合金剑 / 钛合金镐）

⚠ 这一轮**在动第一个字节之前**就抄（ZF65 那次忘了、只能事后反向重建，见 §10）。
两张用户给的贴图也各留一份原名副本（下一步要改名成 ASCII）。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf66_pre"

FILES = [
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    # 用户给的两张工具贴图（原名留档，下一步改名成 ASCII）
    r"src\main\resources\assets\potato_s_t\textures\item\钛合金剑_001.png",
    r"src\main\resources\assets\potato_s_t\textures\item\钛合金镐_001.png",
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
        print(u"  [%s] %-62s %s  %d B" % (u"OK" if ok else u"FAIL", rel, a[:12], os.path.getsize(dst)))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
