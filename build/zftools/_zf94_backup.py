# -*- coding: utf-8 -*-
u"""_zf94_backup.py —— ZF94 **动手前**的改前件（§10）

本轮：用户说「**3. 电力高炉 接线方块还是对称一致一下吧**」——
上一轮（ZF92）我在汇报里点名过「两根柱子的**东/西面仍然不一样**（一根是格栅、一根是素板）」，
他现在要它们一致。

会动到的：四份 `electric_blast_furnace_*.obj`（只动 `vt`）、两份文档、`_zf78_falsify.py`、
旧成品 jar 与 `.sha1`。另把 ZF92 那份"补丁工程"与用户原件留档，方便复现。
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
BK = r"C:\PotatoST救援\zf94_pre"
MB = r"src\main\resources\assets\potato_s_t\models\block"
FILES = [
    MB + r"\electric_blast_furnace_north.obj",
    MB + r"\electric_blast_furnace_south.obj",
    MB + r"\electric_blast_furnace_east.obj",
    MB + r"\electric_blast_furnace_west.obj",
    MB + r"\electric_blast_furnace.mtl",
    r"build\zftools\_zf92_fix_uv.py",
    r"build\zftools\_zf92_ebf_fixed.bbmodel",
    r"build\zftools\_zf92_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s（重跑会覆盖改前件，直接中止）" % BK)
        return 1
    lines, ok = [], 0
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
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
