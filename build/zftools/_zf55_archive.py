# -*- coding: utf-8 -*-
"""_zf55_archive.py —— ZF55 归档：改前件已在 zf55_pre\\ 根下，这里补"本阶段新增 + 成品"

§10 归档规矩：改前件（4 java + 4 lang）在 `zf55_pre\\` 根下按原目录结构存着；
本阶段**新产生的**东西（探针源码、六个脚本、探针/反证/门日志、成品 jar + sha1）
统一进 `zf55_pre\\新增文件\\`，并写一份 MANIFEST.txt（带 SHA1，可核对）。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf55_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 探针源码（已从 src 删掉，只留档；⚠ 这份是**事后重建**的，见 MANIFEST）
    u"build\\zftools\\check\\AlloyShellCheck.java",
    # 本阶段的脚本
    u"build\\zftools\\_zf55_backup.py",
    u"build\\zftools\\_zf55_verify.py",
    u"build\\zftools\\_zf55_gates.ps1",
    u"build\\zftools\\_zf55_gatesum.py",
    u"build\\zftools\\_zf55_publish.py",
    u"build\\zftools\\_zf55_docs.py",
    u"build\\zftools\\_zf55_archive.py",
    # 证据日志
    u"build\\zftools\\_zf55_probe.txt",
    u"build\\zftools\\_zf55_probe_rebuild.log",
    u"build\\zftools\\_zf55_\u53cd\u8bc1.txt",
    u"build\\zftools\\_zf55_gates_summary.txt",
    u"build\\zftools\\_zf55_verify.log",
    # 成品
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
        u"ZF55 归档清单（新增文件 + 成品）\n"
        u"说明：改前件在 zf55_pre\\ 根下（4 个 java + 4 个 lang，按原目录结构）。\n"
        u"成品 release\\PotatoST-0.10.jar 的 SHA1 见其 .sha1 文件；本轮作废上一版 1438234a…。\n"
        u"\n"
        u"⚠ 一笔失误：收尾时先把探针从 src 删了、忘了先抄一份到 build/zftools/check/。\n"
        u"   这里那份 check\\AlloyShellCheck.java 是**事后按归档日志逐条重建**的；\n"
        u"   重建版重跑过一次，[AS] 52 行与原日志（_zf55_probe.txt）**逐字一致** ⇒ 行为等价。\n"
        u"   规矩（已写进 §4.32）：探针先抄进 check\\，再从 src 删。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
