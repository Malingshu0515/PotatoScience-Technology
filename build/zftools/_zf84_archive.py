# -*- coding: utf-8 -*-
u"""_zf84_archive.py —— 把 ZF84 的改动归档到 `C:\\PotatoST救援\\zf84_pre\\新增文件\\`"""
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
BK = r"C:\PotatoST救援\zf84_pre"
NEW = os.path.join(BK, u"新增文件")

GROUPS = [
    (u"资源：汽油的两张流体贴图 + 原图",
     [r"src\main\resources\assets\potato_s_t\textures\block\gasoline_still.png",
      r"src\main\resources\assets\potato_s_t\textures\block\gasoline_flow.png",
      r"build\用户素材\gasoline_new.jpg",
      r"build\用户素材\_来源凭据.json"], 4),
    (u"工具：本轮脚本 + 证据",
     [r"build\zftools\_zf84_*.py",
      r"build\zftools\_zf84_*.ps1",
      r"build\zftools\_zf84_pixels.json",
      r"build\zftools\_zf84_gates.txt",
      r"build\zftools\_zf78_falsify.py"], 7),
    (u"文档", [r"docs\开发档案.md", r"docs\贴图清单.md"], 2),
    (u"成品", [r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1"], 2),
]

fails = []
lines = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    total = 0
    size = 0
    for title, patterns, minimum in GROUPS:
        files = []
        for pat in patterns:
            files += [p for p in glob.glob(os.path.join(ROOT, pat)) if os.path.isfile(p)]
        files = sorted(set(files))
        if len(files) < minimum:
            fails.append(u"%s：只找到 %d 份（至少应有 %d）" % (title, len(files), minimum))
        print(u"== %s：%d 份 ==" % (title, len(files)))
        for src in files:
            rel = os.path.relpath(src, ROOT)
            dst = os.path.join(NEW, rel)
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
    print(u"\n归档 %d 份 / %.1f KB" % (total, size / 1024.0))
    io.open(os.path.join(BK, u"新增文件_清单.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"# ZF84 归档（%d 份，逐份核过哈希）\n\n" % total
                                 + u"\n".join(lines) + u"\n")
    print(u"清单已写：zf84_pre\\新增文件_清单.txt")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
