# -*- coding: utf-8 -*-
u"""_zf151_falsify.py —— ZF151 反证刀（静态，**不开游戏**）：改一处 ⇒ 指定那一项必须变红 ⇒ 还原必须回绿。

跑法：python build\\zftools\\_zf151_falsify.py
"""
import hashlib
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
V = os.path.join(ZT, u"_zf151_verify.py")
SOLAR = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "SolarPanelBlock.java")
MODB = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "ModBlocks.java")
TAG = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft", "tags", "block",
                   "mineable", "pickaxe.json")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

KNIVES = [
    (u"K1 抠掉 SolarPanelBlock 的 getDrops 覆写", SOLAR,
     u"    public List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {\n"
     u"        return List.of(new ItemStack(this));\n    }",
     u"    // [ZF151 反证] getDrops 被抠掉了", u"A1 SolarPanelBlock 覆写了 getDrops"),
    (u"K2 返回值改成空表（= 修了等于没修）", SOLAR,
     u"return List.of(new ItemStack(this));", u"return List.of();", u"A2 返回值是 List.of(new ItemStack(this))"),
    (u"K3 标签里删掉 fluid_exchanger", TAG,
     u'    "potato_s_t:diesel_generator_port",\n    "potato_s_t:fluid_exchanger",',
     u'    "potato_s_t:diesel_generator_port",', u"B3 本轮补的那一项在标签里：fluid_exchanger"),
    (u"K4 标签里删掉 solar_panel", TAG,
     u'    "potato_s_t:solar_panel",\n', u"", u"B4 太阳能板仍在标签里"),
    (u"K5 给柴油机接线口加回 requiresCorrectToolForDrops", MODB,
     u'                    .sound(SoundType.METAL)\n'
     u'                    .noLootTable()));\n'
     u'\n'
     u'    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DieselGeneratorPortBlockEntity>>',
     u'                    .sound(SoundType.METAL)\n'
     u'                    .requiresCorrectToolForDrops()\n'
     u'                    .noLootTable()));\n'
     u'\n'
     u'    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DieselGeneratorPortBlockEntity>>',
     u"C3 柴油机接线口已去掉 requiresCorrectToolForDrops"),
    (u"K6 建筑材家族 helper 里的 requiresCorrectToolForDrops", MODB,
     u"                .sound(SoundType.METAL)\n"
     u"                .requiresCorrectToolForDrops());\n"
     u"    }\n"
     u"\n"
     u"    /** 一般金属块 */",
     u"                .sound(SoundType.METAL));\n"
     u"    }\n"
     u"\n"
     u"    /** 一般金属块 */",
     u"C4 建材家族的 requiresCorrectToolForDrops"),
    (u"K7 档案里删掉 §5 的 ZF151 行标记", DOC,
     u"| ZF151 |", u"| ZF151x |", u"D2 档案 §5 有 ZF151 行"),
    (u"K8 公告里删掉 ZF151 那一条的标题", ANN,
     u"## New in 0.12 ZF151", u"## (deleted)", u"D4 英文公告里有 ZF151 那一条"),
]

fails, rows = [], []


def main():
    for label, path, old, new, marker in KNIVES:
        original = open(path, "rb").read()
        h0 = hashlib.sha1(original).hexdigest()
        text = io.open(path, encoding=u"utf-8", newline=u"").read()
        # ⚠ 这棵树里换行**不统一**：`ModBlocks.java` 是 CRLF，`SolarPanelBlock.java` / 标签 / 文档是 LF。
        #   刀的多行锚点一律按 `\n` 写，这里按文件自带的换行翻译一遍再匹配
        #   （第一版没做这层，K5/K6 直接"命中 0 次"）。
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        old_e = old.replace(u"\n", eol)
        new_e = new.replace(u"\n", eol)
        if text.count(old_e) != 1:
            fails.append(u"%s：改前串命中 %d 次（换行=%s）" % (label, text.count(old_e),
                                                              u"CRLF" if eol == u"\r\n" else u"LF"))
            continue
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(text.replace(old_e, new_e, 1))
        r = subprocess.run([sys.executable, V], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=300)
        out = r.stdout.decode(u"utf-8", "replace")
        hit = any(marker in l and u"[FAIL]" in l for l in out.split(u"\n"))
        red = (r.returncode != 0) and hit
        open(path, "wb").write(original)
        restored = hashlib.sha1(open(path, "rb").read()).hexdigest() == h0
        r2 = subprocess.run([sys.executable, V], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=300)
        green = r2.returncode == 0
        rows.append((label, red, restored, green))
        if not red:
            fails.append(u"%s：改坏后**没红**（rc=%d，命中=%s）" % (label, r.returncode, hit))
        if not restored:
            fails.append(u"%s：还原后不是逐字节相同" % label)
        if not green:
            fails.append(u"%s：还原后没回绿" % label)

    print(u"================ ZF151 反证刀（静态 %d 把） ================" % len(KNIVES))
    print(u"%-52s %-6s %-8s %-8s" % (u"刀", u"变红", u"逐字节还原", u"回绿"))
    for label, a, b, c in rows:
        print(u"%-52s %-6s %-8s %-8s" % (label[:50], u"OK" if a else u"!!", u"OK" if b else u"!!",
                                         u"OK" if c else u"!!"))
    ok = len([r for r in rows if r[1] and r[2] and r[3]])
    print(u"")
    print(u"刀数 = %d   全中 = %d   失败 = %d" % (len(KNIVES), ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
