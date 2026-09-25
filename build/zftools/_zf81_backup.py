# -*- coding: utf-8 -*-
u"""_zf81_backup.py —— ZF81 **动手前**的改前件（§10：第一个字节改动之前先抄）

本轮：用户原话「**电解器还是改成 1000Fe/t 吧**」。
预计改动（都已按"先扫活体数字"扫过一遍，见 `_zf81_scan`）：
  · `ElectrolyzerBlockEntity.java`（两个能耗常量 + 注释里的 100 FE/t）
  · 四份 lang（电解器 tooltip 里的 100 FE）
  · `docs/UpdateAnnouncement_EN.md`（电解器那一行的 100 FE/t）
  · `docs/开发档案.md`（§5 ZF81 行 + §9 验收）
  · `build/zftools/_zf71_verify.py`（活体核对：常量 = 100、tooltip 含 100 FE）
  · `build/zftools/_zf78_falsify.py`（加本轮刀）
  · 成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf81_pre"

FILES = [
    r"src\main\java\com\potatost\mod\ElectrolyzerBlockEntity.java",
    r"src\main\java\com\potatost\mod\MachineRecipes.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s（不覆盖）" % BK)
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
    io.open(os.path.join(BK, "_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
