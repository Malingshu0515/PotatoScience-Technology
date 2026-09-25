# -*- coding: utf-8 -*-
u"""_zf82_backup.py —— ZF82 **动手前**的改前件（§10：第一个字节改动之前先抄）

本轮两件（用户原话）：
  ① 「新进 柴油桶 汽油桶（先用水桶贴图）和原版水桶一致 可以倒出相应的流体返回空桶
     并可以被空桶收回源头液体」
  ② 「再加一个【容器换流器】… 3s后 消耗油罐内1000mb的液体 把桶变成相应的流体桶
     （别的mod的流体也可以，前提是流体有对应桶的形式）流体泵也可以把液体泵出
     这个是直接消耗油罐的流体容量 然后泵出 有多少泵多少（取决于泵的速率）配方：…」

预计改动：
  · `ModFluids.java`（柴油/汽油加 `.bucket(...)` 与 `.block(...)`）
  · `ModBlocks.java`（两个新液体方块 diesel / gasoline）
  · `ModItems.java`（两个新桶物品 + 创造页）
  · `ModMenus.java` / `PotatoST.java`（能力）/ `PotatoSTClient.java`（界面）
  · 新机器四件（方块 / 方块实体 / 菜单 / 界面）
  · 4 份 lang / 贴图与模型 / 合成配方 JSON
  · 往轮校验脚本（活体数字：257 键、29 条合成配方）与 4 份文档
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
BK = r"C:\PotatoST救援\zf82_pre"

FILES = [
    r"src\main\java\com\potatost\mod\ModFluids.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\ModMenus.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\PotatoSTClient.java",
    r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\blockstates\crude_oil.json",
    r"src\main\resources\assets\potato_s_t\models\block\crude_oil.json",
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf81_verify.py",
    r"build\zftools\_zf78_falsify.py",
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
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
