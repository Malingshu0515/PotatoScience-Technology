# -*- coding: utf-8 -*-
"""_zf60_archive.py —— ZF60 归档（改前件在 zf60_pre\\ 根下，这里补新增 + 成品 + 解码管线）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf60_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"build\\zftools\\_zf60_backup.py",
    u"build\\zftools\\_zf60_decode.ps1",
    u"build\\zftools\\_zf60_chunks.ps1",
    u"build\\zftools\\_zf60_alpha.ps1",
    u"build\\zftools\\_zf60_qcheck.py",
    u"build\\zftools\\_zf60_bg.py",
    u"build\\zftools\\_zf60_install.py",
    u"build\\zftools\\_zf60_verify.py",
    u"build\\zftools\\_zf60_verify_utf8.txt",
    u"build\\zftools\\_zf60_bg.txt",
    u"build\\zftools\\_zf60_install_utf8.txt",
    u"build\\zftools\\_zf60_gates.ps1",
    u"build\\zftools\\_zf60_gates_summary.txt",
    u"build\\zftools\\_zf60_publish.py",
    u"build\\zftools\\_zf60_docs.py",
    u"build\\zftools\\_zf60_archive.py",
    # 解码出来的成品贴图（也可从资源树取，这里留一份"落盘当时的原件"）
    u"build\\zftools\\_zf60_png\\magnet.png",
    u"build\\zftools\\_zf60_png\\iron_powder.png",
    u"build\\zftools\\_zf60_png\\titanium_ore.png",
    u"build\\zftools\\_zf60_png\\deepslate_titanium_ore.png",
    u"build\\zftools\\_zf60_png\\raw_titanium.png",
    u"build\\zftools\\_zf60_png\\titanium_powder.png",
    u"build\\zftools\\_zf60_png\\titanium_ingot.png",
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
        rows.append(u"%-72s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF60 归档清单（新增文件 + 成品）\n"
        u"主题：用户给的 7 张贴图（磁铁/铁粉/钛矿/深层钛矿/粗钛/钛粉/钛锭）。\n"
        u"⚠ 这 7 个文件扩展名是 .png，实际是 **webp 且带 alpha**；WPF 的 BitmapDecoder 会把 alpha 丢掉\n"
        u"  （透明区底下是花屏），正解是 BitmapImage + PreservePixelFormat —— 见 §4.35。\n"
        u"改前件在 zf60_pre\\ 根下（9 个：2 张占位贴图 + 5 个物品模型 + 2 个方块模型）。\n"
        u"成品 release\\PotatoST-0.10.jar SHA1 见其 .sha1；本轮作废上一版 10016a23…。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
