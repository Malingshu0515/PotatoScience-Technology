# -*- coding: utf-8 -*-
r'''_zf144_bkfix.py —— 把**我的**改前件从（被两家共用的）`zf142_pre` 搬到 `zf144_pre`。

背景：`zf142_pre` 是**两家先后写进去的**（他们 23:33 建、我 23:39 又写了一批）。
我改号成 ZF144 之后，我的备份根要独立出来 —— 但**不能重跑备份**：
现在的盘上已经不是"改前"了（`ModTiers` / `ModItems` / 四语言 / 文档都改过了，重跑只会把
改后的内容抄成"改前件"）。所以这一趟是**搬运**：
    从 `zf142_pre` 里把我那批（时间点 23:39 那次拷进去的）**原样复制**到 `zf144_pre`，
    再按新根重算一份 `_sha1.txt`；`zf142_pre` 保持原样（他们的东西一个不动）。

跑法：python build\zftools\_zf144_bkfix.py [--write]
'''
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
OLD = os.path.join(r"C:\PotatoST救援", "zf142_pre")
NEW = os.path.join(r"C:\PotatoST救援", "zf144_pre")

# 我那一轮的 NAMED 名单（与 _zf144_backup.py 一致）+ 四类 glob
NAMED = [
    r"src\main\java\com\potatost\mod\StarSteelSwordItem.java",
    r"src\main\java\com\potatost\mod\StarSteelTools.java",
    r"src\main\java\com\potatost\mod\ModTiers.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\用户素材\_来源凭据.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf104_gates.ps1",
    r"build\zftools\_zf104_gatecount.py",
    r"build\zftools\TextureCheck.py",
]
GATE_PAT = ("_verify.py", "_check.py", "_chain.py", "_falsify.py",
            "_gatesnap.py", "_fluidcheck.py", "_langcheck.py", "_repro.py")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    todo = list(NAMED)
    if os.path.isdir(os.path.join(OLD, "build", "zftools")):
        for name in sorted(os.listdir(os.path.join(OLD, "build", "zftools"))):
            if any(name.endswith(p) for p in GATE_PAT):
                rel = os.path.join("build", "zftools", name)
                if rel not in todo:
                    todo.append(rel)

    lines, miss = [], []
    for rel in todo:
        src = os.path.join(OLD, rel)
        if not os.path.isfile(src):
            miss.append(rel)
            continue
        lines.append(u"%s\t%s\t%d" % (sha1(src), rel, os.path.getsize(src)))
    print(u"要搬 %d 份（缺 %d）" % (len(lines), len(miss)))
    if miss:
        print(u"  ⚠ 不在旧根里的：%s" % miss[:5])
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    for rel in todo:
        src = os.path.join(OLD, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(NEW, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if sha1(dst) != sha1(src):
            print(u"  !! 搬运后哈希不一致：%s" % rel)
            return 1
    io.open(os.path.join(NEW, u"_sha1.txt"), u"w", encoding=u"utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    io.open(os.path.join(NEW, u"_说明.txt"), u"w", encoding=u"utf-8", newline=u"\n").write(
        u"ZF144 改前件（星璨钢锹 + 剑的星辉斩）\n"
        u"⚠ 本根是从 `zf142_pre` **搬**过来的，不是重跑的：\n"
        u"  我这一轮一开始误取了 ZF142，而另一条线正在用 ZF142（星图极带模糊），\n"
        u"  两家的备份先后写进了同一个 `zf142_pre`。改号成 ZF144 之后，\n"
        u"  把我那批（23:39 那次拷进去的）原样搬到本根，`zf142_pre` 保持原样不动。\n"
        u"  被误覆盖的他们那份 `_sha1.txt` 由 `_zf142_repair.py` 按他们脚本里的清单重建，\n"
        u"  说明写在 `zf142_pre\\_补说明_被误覆盖的sha1清单.txt`。\n")
    print(u"已搬完并写好 _sha1.txt / _说明.txt")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
