# -*- coding: utf-8 -*-
u"""_zf166_retarget.py —— ZF166 的**跟平**：把本轮合法改动作废的判据跟到新事实（绝不放宽）。

本轮活体数字：语言键 **593 → 605**（lzh **595 → 607**，加了 12 个流体转化器键）、
配方 **93 → 94**（生成器表加了一条）、方块物品 **36 → 37**、`crafting_shaped` **66 → 67**、
class 数（打包后看）、成品哈希（打包后跟）。

跑法：python build\\zftools\\_zf166_retarget.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
GATES = [u"_zf64_verify.py", u"_zf70_verify.py", u"_zf71_verify.py", u"_zf72_verify.py",
         u"_zf73_repro.py", u"_zf73_verify.py", u"_zf74_verify.py", u"_zf75_verify.py",
         u"_zf78_verify.py", u"_zf79_verify.py", u"_zf80_verify.py", u"_zf81_verify.py",
         u"_zf82_verify.py", u"_zf89_verify.py", u"_zf90_verify.py", u"_zf91_verify.py",
         u"_zf92_verify.py", u"_zf93_verify.py", u"_zf94_verify.py", u"_zf95_verify.py",
         u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py", u"_zf99_verify.py",
         u"_zf100_verify.py", u"_zf100_recipe_guard.py", u"_zf101_verify.py",
         u"_zf102_verify.py", u"_zf103_verify.py", u"_zf104_verify.py", u"_zf107_verify.py",
         u"_zf108_verify.py", u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py",
         u"_zf113_verify.py", u"_zf114_verify.py", u"_zf117_verify.py", u"_zf118_verify.py",
         u"_zf119_verify.py", u"_zf120_verify.py", u"_zf121_verify.py", u"_zf122_verify.py",
         u"_zf123_verify.py", u"_zf123_langaudit.py", u"_zf124_verify.py", u"_zf125_verify.py",
         u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py", u"_zf133_verify.py",
         u"_zf134_verify.py", u"_zf135_verify.py", u"_zf139_verify.py", u"_zf141_verify.py",
         u"_zf142_verify.py", u"_zf143_verify.py", u"_zf144_verify.py", u"_zf145_verify.py",
         u"_zf146_verify.py", u"_zf148_verify.py", u"_zf149_verify.py", u"_zf151_verify.py",
         u"_zf150_verify.py", u"_zf153_verify.py", u"_zf155_verify.py", u"_zf156_verify.py",
         u"_zf158_verify.py", u"_zf160_verify.py", u"_zf162_verify.py", u"_zf164_verify.py",
         u"_zf137_verify.py", u"_zf140_verify.py", u"_zf117_audit.py", u"_zf109_tabaudit.py",
         u"_zf149_jar.py", u"_zf156_jarcheck.py", u"_zf155_jarcheck.py"]

NUM = [(u"593", u"605"), (u"595", u"607")]

EDITS = [
    # 键集合：ZF155 / ZF162 那两条"新增键"名单也要把 ZF166 那 12 个算进去
    (u"_zf155_verify.py",
     u'        ZF162_ADDED = {u"gui.potato_s_t.filling.diag.unsupported"}',
     u'        ZF162_ADDED = {u"gui.potato_s_t.filling.diag.unsupported"}\n'
     u'        ZF166_ADDED = {u"block.potato_s_t.fluid_converter",\n'
     u'                       u"tooltip.potato_s_t.fluid_converter",\n'
     u'                       u"gui.potato_s_t.fluid_converter.tank.input",\n'
     u'                       u"gui.potato_s_t.fluid_converter.tank.output",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.input_empty",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.target_empty",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.same_fluid",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.no_shared_tag",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.output_full",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.no_power",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.running",\n'
     u'                       u"gui.potato_s_t.fluid_converter.status.idle"}',
     u"_zf155：B7 加上 ZF166 那 12 个键"),
    (u"_zf155_verify.py",
     u"            if added != set(NEW_KEYS) | ZF162_ADDED:",
     u"            if added != set(NEW_KEYS) | ZF162_ADDED | ZF166_ADDED:",
     u"_zf155：B7 判据带上 ZF166"),
    (u"_zf155_verify.py",
     u"                                    % (lg, sorted(added ^ (set(NEW_KEYS) | ZF162_ADDED))))",
     u"                                    % (lg, sorted(added ^ (set(NEW_KEYS) | ZF162_ADDED | ZF166_ADDED))))",
     u"_zf155：B7 报错信息带上 ZF166"),
    # 配方份数 93 → 94
    (u"_zf149_jar.py",
     u'check(len(recipes) == 93, u"① 配方份数（发布那一刻的实测值；ZF162 重打时 93：ZF160 的 94 减掉电力高炉那条）",',
     u'check(len(recipes) == 94, u"① 配方份数（发布那一刻的实测值；ZF166 重打时 94：ZF162 的 93 + 流体转化器）",',
     u"_zf149_jar：配方 93 → 94"),
    (u"_zf156_jarcheck.py",
     u'check(len(recipes) == 93, u"③ jar 里配方 93 份（ZF156 的 91 + 另一条线在途的 3 份 generator_fuel'
     u' − ZF162 删掉的电力高炉那 1 份）",',
     u'check(len(recipes) == 94, u"③ jar 里配方 94 份（ZF162 的 93 + ZF166 的流体转化器）",',
     u"_zf156_jarcheck：配方 93 → 94"),
    (u"_zf149_verify.py",
     u'u"**365 classes, 43 advancements, 93 recipes**" in ann',
     u'u"**365 classes, 43 advancements, 94 recipes**" in ann',
     u"_zf149_verify：公告那句的配方数 93 → 94（class 数由 _zf166_docs.py 打包后再跟）"),
    (u"_zf149_verify.py",
     u'u"C7 公告 Download 段那一句的三个数跟到 365 / 93（43 不变；ZF162 重打时的实测值）"',
     u'u"C7 公告 Download 段那一句的三个数跟到 365 / 94（43 不变；ZF166 重打时的实测值）"',
     u"_zf149_verify：C7 标签跟到 ZF166"),
    (u"_zf162_verify.py",
     u"check(n_recipe == 93, u\"D3 盘上配方 93 份（94 − 电力高炉那条）\", u\"实际 %d\" % n_recipe)",
     u"check(n_recipe == 94, u\"D3 盘上配方 94 份（ZF166 起：电力高炉那条删掉、加了流体转化器）\", u\"实际 %d\" % n_recipe)",
     u"_zf162：D3 配方份数 93 → 94"),
    # 方块物品 36 → 37；crafting_shaped 66 → 67
    (u"_zf109_verify.py",
     u'    check(u"ModBlocks 的方块物品一共 36 个（账目基准；ZF112 锂电池构造间、ZF125 柴油发电机控制器'
     u'、ZF162 删掉电力高炉物品形态）",\n          len(registered) == 36,',
     u'    check(u"ModBlocks 的方块物品一共 37 个（账目基准；ZF112 锂电池构造间、ZF125 柴油发电机控制器'
     u'、ZF162 删掉电力高炉物品形态、ZF166 流体转化器）",\n          len(registered) == 37,',
     u"_zf109：方块物品 36 → 37"),
    (u"_zf134_verify.py",
     u"EXPECT_SHAPED = 66   # 0.13 ZF162：删掉电力高炉那条 crafting_shaped 配方 ⇒ 67 → 66",
     u"EXPECT_SHAPED = 67   # 0.13 ZF166：加了流体转化器那条 crafting_shaped 配方 ⇒ 66 → 67",
     u"_zf134：crafting_shaped 66 → 67"),
    # 我自己那两条门也要跟（键数 + 探针报告名）
    (u"_zf164_verify.py",
     u'check(counts.get(u"zh_cn") == 593 and counts.get(u"lzh") == 595,',
     u'check(counts.get(u"zh_cn") == 605 and counts.get(u"lzh") == 607,',
     u"_zf164：C5 键数跟到 ZF166"),
    (u"_zf164_verify.py",
     u'      u"C5 语言键数仍是 593×4 + 595（本轮不加键）", repr(counts))',
     u'      u"C5 语言键数 605×4 + 607（ZF166 加了 12 个流体转化器键）", repr(counts))',
     u"_zf164：C5 标签跟到 ZF166"),
]


def main(argv):
    write = u"--write" in argv
    changed, done, fails, notes = set(), 0, [], []
    for name in GATES:
        p = os.path.join(ZT, name)
        if not os.path.isfile(p):
            notes.append(u"（不在盘上）%s" % name)
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        new = text
        for a, b in NUM:
            new = new.replace(a, b)
        if new != text:
            hits = sum(1 for l1, l2 in zip(text.split(u"\n"), new.split(u"\n")) if l1 != l2)
            notes.append(u"%s：活体数字换 %d 行" % (name, hits))
            changed.add(name)
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(new)
    for name, old, new, why in EDITS:
        p = os.path.join(ZT, name)
        if not os.path.isfile(p):
            fails.append(u"%s 不在盘上（%s）" % (name, why))
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        if text.count(old) == 0 and new in text:
            notes.append(u"%s：（已跟平过，跳过）%s" % (name, why))
            continue
        if text.count(old) != 1:
            fails.append(u"%s：改前串出现 %d 次 —— %s" % (name, text.count(old), why))
            continue
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))
        done += 1
        changed.add(name)
        notes.append(u"%s：%s" % (name, why))
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"\n改到的门：%d 份；语义跟平 %d 处" % (len(changed), done))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
