# -*- coding: utf-8 -*-
"""_zf56_archive.py —— ZF56 归档（改前件在 zf56_pre\\ 根下，这里补新增 + 成品 + 生成的脚本）

⚠ 这次记得了（§4.32 的规矩）：**探针先抄进 build/zftools/check/，再从 src 删** ——
   归档前先确认 check\\AlloyFormedCheck.java 存在。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf56_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"build\\zftools\\check\\AlloyFormedCheck.java",
    u"build\\zftools\\_zf56_backup.py",
    u"build\\zftools\\_zf56_verify.py",
    u"build\\zftools\\_zf56_verify.txt",
    u"build\\zftools\\_zf56_gates.ps1",
    u"build\\zftools\\_zf56_gates_summary.txt",
    u"build\\zftools\\_zf56_publish.py",
    u"build\\zftools\\_zf56_docs.py",
    u"build\\zftools\\_zf56_archive.py",
    u"build\\zftools\\_zf56_probe.txt",
    u"build\\zftools\\zf56_falsifyA.txt",
    u"build\\zftools\\zf56_falsifyB.txt",
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
        rows.append(u"%-70s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF56 归档清单（新增文件 + 成品）\n"
        u"本次主题：4×5×4 是「成型后的合金炉」，不是主控本体（主控未成型 = 物品栏那个小方块）。\n"
        u"改前件在 zf56_pre\\ 根下（4 个：两个 java + blockstate + _zf54_verify.py）。\n"
        u"成品 release\\PotatoST-0.10.jar SHA1 见其 .sha1；本轮作废上一版 0f55763d…。\n"
        u"探针 AlloyFormedCheck.java 已按规矩先抄进 check\\ 再删 src。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
