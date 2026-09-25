# -*- coding: utf-8 -*-
u"""_zf90_presupply2.py —— 给 zf90_pre 再补 4 份改前件（§10；用户又丢了两样东西）

本轮进行到一半，用户又往 `textures/item` 放了两样：
  · `柴油桶_001.png`（3188 B，16×16 RGBA 真 PNG，含 110 个透明像素）—— 柴油桶的图；
  · `copper_plate.png` 被**换了一版**（929 B → 3297 B；画面同一块铜板，边缘是重导出的）。

它们会牵动：柴油桶的模型（现在借原版水桶贴图）、`_zf71_verify.py` 与英文公告里那条
「借原版贴图的模型 = 7 个」的活体数字、以及 `docs/贴图清单.md`（重跑 `--plan`）。

所以先把这几份**动它之前**的内容抄进快照：
  `models/item/diesel_bucket.json` / `_zf71_verify.py` / `UpdateAnnouncement_EN.md` / 用户原图 `柴油桶_001.png`。
（`copper_plate.png` 的**改前那一版**（929 B）不在盘上了 —— 它在 `zf90_pre` 自带的那个成品 jar 里，
 需要时 `unzip` 取回；这一条写进 `_补说明.txt`。）
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
BK = r"C:\PotatoST救援\zf90_pre"
FILES = [
    r"src\main\resources\assets\potato_s_t\models\item\diesel_bucket.json",
    r"src\main\resources\assets\potato_s_t\textures\item\柴油桶_001.png",
    r"build\zftools\_zf71_verify.py",
    r"docs\UpdateAnnouncement_EN.md",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    lines = [u"zf90_pre 补账（第二批，§10）", u"",
             u"用户在本轮中途又放了两样（柴油桶图 + 重导出的铜板图），牵动柴油桶模型、",
             u"`_zf71_verify.py` 与英文公告里的活体数字（借原版贴图 7 → 6），以及贴图清单。", u"",
             u"⚠ `copper_plate.png` 的**改前那一版（929 B）盘上已无** —— 它在 zf90_pre 自带的",
             u"   成品 jar（`release\\PotatoST-0.11.jar`，即 ZF89 的 `05895f2d…`）里，",
             u"   条目 `assets/potato_s_t/textures/item/copper_plate.png`，随时可逐字节取回。", u""]
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
            print(u"  [OK]   %s  %s…（%d 字节）" % (rel, after[:8], os.path.getsize(dst)))
    io.open(os.path.join(BK, u"_补说明2.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"补账 %d 份 → %s\\_补说明2.txt" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
