# -*- coding: utf-8 -*-
u"""_zf72_backup.py —— ZF72 改前件（v0.11 石油线「规划轮」：只写文档）

§10：动手前先抄一份并核哈希。

【本轮换了备份根】上一轮的根
    C:\\Users\\Administrator\\Desktop\\PotatoST救援_20260917_183054
已经在 2026-09-19 13:36 被删进回收站（424,191,790 B，`$R` 实体仍在 ⇒ 可还原，见
`_zf72_recycle_list.py` 的输出）。桌面会被清，所以新根挪到 C 盘、不进桌面：
    C:\\PotatoST救援\\zf72_pre

本轮**不动 jar**（只加一份 docs 文档 + 改档案），旧成品 `84d09345…` 继续有效、**不作废**。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf72_pre"

FILES = [
    r"docs\开发档案.md",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    print(u"本轮改前件 %d 个" % len(FILES))
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        # 幂等保护：改前件**一旦落下就不许被覆盖**。
        # 本轮之后的任何时候再跑一次这个脚本，源文件已经被编辑过 ——
        # 若照抄一遍，改前件就被改后内容顶掉了（这正是备份事故的经典形态）。
        if os.path.isfile(dst):
            a, b = sha1(src), sha1(dst)
            if a == b:
                print(u"  [SKIP] %-40s 已存在且与源相同（幂等重跑，不覆盖）" % rel)
            else:
                print(u"  [KEEP] %-40s 已存在且与源**不同** ⇒ 保留改前件、不覆盖（源已被编辑过）"
                      % rel)
                print(u"         改前件 %s / 当前源 %s" % (b[:12], a[:12]))
            continue
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-40s %s  %d B" % (u"OK" if ok else u"FAIL", rel, a[:12], os.path.getsize(dst)))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
