# -*- coding: utf-8 -*-
u"""_zf92_backup.py —— ZF92 **动手前**的改前件（§10）

本轮要改的东西：电力高炉四份 OBJ 里**那两根接线柱（1×1×1，塔的 ±X 两侧 y 1..2）
六个面的 UV 归属** —— 只动 `vt`，不动顶点、不动贴图。

改前件 = 会被这一轮动到的全部文件：
  · 四份 `electric_blast_furnace_{north,south,east,west}.obj`（要被重烘覆盖）
  · `electric_blast_furnace.mtl` 与四个 model JSON（本轮不动，配套留档）
  · `_zf91_bake.py`（重烘就是跑它；留一份当时的样子）
  · `_zf78_falsify.py`（要挂 ZF92 与加刀）
  · `_zf91_verify.py`（本轮不改，但它是"旧真相"的看守，留档）
  · 两份文档、旧成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf92_pre"
MB = r"src\main\resources\assets\potato_s_t\models\block"
FILES = [
    MB + r"\electric_blast_furnace_north.obj",
    MB + r"\electric_blast_furnace_south.obj",
    MB + r"\electric_blast_furnace_east.obj",
    MB + r"\electric_blast_furnace_west.obj",
    MB + r"\electric_blast_furnace.mtl",
    MB + r"\electric_blast_furnace_north.json",
    MB + r"\electric_blast_furnace_south.json",
    MB + r"\electric_blast_furnace_east.json",
    MB + r"\electric_blast_furnace_west.json",
    r"build\zftools\_zf91_bake.py",
    r"build\zftools\_zf91_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
# 用户工程原件（ZF91 留档过，这里再留一份，方便 ZF92 复现"改哪两个元素"）
BB_KEEP = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s（重跑会覆盖改前件，直接中止）" % BK)
        return 1
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
    if not os.path.exists(BB_KEEP):
        fails.append(u"用户工程留档不在：%s" % BB_KEEP)
    else:
        dst = os.path.join(BK, "user", "electric_blast_furnace.bbmodel")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(BB_KEEP, dst)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()
        ok += 1
        lines.append(u"sha256 %s  %10d  %s" % (h, os.path.getsize(dst),
                                              u"user\\electric_blast_furnace.bbmodel"))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
