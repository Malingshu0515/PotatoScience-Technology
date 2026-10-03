# -*- coding: utf-8 -*-
u"""_zf186_backup.py —— ZF186 **改前备份根**（§10：动手前先备份，逐份核 sha1 + 回读）。

主题：本模组接入 **配置系统**（NeoForge `ModConfigSpec`，COMMON）+ **配置界面**（NeoForge 自带
`ConfigurationScreen`，走 `IConfigScreenFactory` 扩展点，**不新增任何依赖**）。

备份内容（改前件）：
  · 7 份将改源码：`PotatoST` / `GravityDeviceItem` / `BlackHoleManager` /
    `LithiumBatteryBlockEntity` / `LithiumBatteryBlock` / `ModItems`（注释里的旧数字） /
    `META-INF/neoforge.mods.toml`（证明"依赖没变"）；
  · 5 份 lang（要塞配置键，要保持五语种键齐）；
  · 4 份文档 + `_zf149_verify.py`（哈希靶子）+ `gradle.properties` + `build.gradle`；
  · 旧成品 `release\\PotatoST-0.14.jar` + `.sha1`；
  · **全部常驻门**（`_zf*_verify.py` 这类，白名单同 `_zf186_gatesnap.py`）。

跑法：python build\\zftools\\_zf186_backup.py
"""
import glob
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DEST = os.path.join(ROOT, "build", "zftools", "zf186_pre")

FIXED = [
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\GravityDeviceItem.java",
    r"src\main\java\com\potatost\mod\BlackHoleManager.java",
    r"src\main\java\com\potatost\mod\LithiumBatteryBlockEntity.java",
    r"src\main\java\com\potatost\mod\LithiumBatteryBlock.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\META-INF\neoforge.mods.toml",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\0.13_0.14更新公告与介绍_中英.md",
    r"build\zftools\_zf149_verify.py",
    r"gradle.properties",
    r"build.gradle",
    r"release\PotatoST-0.14.jar",
    r"release\PotatoST-0.14.jar.sha1",
]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    gates = []
    for p in sorted(glob.glob(os.path.join(ROOT, "build", "zftools", u"_zf*.py"))):
        b = os.path.basename(p)
        if b.startswith(u"_zf186"):
            continue
        if u"falsify" in b or u"_bak" in b:
            continue
        if any(b.endswith(a) for a in (u"_verify.py", u"_repro.py", u"_guard.py", u"_audit.py")):
            gates.append(os.path.join("build", "zftools", b))
    rels = FIXED + gates

    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    manifest = []
    fails = []
    for rel in rels:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"不在盘上：%s" % rel)
            continue
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        h1, h2 = sha(src), sha(dst)
        size = os.path.getsize(src)
        ok = (h1 == h2) and os.path.getsize(dst) == size
        manifest.append(u"%s  %d  %s  %s" % (h1, size, u"OK" if ok else u"**不符**", rel))
        if not ok:
            fails.append(u"回读不符：%s" % rel)

    io.open(os.path.join(DEST, "MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(manifest) + u"\n")
    print(u"备份根：%s" % DEST)
    print(u"份数 = %d（其中常驻门 %d）   失败 = %d" % (len(manifest), len(gates), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    # 反面自证：清单里每一行都必须在盘上真的存在
    back = io.open(os.path.join(DEST, "MANIFEST.txt"), encoding="utf-8").read().strip().split(u"\n")
    miss = [l for l in back if not os.path.isfile(os.path.join(DEST, l.split(u"  ")[-1]))]
    print(u"清单回读 %d 行；缺件 %d" % (len(back), len(miss)))
    for m in miss:
        print(u"  !! 缺 " + m)
    return 1 if (fails or miss) else 0


if __name__ == "__main__":
    sys.exit(main())
