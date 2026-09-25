# -*- coding: utf-8 -*-
u"""_zf8687_archive.py —— ZF86 / ZF87 归档（各自进自己的 `新增文件\\`）

两个阶段各抄一份、逐份核哈希、每类断言"至少 N 份"（防 glob 写错静默少拷）。
"""
import glob
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
TEX = r"src\main\resources\assets\potato_s_t\textures\item"
MODEL = r"src\main\resources\assets\potato_s_t\models\item"

ROUNDS = [
    (r"C:\PotatoST救援\zf86_pre", u"ZF86：四张素材转档", [
        ([TEX + r"\copper_plate.png", TEX + r"\sodium_chloride.png",
          TEX + r"\capacitor.png", TEX + r"\lithium_carbonate.png",
          MODEL + r"\sodium_chloride.json", MODEL + r"\capacitor.json",
          MODEL + r"\lithium_carbonate.json"], 7),
        ([r"build\zftools\_zf86_*.py", r"build\zftools\_zf86_*.ps1",
          r"build\zftools\_zf86_*.log", r"build\zftools\_zf86_gates.txt",
          r"build\zftools\_zf86_jpg_pixels.json"], 8),
        ([r"docs\开发档案.md", r"docs\贴图清单.md"], 2),
    ]),
    (r"C:\PotatoST救援\zf87_pre", u"ZF87：油桶贴图", [
        ([TEX + r"\oil_bucket.png", MODEL + r"\oil_bucket.json",
          r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1"], 4),
        ([r"build\zftools\_zf87_*.py", r"build\zftools\_zf87_*.ps1",
          r"build\zftools\_zf87_gates.txt", r"build\zftools\_zf87_oil_pixels.json"], 4),
        ([r"docs\开发档案.md", r"docs\贴图清单.md"], 2),
    ]),
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    for bk, title, groups in ROUNDS:
        new = os.path.join(bk, u"新增文件")
        print(u"== %s ==" % title)
        total, size, lines = 0, 0, []
        for patterns, minimum in groups:
            files = []
            for pat in patterns:
                if u"*" in pat:
                    files += [p for p in glob.glob(os.path.join(ROOT, pat)) if os.path.isfile(p)]
                else:
                    p = os.path.join(ROOT, pat)
                    if os.path.isfile(p):
                        files.append(p)
            files = sorted(set(files))
            if len(files) < minimum:
                fails.append(u"%s：只找到 %d 份（至少应有 %d）" % (title, len(files), minimum))
            for src in files:
                rel = os.path.relpath(src, ROOT)
                dst = os.path.join(new, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                before = sha1(src)
                shutil.copy2(src, dst)
                after = sha1(dst)
                if before != after:
                    fails.append(u"%s：拷贝后哈希不一致" % rel)
                else:
                    total += 1
                    size += os.path.getsize(dst)
                    lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
        io.open(os.path.join(bk, u"新增文件_清单.txt"), "w", encoding="utf-8",
                newline=u"\n").write(u"# %s 归档（%d 份，逐份核过哈希）\n\n" % (title, total)
                                     + u"\n".join(lines) + u"\n")
        print(u"   归档 %d 份 / %.1f KB" % (total, size / 1024.0))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
