# -*- coding: utf-8 -*-
"""_zf51_lang.py —— ZF51：把"合金冶炼炉"改成"合金炉主控"（匠魂那种控制器）

用户原话：「合金炉主控需要激活多方块结构才可以使用 而不是直接为合金冶炼炉
  类似于匠魂 他只是个控制器 需要先激活他」

改动：
  ① `block.potato_s_t.alloy_smelter`：合金冶炼炉 → **合金炉主控**（方块物品名 / Jade 都读它）
  ② 新增 `gui.potato_s_t.alloy_smelter.name`：**合金冶炼炉**（激活之后的界面标题）
  ③ 新增 `gui.potato_s_t.alloy_smelter.status`：Shift 右键的状态行（2 个 %s）
  ④ `gui...formed` 文案：已成型 → **已激活**（匠魂的说法）
  ⑤ `block...alloy_smelter_port`：合金冶炼炉接线口 → 合金炉接线口（与主控对齐）
  ⑥ tooltip 重写：先说"这只是控制器，要先激活"
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
CODES = tuple(sys.argv[1:]) or ALL_CODES

RENAME = [
    ("block.potato_s_t.alloy_smelter", {
        "zh_cn": u"合金炉主控", "en_us": u"Alloy Smelter Controller",
        "ja_jp": u"合金精錬炉コントローラー", "ru_ru": u"Контроллер плавильни сплавов"}),
    ("block.potato_s_t.alloy_smelter_port", {
        "zh_cn": u"合金炉接线口", "en_us": u"Alloy Smelter Power Port",
        "ja_jp": u"合金精錬炉の接続口", "ru_ru": u"Порт питания плавильни сплавов"}),
    ("gui.potato_s_t.alloy_smelter.formed", {
        "zh_cn": u"合金冶炼炉已激活", "en_us": u"Alloy Smelter activated",
        "ja_jp": u"合金精錬炉を起動しました", "ru_ru": u"Плавильня сплавов активирована"}),
    ("tooltip.potato_s_t.alloy_smelter", {
        "zh_cn": u"这只是一个控制器，本身不是炉子。\\n空手右键激活多方块结构（结构不完整会告诉你哪一格不对）；激活之后右键才打开界面。\\n结构：4 层 × 5 排 × 4 列，控制器摆在正面最左那一格（原图纸那里是标靶）。\\n激活后：5 个输入槽只收锭、3 个输出槽、2 个消耗槽（暂时放不了东西），储能 32768 FE。\\n电只从那两处接线口进。手持扳手 Shift 右键拆解。\\n配方尚未加入。",
        "en_us": u"This is only a controller, not the furnace itself.\\nRight-click with an empty hand to activate the multiblock (it tells you which cell is wrong); only after activation does right-click open the GUI.\\nStructure: 4 layers x 5 x 4; the controller sits at the front-left cell (where the drawing had a target block).\\nOnce active: 5 input slots that only accept ingots, 3 output slots, 2 consumable slots (not usable yet), 32768 FE storage.\\nPower only enters through the two power ports. Hold a wrench and shift-right-click to take it apart.\\nNo recipes yet.",
        "ja_jp": u"これはコントローラーであり、炉そのものではありません。\\n素手で右クリックしてマルチブロックを起動します（不完全ならどのマスが違うか表示されます）。起動後に右クリックで画面が開きます。\\n構造：4 層 × 5 × 4。コントローラーは正面左端のマス（図面では的ブロックだった場所）。\\n起動後：入力 5（インゴットのみ）、出力 3、消費 2（現在は使えません）、蓄電 32768 FE。\\n電力は 2 か所の接続口からのみ入ります。レンチでスニーク+右クリックすると解体できます。\\nレシピは未実装です。",
        "ru_ru": u"Это только контроллер, а не сама печь.\\nЩёлкните правой кнопкой пустой рукой, чтобы активировать конструкцию (она подскажет, какая ячейка неверна); интерфейс откроется только после активации.\\nКонструкция: 4 слоя × 5 × 4; контроллер стоит в передней левой ячейке (в чертеже там был блок-мишень).\\nПосле активации: 5 входных слотов только для слитков, 3 выходных, 2 расходных (пока недоступны), запас 32768 FE.\\nЭнергия подаётся только через два порта питания. С гаечным ключом и присев — разобрать.\\nРецептов пока нет."}),
]

NEW_KEYS = [
    ("gui.potato_s_t.alloy_smelter.name", {
        "zh_cn": u"合金冶炼炉", "en_us": u"Alloy Smelter", "ja_jp": u"合金精錬炉",
        "ru_ru": u"Плавильня сплавов"}),
    ("gui.potato_s_t.alloy_smelter.status", {
        "zh_cn": u"合金冶炼炉已激活：储能 %s / %s FE",
        "en_us": u"Alloy Smelter active: %s / %s FE",
        "ja_jp": u"合金精錬炉 起動中：蓄電 %s / %s FE",
        "ru_ru": u"Плавильня сплавов активна: %s / %s FE"}),
]


def set_line(lines, key, value):
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + key + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (key, value, "," if l.rstrip().endswith(",") else "")
            hit += 1
    if hit != 1:
        raise SystemExit(u"%s: 找到 %d 处（应为 1）" % (key, hit))


for code in CODES:
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    lines = text.split("\n")
    for key, table in RENAME:
        set_line(lines, key, table[code])
    text = "\n".join(lines)

    todo = [(k, t) for k, t in NEW_KEYS if ('"' + k + '"') not in text]
    if todo:
        lines = text.split("\n")
        last = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('"'):
                last = i
                break
        if last is None:
            raise SystemExit(u"%s: 找不到最后一个键行" % code)
        if not lines[last].rstrip().endswith(","):
            lines[last] = lines[last].rstrip() + ","
        add = [u'    "%s":  "%s",' % (k, t[code]) for k, t in todo]
        add[-1] = add[-1][:-1]
        lines[last + 1:last + 1] = add
        text = "\n".join(lines)

    after = json.loads(text)
    if len(after) != len(before) + len(todo):
        raise SystemExit(u"%s: 键数 %d -> %d（应加 %d）" % (code, len(before), len(after), len(todo)))
    # ⚠ 期望值按**解析后**的类型比（§4.28）
    for key, table in RENAME:
        if after[key] != table[code].replace(u"\\n", u"\n"):
            raise SystemExit(u"%s: %s 没改对 = %r" % (code, key, after[key]))
    for k, t in todo:
        if after[k] != t[code].replace(u"\\n", u"\n"):
            raise SystemExit(u"%s: %s = %r" % (code, k, after[k]))
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s: %d 键；主控名 = %s" % (code, len(after), after["block.potato_s_t.alloy_smelter"]))

print(u"改完。")
