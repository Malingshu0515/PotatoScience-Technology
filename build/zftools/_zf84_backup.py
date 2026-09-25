# -*- coding: utf-8 -*-
u"""_zf84_backup.py —— ZF84 **动手前**的改前件（§10：第一个字节改动之前先抄；这次记着了）

本轮：用户给了一张新图（「汽油的新贴图」）⇒ 换 `textures/block/gasoline_still.png`
与 `gasoline_flow.png`（两张本来逐字节相同，ZF78 的约定是同一张图兼作 still/flow）。
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf84_pre"
FILES = [
    r"src\main\resources\assets\potato_s_t\textures\block\gasoline_still.png",
    r"src\main\resources\assets\potato_s_t\textures\block\gasoline_flow.png",
    r"docs\贴图清单.md",
    r"docs\开发档案.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s" % BK)
    lines = []
    ok = 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
            print(u"  [OK]   %s（%s…）" % (rel, after[:8]))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"\n改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
