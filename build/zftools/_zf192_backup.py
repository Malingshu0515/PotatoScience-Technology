# -*- coding: utf-8 -*-
u"""_zf192_backup.py —— ZF192 **改前备份根**（§10：动手前先备份，逐份核 sha1 + 回读）。

主题：**坍缩模式副手不用放方块**（「空手也能放」）：`use()` / `onUseTick()` / `fire()` 三处按模式放行，
黑洞的"种子方块"用 `Blocks.AIR` 当哨兵，`loadFrom` 只对**非坍缩**模式把 AIR 当成"方块没了"丢掉。

跑法：python build\\zftools\\_zf192_backup.py
"""
import glob
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DEST = os.path.join(ROOT, "build", "zftools", "zf192_pre")

FIXED = [
    r"src\main\java\com\potatost\mod\GravityDeviceItem.java",
    r"src\main\java\com\potatost\mod\BlackHoleManager.java",
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
    r"build\zftools\_zf186_verify.py",
    r"build\zftools\_zf188_verify.py",
    r"build\zftools\_zf190_verify.py",
    r"build\zftools\_zf190_repack.py",
    r"build\zftools\_zf186_gatesnap.py",   # 全门快照脚本（各轮共用这一份）
    r"build\zftools\check\Zf186Check.java",
    r"build\zftools\check\Zf188Check.java",
    r"build\zftools\check\Zf190Check.java",
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
        if b.startswith(u"_zf192") or u"falsify" in b or u"_bak" in b:
            continue
        if any(b.endswith(a) for a in (u"_verify.py", u"_repro.py", u"_guard.py", u"_audit.py")):
            gates.append(os.path.join("build", "zftools", b))
    rels = FIXED + gates

    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    manifest, fails = [], []
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
    back = io.open(os.path.join(DEST, "MANIFEST.txt"), encoding="utf-8").read().strip().split(u"\n")
    miss = [l for l in back if not os.path.isfile(os.path.join(DEST, l.split(u"  ")[-1]))]
    print(u"备份根：%s" % DEST)
    print(u"份数 = %d（其中常驻门 %d）   失败 = %d   清单缺件 = %d"
          % (len(manifest), len(gates), len(fails), len(miss)))
    for f in fails + miss:
        print(u"  !! " + f)
    return 1 if (fails or miss) else 0


if __name__ == u"__main__":
    sys.exit(main())
