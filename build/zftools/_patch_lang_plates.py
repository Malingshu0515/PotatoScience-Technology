# -*- coding: utf-8 -*-
"""_patch_lang_plates.py —— 给 4 个语言文件加 6 个板材键（0.10 ZF16）

**为什么又是脚本**：语言文件是 **CRLF**，edit 工具插入的新行只带 LF，会搞成混合换行（§4.8）。
脚本里同时带三道自检：锚点唯一、键数 116->122、键集合 4 语言一致，且**出现裸 LF 直接报错**。

跑法：
    python build/zftools/_patch_lang_plates.py --dry
    python build/zftools/_patch_lang_plates.py
"""
import io
import json
import os
import sys

LANG_DIR = os.path.join("E:\\PotatoST", "src", "main", "resources", "assets", "potato_s_t", "lang")
EXPECTED_BEFORE = 116
EXPECTED_AFTER = 122

# 锚点：锂那批的最后一个键（各语言不同）
ANCHOR = {
    "zh_cn.json": '    "item.potato_s_t.lithium_carbonate":  "碳酸锂",',
    "en_us.json": '    "item.potato_s_t.lithium_carbonate":  "Lithium Carbonate",',
    "ja_jp.json": '    "item.potato_s_t.lithium_carbonate":  "炭酸リチウム",',
    "ru_ru.json": '    "item.potato_s_t.lithium_carbonate":  "Карбонат лития",',
}

# 物品 id -> 各语言显示名（顺序即写入顺序）
NAMES = [
    ("iron_plate",     "铁板",   "Iron Plate",     "鉄板",           "Железная пластина"),
    ("nickel_plate",   "镍板",   "Nickel Plate",   "ニッケル板",       "Никелевая пластина"),
    ("cobalt_plate",   "钴板",   "Cobalt Plate",   "コバルト板",       "Кобальтовая пластина"),
    ("silver_plate",   "银板",   "Silver Plate",   "銀板",           "Серебряная пластина"),
    ("aluminum_plate", "铝板",   "Aluminum Plate", "アルミニウム板",   "Алюминиевая пластина"),
    ("steel_plate",    "钢板",   "Steel Plate",    "鋼板",           "Стальная пластина"),
]
COLS = {"zh_cn.json": 1, "en_us.json": 2, "ja_jp.json": 3, "ru_ru.json": 4}


def patch_one(name, dry):
    path = os.path.join(LANG_DIR, name)
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()

    before = json.loads(text)
    if len(before) != EXPECTED_BEFORE:
        raise SystemExit("[FAIL] {0}：改前 {1} 键，预期 {2}".format(name, len(before), EXPECTED_BEFORE))

    nl = "\r\n" if "\r\n" in text else "\n"
    anchor = ANCHOR[name]
    if text.count(anchor) != 1:
        raise SystemExit("[FAIL] {0}：锚点出现 {1} 次（要求 1）".format(name, text.count(anchor)))

    col = COLS[name]
    new_lines = []
    for row in NAMES:
        new_lines.append('    "item.potato_s_t.{0}":  "{1}",'.format(row[0], row[col]))
    # 锚点行**本身已经带尾逗号**（它不是对象最后一条），所以这里只补换行 + 新行，
    # 千万不能再补一个逗号 —— 那会拼出 `,,`，是第一版跑出来的错。
    # 新加的 6 行里**最后一行也要带逗号**，因为锚点后面本来还有 micro_crusher 等条目。
    text = text.replace(anchor, anchor + nl + nl.join(new_lines))

    after = json.loads(text)
    if len(after) != EXPECTED_AFTER:
        raise SystemExit("[FAIL] {0}：改后 {1} 键，预期 {2}".format(name, len(after), EXPECTED_AFTER))
    if set(before) - set(after):
        raise SystemExit("[FAIL] {0}：改完反而少了键".format(name))
    if "\n" in text.replace("\r\n", ""):
        raise SystemExit("[FAIL] {0}：出现裸 LF，换行风格被破坏".format(name))

    if dry:
        print("  [dry] {0}：{1} -> {2} 键".format(name, len(before), len(after)))
    else:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("  [写] {0}：{1} -> {2} 键".format(name, len(before), len(after)))
    return after


def main(argv):
    dry = "--dry" in argv
    print("== 给 4 个语言文件加板材键 ==")
    sets = {}
    for name in ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"):
        sets[name] = set(patch_one(name, dry))
    ref = sets["zh_cn.json"]
    bad = False
    for name, keys in sets.items():
        if keys != ref:
            bad = True
            print("[FAIL] {0} 与 zh_cn 键集合不一致：缺 {1} / 多 {2}".format(
                name, sorted(ref - keys), sorted(keys - ref)))
    if bad:
        return 1
    print("")
    print("4 个语言文件键集合完全一致：{0} 键".format(len(ref)))
    print("本次新增：")
    for row in NAMES:
        print("    item.potato_s_t.{0:<16} {1}".format(row[0], row[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
