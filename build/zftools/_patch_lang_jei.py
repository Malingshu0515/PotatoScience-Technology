# -*- coding: utf-8 -*-
"""_patch_lang_jei.py —— 给 4 个语言文件加 JEI 说明行键（0.10 ZF19）

JEI 分类**标题**复用已有的 `block.potato_s_t.<机器id>`，不新增键；
这里只加配方下方那几行说明 + 分类里用到的量词。

跑法：
    python build/zftools/_patch_lang_jei.py --dry
    python build/zftools/_patch_lang_jei.py
"""
import io
import json
import os
import sys

LANG_DIR = os.path.join("E:\\PotatoST", "src", "main", "resources", "assets", "potato_s_t", "lang")
EXPECTED_BEFORE = 122
EXPECTED_AFTER = 129

# 锚点 = 板材那批的最后一个键（它不是对象末条，所以自带尾逗号）
ANCHOR = {
    "zh_cn.json": '    "item.potato_s_t.steel_plate":  "钢板",',
    "en_us.json": '    "item.potato_s_t.steel_plate":  "Steel Plate",',
    "ja_jp.json": '    "item.potato_s_t.steel_plate":  "鋼板",',
    "ru_ru.json": '    "item.potato_s_t.steel_plate":  "Стальная пластина",',
}

# 键 -> (zh, en, ja, ru)；占位符签名必须 4 语言一致（LangCheck 会核对）
KEYS = [
    ("time",            "耗时：%s 秒",           "Time: %s s",                     "所要時間：%s 秒",                    "Время: %s с"),
    ("energy",          "耗电：%s FE/t",         "Energy: %s FE/t",                "電力：%s FE/t",                     "Энергия: %s FE/т"),
    ("range",           "产出 %s~%s 个",         "Output %s~%s",                   "産出 %s~%s 個",                     "Выход %s~%s шт."),
    ("continuous",      "每 tick 持续产出",      "Produced continuously every tick", "毎 tick 継続的に産出",             "Производится непрерывно каждый тик"),
    ("passive",         "不需要电，但很慢",      "No power needed, but slow",      "電力不要だが遅い",                   "Без энергии, но медленно"),
    ("per_salt",        "每 %s mB 水消耗 1 个海盐", "Consumes 1 Sea Salt per %s mB of water", "%s mB の水ごとに海塩 1 個を消費", "Расходует 1 морскую соль на каждые %s mB воды"),
    ("energy_per_tank", "每罐耗电 %s FE/t",      "%s FE/t per tank",               "タンクごとに %s FE/t",               "%s FE/т на баллон"),
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
    for row in KEYS:
        new_lines.append('    "gui.potato_s_t.jei.{0}":  "{1}",'.format(row[0], row[col]))
    # 锚点自带尾逗号 ⇒ 只补换行 + 新行（不能再补逗号，否则拼出 ,, —— ZF16 踩过）
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
    print("== 给 4 个语言文件加 JEI 说明行键 ==")
    sets = {}
    for name in ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"):
        sets[name] = set(patch_one(name, dry))
    ref = sets["zh_cn.json"]
    bad = False
    for name, keys in sets.items():
        if keys != ref:
            bad = True
            print("[FAIL] {0} 键集合与 zh_cn 不一致：缺 {1}".format(name, sorted(ref - keys)))
    if bad:
        return 1
    print("")
    print("4 个语言文件键集合完全一致：{0} 键".format(len(ref)))
    print("本次新增：")
    for key, *rest in KEYS:
        print("    gui.potato_s_t.jei.{0:<16} {1}".format(key, rest[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
