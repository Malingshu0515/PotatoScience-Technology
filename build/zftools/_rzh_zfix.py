# -*- coding: utf-8 -*-
r"""_rzh_zfix.py —— 用户手改中文之后的收口：修断句 + 清残留 + 补回多删。

分三组，全部走 `_rzh_fix_batch.py` 的 EDITS 通道（行首锚定 + 旧值必须相等）：

  A. zh_cn 断句修复：用户删减留下的悬空破折号 / 顿号开头 / 空首行 / 重复字。
     **只补成通顺，不回填他删掉的信息**（他的尺度是"能删就删"）。
  B. lzh：`acidic_reaction_chamber` 里我上一轮漏删的 ①②③ 配方表（zh 已无，
     文言文独有 —— 属于"同一份提示在一种语言里多出三行配方"）。
  C. lzh：`star_steel_armor` / `titanium_armor` 我上一轮删掉的 24 锭配方表
     —— 用户这次没删，按"以 zh 为准"补回。

用法：`python build/zftools/_rzh_zfix.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")


def cur(loc, key):
    """读盘上当前值 —— 旧值绝不手抄。"""
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


# ---------------------------------------------------------------------------
# A. zh_cn 断句修复
# ---------------------------------------------------------------------------
ZH = [
    (u"tooltip.potato_s_t.star_steel_axe.3",
     u"冲击波拆掉沿途所有原木 \n在末地：额外造成远程伤害",
     u"冲击波拆掉沿途所有原木；撞上斧子挖不动的方块、或 10 秒没碰到木头就消失。\n在末地：额外造成远程伤害"),

    (u"tooltip.potato_s_t.oil_pump",
     u"只在海洋油田群系开工 —— 脚下不是海洋油田一律停机。\n下方必须是水源 需要含水锁链（最多数 64 格）。\n每采出 25~80 桶，以机器为中心 10×10 个区块的海洋油田会变成普通海洋（冻洋 / 暖洋 / 温带海洋…）。\n⚠ 那 100 个区块包含机器自己所在 ",
     u"只在海洋油田群系开工 —— 脚下不是海洋油田一律停机。\n下方必须是水源 需要含水锁链（最多数 64 格）。\n每采出 25~80 桶，以机器为中心 10×10 个区块的海洋油田会变成普通海洋（冻洋 / 暖洋 / 温带海洋…）。\n⚠ 那 100 个区块包含机器自己所在，抽一次之后得把机器挪到还剩油田的地方。"),

    (u"tooltip.potato_s_t.star_steel_set",
     u"星璨钢套：与夜同频。\n夜幕落下时，；此时装备将不损 发出星璨之光的力量，头盔会点亮相貌之外的视野\n四件共振，才是它真正的形态：末地之中永不磨损；\n虚空也夺不走你 —— 它会在 20×20 内为你寻一处落脚的方块，先托住你、再抹去坠落；若四下无物，便与附近的生物交换位置。",
     u"星璨钢套：与夜同频。\n夜幕落下时，每一件都获得抗性提升 I；此时装备不磨损。星璨钢的力量不止于此 —— 头盔还会点亮相貌之外的视野。\n四件共振，才是它真正的形态：末地之中永不磨损。\n虚空也夺不走你 —— 它会在 20×20 内为你寻一处落脚的方块，先托住你、再抹去坠落；若四下无物，便与附近的生物交换位置。"),

    (u"tooltip.potato_s_t.titanium_alloy_set",
     None,   # 同 ZH 列表里的 old 由 cur() 取
     u"钛合金套：坚韧与附魔的平衡。\n比金更受附魔台青睐，也比金更扛得住。"),

    (u"advancements.potato_s_t.steel.description",
     None,
     u"钢材是后面几乎所有东西的骨架"),

    (u"tooltip.potato_s_t.ammonia_synthesis_chamber",
     None,
     u"催化剂槽要放铁粉。\n原料罐下方的气罐槽按 50 mB/t，把气罐里的氮 / 氢灌进机器；\n输出罐下方的气罐槽是反向的：50 mB/t，把氨气灌进气罐。\n泵只能泵入氮气 / 氢气、泵出氨气；有红石信号即停机。"),

    # ---- 小瑕疵 ----
    (u"advancements.potato_s_t.capacitor.description",
     None, u"这可是超级电容器！"),

    (u"advancements.potato_s_t.blast_furnace.description",
     None, u"一栋 3×3×3 的多方块机器，产能的提升"),

    (u"advancements.potato_s_t.vibranium.description",
     None, u"昂贵的原材料"),

    (u"advancements.potato_s_t.fuel.description",
     None, u"两种液体燃料，老大脾气倔，老二倔脾气"),

    (u"advancements.potato_s_t.starfall.description",
     None, u"右键甩出星轨坠：30 秒倒计时、前 10 秒可取消"),

    (u"advancements.potato_s_t.star_steel_slash.description",
     None, u"什么时候可以召唤星辉死神？"),

    (u"advancements.potato_s_t.music_disc_anvil.title",
     None, u"共和国之砧（或者 贞？）"),

    (u"advancements.potato_s_t.music_disc_anvil.description",
     None, u"共和国不会怜悯只会打铁的你"),

    (u"gui.potato_s_t.fluid_exchanger.status.output_full",
     None, u"[容器换流器] 右槽要放「1 个」空桶 —— 它会原地变成那种流体的桶"),
]

# ---------------------------------------------------------------------------
# B/C. lzh 修正
# ---------------------------------------------------------------------------
LZH = [
    # B. 酸反应室：zh 已删掉整张配方表，文言文里还留着三行
    (u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"原料罐四（各 1000 mB）：二氧化碳 / 氧氣 / 氨氣 / 水；產物罐三：碳酸 / 硝酸 / 硫酸。\n以按鈕擇方：① 10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸　② 1 mB 氧氣 + 1 mB 氨氣 → 1 mB 硝酸\n③ 10 個硫 + 100 mB 水 → 100 mB 硫酸（一批 5 秒，材料至末刻方扣）\n耗電皆 500 FE/t，緩衝 12400 FE（須持續供電）；有紅石信號即停機。\n友情之告：此中所產，請勿飲之。",
     u"耗電 500 FE/t\n友情之告：此中所產，請勿飲之。"),
]


def main():
    edits = []
    skipped = []
    for key, old, new in ZH:
        if old is None:
            old = cur(u"zh_cn", key)
        if old == new:
            skipped.append(key)
            continue
        edits.append((u"zh_cn", key, old, new))

    for key, old, new in LZH:
        on_disk = cur(u"lzh", key)
        if on_disk == new:
            skipped.append(key)
            continue
        if on_disk != old:
            raise SystemExit(u"[拒绝] lzh %s 与预期不符\n  盘上: %r\n  预期: %r"
                             % (key, on_disk, old))
        edits.append((u"lzh", key, old, new))

    # 走既有入口：把 EDITS 注入后调用它自己的 main()
    import _rzh_fix_batch as fb
    fb.EDITS = edits
    if skipped:
        print(u"（%d 条已是目标值，跳过）" % len(skipped))
    print(u"待改 %d 条" % len(edits))
    return fb.main()


if __name__ == u"__main__":
    sys.exit(main())
