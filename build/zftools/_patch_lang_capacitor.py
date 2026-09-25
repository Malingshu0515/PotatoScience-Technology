# -*- coding: utf-8 -*-
"""_patch_lang_capacitor.py —— 给 4 个语言文件加「电容」键（0.10 ZF21）

跑法：
    python build/zftools/_patch_lang_capacitor.py --dry
    python build/zftools/_patch_lang_capacitor.py
"""
import io
import json
import os
import sys

LANG_DIR = os.path.join("E:\\PotatoST", "src", "main", "resources", "assets", "potato_s_t", "lang")
EXPECTED_BEFORE = 129
EXPECTED_AFTER = 130

# 锚点 = 上一批（JEI）的最后一个键；它不是对象末条，所以自带尾逗号
ANCHOR = {
    "zh_cn.json": '    "gui.potato_s_t.jei.energy_per_tank":  "每罐耗电 %s FE/t",',
    "en_us.json": '    "gui.potato_s_t.jei.energy_per_tank":  "%s FE/t per tank",',
    "ja_jp.json": '    "gui.potato_s_t.jei.energy_per_tank":  "タンクごとに %s FE/t",',
    "ru_ru.json": '    "gui.potato_s_t.jei.energy_per_tank":  "%s FE/т на баллон",',
}

NEW_KEY = "item.potato_s_t.capacitor"
NAME = {
    "zh_cn.json": "电容",
    "en_us.json": "Capacitor",
    "ja_jp.json": "コンデンサ",
    "ru_ru.json": "Конденсатор",
}


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

    new_line = '    "{0}":  "{1}",'.format(NEW_KEY, NAME[name])
    # 锚点自带尾逗号 ⇒ 只补换行 + 新行（不能再补逗号，否则 ,, —— ZF16 踩过）
    text = text.replace(anchor, anchor + nl + new_line)

    after = json.loads(text)
    if len(after) != EXPECTED_AFTER:
        raise SystemExit("[FAIL] {0}：改后 {1} 键，预期 {2}".format(name, len(after), EXPECTED_AFTER))
    if set(before) - set(after):
        raise SystemExit("[FAIL] {0}：改完反而少了键".format(name))
    if "\n" in text.replace("\r\n", ""):
        raise SystemExit("[FAIL] {0}：出现裸 LF，换行风格被破坏".format(name))

    if dry:
        print("  [dry] {0}：{1} -> {2} 键  （{3}）".format(name, len(before), len(after), NAME[name]))
    else:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("  [写] {0}：{1} -> {2} 键  （{3}）".format(name, len(before), len(after), NAME[name]))
    return after


def main(argv):
    dry = "--dry" in argv
    print("== 给 4 个语言文件加「电容」= ==")
    sets = {}
    for name in ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"):
        sets[name] = set(patch_one(name, dry))
    ref = sets["zh_cn.json"]
    bad = [n for n, k in sets.items() if k != ref]
    if bad:
        for n in bad:
            print("[FAIL] {0} 与 zh_cn 键集合不一致".format(n))
        return 1
    print("")
    print("4 个语言文件键集合完全一致：{0} 键".format(len(ref)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
