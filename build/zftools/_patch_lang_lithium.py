# -*- coding: utf-8 -*-
"""_patch_lang_lithium.py —— 给 4 个语言文件加锂条目（0.10 ZF15）

**为什么用脚本而不是逐个 edit**：语言文件是 **CRLF**，而 edit 工具插入的新行只带 LF，
会把文件搞成混合换行（§4.8 记过这个风格约束）。这里一次性读原文、按 CRLF 插入、原样写回。

**纪律**：每个锚点必须**恰好出现一次**，否则直接报错退出，绝不"尽力而为"。
改完还会核对：JSON 能解析 + 键数 = 112+4 = 116 + 4 个文件的键集合完全一致。

跑法：
    python build/zftools/_patch_lang_lithium.py --dry
    python build/zftools/_patch_lang_lithium.py
"""
import io
import json
import os
import sys

LANG_DIR = os.path.join("E:\\PotatoST", "src", "main", "resources", "assets", "potato_s_t", "lang")
EXPECTED_BEFORE = 112
EXPECTED_AFTER = 116

# 锚点 ①：锰矿那两行（深层的后面插锂矿石，粗锰后面插粗锂）
ANCHOR_ORE_RAW = {
    "zh_cn.json": ('    "item.potato_s_t.raw_manganese":  "粗锰",',
                   ['    "block.potato_s_t.lithium_ore":  "锂矿石",',
                    '    "item.potato_s_t.raw_lithium":  "粗锂",']),
    "en_us.json": ('    "item.potato_s_t.raw_manganese":  "Raw Manganese",',
                   ['    "block.potato_s_t.lithium_ore":  "Lithium Ore",',
                    '    "item.potato_s_t.raw_lithium":  "Raw Lithium",']),
    "ja_jp.json": ('    "item.potato_s_t.raw_manganese":  "粗マンガン",',
                   ['    "block.potato_s_t.lithium_ore":  "リチウム鉱石",',
                    '    "item.potato_s_t.raw_lithium":  "粗リチウム",']),
    "ru_ru.json": ('    "item.potato_s_t.raw_manganese":  "Необработанный марганец",',
                   ['    "block.potato_s_t.lithium_ore":  "Литиевая руда",',
                    '    "item.potato_s_t.raw_lithium":  "Необработанный литий",']),
}

# 锚点 ②：硅那一行后面插锂矿精粉 / 碳酸锂
ANCHOR_PRODUCTS = {
    "zh_cn.json": ('    "item.potato_s_t.silicon":  "硅",',
                   ['    "item.potato_s_t.lithium_concentrate":  "锂矿精粉",',
                    '    "item.potato_s_t.lithium_carbonate":  "碳酸锂",']),
    "en_us.json": ('    "item.potato_s_t.silicon":  "Silicon",',
                   ['    "item.potato_s_t.lithium_concentrate":  "Lithium Concentrate",',
                    '    "item.potato_s_t.lithium_carbonate":  "Lithium Carbonate",']),
    "ja_jp.json": ('    "item.potato_s_t.silicon":  "ケイ素",',
                   ['    "item.potato_s_t.lithium_concentrate":  "リチウム精鉱",',
                    '    "item.potato_s_t.lithium_carbonate":  "炭酸リチウム",']),
    "ru_ru.json": ('    "item.potato_s_t.silicon":  "Кремний",',
                   ['    "item.potato_s_t.lithium_concentrate":  "Литиевый концентрат",',
                    '    "item.potato_s_t.lithium_carbonate":  "Карбонат лития",']),
}

# 锚点 ③：粉碎机 tooltip —— 在「内部缓冲」前插一条锂配方；并把结尾那句补上"粗锂"
TOOLTIP_LINE = {
    "zh_cn.json": (r"\n内部缓冲 2500 FE",
                   r"\n· 粗锂 -> 2~4 锂矿精粉（12s，20 FE/t）\n内部缓冲 2500 FE"),
    "en_us.json": (r"\nInternal buffer: 2500 FE",
                   r"\n· Raw Lithium -> 2~4 Lithium Concentrate (12s, 20 FE/t)\nInternal buffer: 2500 FE"),
    "ja_jp.json": (r"\n内部バッファ：2500 FE",
                   r"\n· 粗リチウム -> リチウム精鉱 2~4 個（12秒、20 FE/t）\n内部バッファ：2500 FE"),
    "ru_ru.json": (r"\nВнутренний буфер: 2500 FE",
                   r"\n· Необработанный литий -> 2~4 литиевого концентрата (12 с, 20 FE/t)\nВнутренний буфер: 2500 FE"),
}

TOOLTIP_TAIL = {
    "zh_cn.json": ("（矿石与石英按 c: 通用标签匹配，别的 mod 的同类物品也认）",
                   "（矿石、粗锂与石英按 c: 通用标签匹配，别的 mod 的同类物品也认）"),
    "en_us.json": ("(Ores and quartz match by c: common tags, so other mods' equivalents work too)",
                   "(Ores, raw lithium and quartz match by c: common tags, so other mods' equivalents work too)"),
    "ja_jp.json": ("（鉱石とクォーツは c: 共通タグで判定するため、他 Mod の同等品も使えます）",
                   "（鉱石・粗リチウム・クォーツは c: 共通タグで判定するため、他 Mod の同等品も使えます）"),
    "ru_ru.json": ("(Руды и кварц определяются по общим тегам c:, поэтому аналоги из других модов тоже подходят)",
                   "(Руды, необработанный литий и кварц определяются по общим тегам c:, поэтому аналоги из других модов тоже подходят)"),
}


def patch_one(name, dry):
    path = os.path.join(LANG_DIR, name)
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()

    before = json.loads(text)
    if len(before) != EXPECTED_BEFORE:
        raise SystemExit("[FAIL] {0}：改前键数是 {1}，预期 {2} —— 先查清楚再动手".format(
            name, len(before), EXPECTED_BEFORE))

    # 机器用的是 CRLF：插入行必须跟着用 CRLF
    nl = "\r\n" if "\r\n" in text else "\n"

    for label, table in (("矿石/粗锂", ANCHOR_ORE_RAW), ("精粉/碳酸锂", ANCHOR_PRODUCTS)):
        anchor, new_lines = table[name]
        n = text.count(anchor)
        if n != 1:
            raise SystemExit("[FAIL] {0} 锚点「{1}」出现 {2} 次（要求恰好 1 次）".format(name, label, n))
        text = text.replace(anchor, anchor + nl + nl.join(new_lines))

    for label, table in (("tooltip 配方行", TOOLTIP_LINE), ("tooltip 结尾句", TOOLTIP_TAIL)):
        old, new = table[name]
        n = text.count(old)
        if n != 1:
            raise SystemExit("[FAIL] {0} {1} 出现 {2} 次（要求恰好 1 次）".format(name, label, n))
        text = text.replace(old, new)

    after = json.loads(text)
    if len(after) != EXPECTED_AFTER:
        raise SystemExit("[FAIL] {0}：改后键数是 {1}，预期 {2}".format(name, len(after), EXPECTED_AFTER))
    missing = set(before) - set(after)
    if missing:
        raise SystemExit("[FAIL] {0}：改完反而少了键 {1}".format(name, sorted(missing)))
    if "\n" in text.replace("\r\n", ""):
        raise SystemExit("[FAIL] {0}：出现了裸 LF，换行风格被破坏了".format(name))

    if dry:
        print("  [dry] {0}：{1} -> {2} 键".format(name, len(before), len(after)))
        return before, after

    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("  [写] {0}：{1} -> {2} 键".format(name, len(before), len(after)))
    return before, after


def main(argv):
    dry = "--dry" in argv
    print("== 给 4 个语言文件加锂条目 ==")
    sets = {}
    for name in ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"):
        _before, after = patch_one(name, dry)
        sets[name] = set(after)

    ref_name = "zh_cn.json"
    ref = sets[ref_name]
    bad = False
    for name, keys in sets.items():
        if keys != ref:
            bad = True
            print("[FAIL] {0} 与 {1} 键集合不一致：缺 {2} / 多 {3}".format(
                name, ref_name, sorted(ref - keys), sorted(keys - ref)))
    if bad:
        return 1
    print("")
    print("4 个语言文件键集合完全一致：{0} 键".format(len(ref)))
    new_keys = sorted(k for k in ref if "lithium" in k)
    print("本次新增的键：")
    for k in new_keys:
        print("    " + k)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
