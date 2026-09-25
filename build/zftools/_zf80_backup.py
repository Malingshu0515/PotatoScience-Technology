# -*- coding: utf-8 -*-
u"""_zf80_backup.py —— ZF80 **动手前**的改前件（§10：第一个字节改动之前先抄）

本轮起因：用户实测「灌装机不往油桶灌液体」。预计改动（视探针结果而定）：
  · `FillingMachineBlockEntity.java` / `FillingMachineMenu.java`（灌装核心或那道门）
  · `FillingMachineBlock.java`（若需要加"手里拿容器右键倒进机器"）
  · `OilBucketItem.java` / `OilBucketContents.java` / `FluidContainerItem.java`
  · 四份 lang（若有新提示）
  · `PotatoST.java`（临时探针挂钩，跑完还原；也抄一份留证）
  · 往轮校验脚本（`_zf78_verify.py` / `_zf79_verify.py`）与新建 `_zf80_verify.py`
  · 四份文档
  · 成品 jar 与 `.sha1`

逐份核哈希；文件不在就记 MISS（不静默跳过）。
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
BK = r"C:\PotatoST救援\zf80_pre"

FILES = [
    r"src\main\java\com\potatost\mod\FillingMachineBlockEntity.java",
    r"src\main\java\com\potatost\mod\FillingMachineBlock.java",
    r"src\main\java\com\potatost\mod\FillingMachineMenu.java",
    r"src\main\java\com\potatost\mod\OilBucketItem.java",
    r"src\main\java\com\potatost\mod\OilBucketContents.java",
    r"src\main\java\com\potatost\mod\FluidContainerItem.java",
    r"src\main\java\com\potatost\mod\HighPressureTankItem.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"docs\开发档案.md",
    r"docs\v0.11规划.md",
    r"docs\贴图清单.md",
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
