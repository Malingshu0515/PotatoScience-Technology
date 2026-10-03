# -*- coding: utf-8 -*-
u"""_zf190_backup.py —— ZF190 **改前备份根**（§10：动手前先备份，逐份核 sha1 + 回读）。

主题：
  ① **修 bug**：正常模式召唤只扣**固定 8M**（原来把整条电力条抽干 —— 容量调 64M 时一次扣 64M）；
  ② 引力装置**第三个模式「坍缩模式-危险」**：召唤扣 4M + 每 tick 50k、无差别吸生物/方块、销毁掉落物、
     强度与伤害随年龄涨、没电即消失、2 分钟硬上限 + 30 威力爆炸。

备份内容：2 份将改源码 + `neoforge.mods.toml` + 五份 lang + 4 份文档 + 本轮要动的脚本 +
上一轮两道门与两个探针 + 旧成品与 `.sha1` + **全部常驻门**。

跑法：python build\\zftools\\_zf190_backup.py
"""
import glob
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DEST = os.path.join(ROOT, "build", "zftools", "zf190_pre")

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
    r"build\zftools\_zf186_repack.py",
    r"build\zftools\_zf188_repack.py",
    r"build\zftools\_zf186_gatesnap.py",
    r"build\zftools\check\Zf186Check.java",
    r"build\zftools\check\Zf188Check.java",
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
        if b.startswith(u"_zf190") or u"falsify" in b or u"_bak" in b:
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
