# -*- coding: utf-8 -*-
u"""_zf86_backup.py —— ZF86 **动手前**的改前件（§10；用户又放了四张素材：铜板被存成了 JPEG + 氯化钠 + 电容 + 碳酸锂）"""
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
BK = r"C:\PotatoST救援\zf86_pre"
TEX = r"src\main\resources\assets\potato_s_t\textures\item"
MODELS = r"src\main\resources\assets\potato_s_t\models\item"
FILES = [
    TEX + r"\copper_plate.png",
    TEX + u"\\氯化钠.jpg",
    TEX + u"\\电容.jpg",
    TEX + u"\\碳酸锂.png",
    MODELS + r"\lithium_carbonate.json",
    MODELS + r"\sodium_chloride.json",
    MODELS + r"\capacitor.json",
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
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
