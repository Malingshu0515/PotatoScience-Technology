# -*- coding: utf-8 -*-
"""_patch_lang_solar.py —— 给 4 个语言文件加「太阳能板」相关键（0.10 ZF22）

9 个键：方块名 / 物品 tooltip / 2 条状态消息 / 6 个状态词。
⚠ 占位符数量各语言必须一致（LangCheck 会核对签名）：
   solar_status 2 个 %s，solar_detail 4 个 %s，其余无。

跑法：
    python build/zftools/_patch_lang_solar.py --dry
    python build/zftools/_patch_lang_solar.py
"""
import io
import json
import os
import sys

LANG_DIR = os.path.join("E:\\PotatoST", "src", "main", "resources", "assets", "potato_s_t", "lang")
EXPECTED_BEFORE = 130
EXPECTED_AFTER = 140

ANCHOR = {
    "zh_cn.json": '    "item.potato_s_t.capacitor":  "电容",',
    "en_us.json": '    "item.potato_s_t.capacitor":  "Capacitor",',
    "ja_jp.json": '    "item.potato_s_t.capacitor":  "コンデンサ",',
    "ru_ru.json": '    "item.potato_s_t.capacitor":  "Конденсатор",',
}

# 键 -> (zh, en, ja, ru)
KEYS = [
    ("block.potato_s_t.solar_panel",
     "太阳能板", "Solar Panel", "ソーラーパネル", "Солнечная панель"),

    ("tooltip.potato_s_t.solar_panel",
     "只在白天发电：日出/傍晚 20、上午/下午 45、正午 60 FE/t\\n雨天为其 60%、雷暴为其 20%\\n正上方必须是空气或无色玻璃（染色玻璃、遮光玻璃都不行）\\n自身储能 512 FE，会自动供电给正下方的设备\\n水平相邻的太阳能板自动并联，共享发电量（不共享储能）\\nShift+右键 查看并联数量与总发电量",
     "Generates only in daytime: dawn/dusk 20, morning/afternoon 45, noon 60 FE/t\\nRain 60% of that, thunder 20%\\nThe block above must be air or colorless glass (stained and tinted glass do not count)\\nStores 512 FE and feeds the block directly below\\nHorizontally adjacent panels connect in parallel and share generation (not storage)\\nShift+Right-click to see the panel count and total output",
     "昼のみ発電：夜明け/夕方 20、午前/午後 45、正午 60 FE/t\\n雨はその 60%、雷雨は 20%\\n真上は空気か無色ガラスであること（色付き・遮光ガラスは不可）\\n蓄電 512 FE、真下の装置へ自動給電\\n水平に隣接するパネルは並列接続し発電量を共有（蓄電は共有しない）\\nShift+右クリックで枚数と総発電量を表示",
     "Работает только днём: рассвет/закат 20, утро/полдень 45, полдень 60 FE/т\\nДождь — 60% от этого, гроза — 20%\\nСверху должен быть воздух или бесцветное стекло (цветное и тонированное не годятся)\\nХранит 512 FE и питает блок прямо под собой\\nПанели в ряд соединяются параллельно и делят выработку (не запас)\\nShift+ПКМ — число панелей и общая выработка"),

    ("message.potato_s_t.solar_status",
     "太阳能板并联：%s 块，总发电 %s FE/t",
     "Solar panels: %s connected, total %s FE/t",
     "ソーラーパネル：%s 枚並列、総発電 %s FE/t",
     "Солнечные панели: %s шт. в цепи, всего %s FE/т"),

    ("message.potato_s_t.solar_detail",
     "本块分到 %s FE/t，储能 %s / %s FE，状态：%s",
     "This panel gets %s FE/t, buffer %s / %s FE, status: %s",
     "このパネルは %s FE/t、蓄電 %s / %s FE、状態：%s",
     "Панель получает %s FE/т, буфер %s / %s FE, состояние: %s"),

    ("message.potato_s_t.solar.state.clear", "晴天", "clear", "晴れ", "ясно"),
    ("message.potato_s_t.solar.state.rain", "雨天（发电量 60%）", "rain (60%)", "雨（60%）", "дождь (60%)"),
    ("message.potato_s_t.solar.state.thunder", "雷暴（发电量 20%）", "thunder (20%)", "雷雨（20%）", "гроза (20%)"),
    ("message.potato_s_t.solar.state.night", "夜间不发电", "night (no output)", "夜間は発電なし", "ночь (нет выработки)"),
    ("message.potato_s_t.solar.state.blocked", "上方被遮挡", "blocked above", "上方が遮られている", "сверху перекрыто"),
    ("message.potato_s_t.solar.state.dimension", "此维度没有阳光", "no sunlight in this dimension", "この次元に日光はない", "в этом измерении нет солнца"),
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
    new_lines = ['    "{0}":  "{1}",'.format(row[0], row[col]) for row in KEYS]
    # 锚点自带尾逗号 ⇒ 只补换行 + 新行（不能再补逗号，否则 ,,）
    text = text.replace(anchor, anchor + nl + nl.join(new_lines))

    after = json.loads(text)
    if len(after) != EXPECTED_AFTER:
        raise SystemExit("[FAIL] {0}：改后 {1} 键，预期 {2}".format(name, len(after), EXPECTED_AFTER))
    if set(before) - set(after):
        raise SystemExit("[FAIL] {0}：改完反而少了键".format(name))
    if "\n" in text.replace("\r\n", ""):
        raise SystemExit("[FAIL] {0}：出现裸 LF，换行风格被破坏".format(name))

    # 占位符签名自检（%s 的个数必须 4 语言一致）
    sig = {}
    for key, value in after.items():
        if key.startswith(("message.potato_s_t.solar", "tooltip.potato_s_t.solar")):
            sig[key] = value.count("%s")
    if dry:
        print("  [dry] {0}：{1} -> {2} 键   占位符 {3}".format(name, len(before), len(after), sig))
    else:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("  [写] {0}：{1} -> {2} 键   占位符 {3}".format(name, len(before), len(after), sig))
    return after


def main(argv):
    dry = "--dry" in argv
    print("== 给 4 个语言文件加太阳能板键 ==")
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
