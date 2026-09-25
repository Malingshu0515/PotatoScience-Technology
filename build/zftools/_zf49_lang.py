# -*- coding: utf-8 -*-
"""_zf49_lang.py —— ZF49 四语言新增 7 个键（合金冶炼炉）

只追加、不重排、幂等（与 ZF45/46/48 同一套做法）。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
CODES = tuple(sys.argv[1:]) or ALL_CODES

NEW_KEYS = [
    ("block.potato_s_t.alloy_smelter", {
        "zh_cn": u"合金冶炼炉", "en_us": u"Alloy Smelter", "ja_jp": u"合金精錬炉",
        "ru_ru": u"Плавильня сплавов"}),
    ("block.potato_s_t.alloy_smelter_port", {
        "zh_cn": u"合金冶炼炉接线口", "en_us": u"Alloy Smelter Power Port",
        "ja_jp": u"合金精錬炉の接続口", "ru_ru": u"Порт питания плавильни"}),
    ("tooltip.potato_s_t.alloy_smelter", {
        "zh_cn": u"用 4 层 × 5 排 × 4 列的结构装配而成（控制器摆在正面最左那一格，原图纸那里是标靶）。\\n空手 Shift 右键成型；成型后右键打开界面；手持扳手 Shift 右键拆解。\\n5 个输入槽只收锭、3 个输出槽、2 个消耗槽（暂时放不了东西）。\\n储能 32768 FE，电只能从那两处接线口进。\\n配方尚未加入。",
        "en_us": u"Assembled from a 4-layer, 5-by-4 structure (the controller sits at the front-left cell, where the drawing had a target block).\\nShift-right-click with an empty hand to form it; right-click to open the GUI; hold a wrench and shift-right-click to take it apart.\\n5 input slots that only accept ingots, 3 output slots and 2 consumable slots (not usable yet).\\nStores 32768 FE; power can only enter through the two power ports.\\nNo recipes yet.",
        "ja_jp": u"4 層 × 5 × 4 の構造物から組み上げます（コントローラーは正面左端のマス。図面では的ブロックだった場所）。\\n素手でスニーク+右クリックで組み立て、右クリックで画面を開き、レンチでスニーク+右クリックで解体します。\\n入力 5 スロットはインゴットのみ、出力 3 スロット、消費スロット 2 つ（現在は使えません）。\\n蓄電 32768 FE。電力は 2 か所の接続口からのみ入ります。\\nレシピは未実装です。",
        "ru_ru": u"Собирается из конструкции 4 слоя × 5 × 4 (контроллер стоит в передней левой ячейке — в чертеже там был блок-мишень).\\nПрисядьте и щёлкните правой кнопкой пустой рукой, чтобы собрать; правой кнопкой — открыть интерфейс; с гаечным ключом и присев — разобрать.\\n5 входных слотов только для слитков, 3 выходных и 2 расходных слота (пока недоступны).\\nХранит 32768 FE; энергия подаётся только через два порта питания.\\nРецептов пока нет."}),
    ("gui.potato_s_t.alloy_smelter.invalid", {
        "zh_cn": u"结构不成立：第 %s 层 第 %s 排 第 %s 格应为 %s",
        "en_us": u"Structure incomplete: layer %s, row %s, column %s should be %s",
        "ja_jp": u"構造が不完全：%s 層 %s 列目 %s 番目は %s であるべきです",
        "ru_ru": u"Конструкция неполная: слой %s, ряд %s, столбец %s должен быть %s"}),
    ("gui.potato_s_t.alloy_smelter.formed", {
        "zh_cn": u"合金冶炼炉已成型", "en_us": u"Alloy Smelter formed",
        "ja_jp": u"合金精錬炉が完成しました", "ru_ru": u"Плавильня сплавов собрана"}),
    ("gui.potato_s_t.alloy_smelter.consume_slot", {
        "zh_cn": u"消耗槽（暂未开放）", "en_us": u"Consumable slot (not yet usable)",
        "ja_jp": u"消費スロット（未開放）", "ru_ru": u"Расходный слот (пока недоступен)"}),
    ("gui.potato_s_t.alloy_smelter.input_hint", {
        "zh_cn": u"输入槽只收锭", "en_us": u"Input slots accept ingots only",
        "ja_jp": u"入力スロットはインゴットのみ", "ru_ru": u"Входные слоты принимают только слитки"}),
]

for code in CODES:
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    todo = [(k, t) for k, t in NEW_KEYS if ('"' + k + '"') not in text]
    if not todo:
        print(u"[跳过] %s：%d 个键都已在（%d 键）" % (code, len(NEW_KEYS), len(before)))
        continue
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
    for k, t in todo:
        # ⚠ 期望值要按**解析后**的类型比（§4.28 那个坑，已经栽过三次）：
        #   表里的 `\\n` 是文件里的两个字符，json.loads 之后是一个真换行。
        want = t[code].replace(u"\\n", u"\n")
        if after[k] != want:
            raise SystemExit(u"%s: %s = %r" % (code, k, after[k]))
    # 占位符签名四语言必须一致（LangCheck 会查，这里先自己拦一道）
    if after["gui.potato_s_t.alloy_smelter.invalid"].count("%s") != 4:
        raise SystemExit(u"%s: invalid 文案的 %%s 不是 4 个" % code)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s: %d -> %d 键" % (code, len(before), len(after)))

print(u"改完。")
