# -*- coding: utf-8 -*-
"""_zf52_lang.py —— 把合金炉主控的介绍改成**摆放方式**（用户：「合金冶炼炉控制器介绍改成合金炉摆放方式」）

设计要点：
  ① 用**数字记法**（用户自己提的：「以后配方太麻烦了 我用数字代替 例如【一般金属块】=【1】」）
     ⇒ 0 空 / 1 一般金属块 / 2 加热装置 / 3 耐热金属块 / 4 接线块 / 5 高炉 / 6 主控 / 7 漏斗 /
       8 炼药锅 / 9 散热装置
  ② 四层**两列并排**、用 `|` 当列分隔（不并排就是 20 行，工具提示太长；`|` 也让复核脚本好切）
  ③ 图纸数字必须与 `AlloySmelterStructure.LAYERS` **逐格一致** —— 由 `_zf52_verify.py` 核对
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
CODES = tuple(sys.argv[1:]) or ALL_CODES

KEY = "tooltip.potato_s_t.alloy_smelter"

# 摆放图：四层 × 五行 × 四列，两列并排；`0` = 空
GRID = [
    (u"第1层（底）", u"第2层", ["1111", "1221", "1221", "1221", "1111"],
     ["4334", "5005", "5005", "5005", "6337"]),
    (u"第3层", u"第4层（顶）", ["3333", "3003", "3003", "3003", "8339"],
     ["0330", "3003", "3003", "3003", "3003"]),
]

NEW = {
    "zh_cn": {
        "title": u"合金炉摆放方式（控制器＝主控，摆在原图纸【标靶】那一格）",
        "legend1": u"1 一般金属块  2 加热装置  3 耐热金属块  4 接线块  5 高炉",
        "legend2": u"6 主控  7 漏斗  8 炼药锅  9 散热装置  0 空",
        "foot": u"空手右键激活（哪一格不对会说）；激活后右键才开界面。5 输入只收锭 / 3 输出 / 2 消耗槽，储能 32768 FE，电只从接线口进。",
    },
    "en_us": {
        "title": u"Alloy Smelter layout (the controller goes where the drawing had the target block)",
        "legend1": u"1 common metal block  2 heater  3 heat-resistant block  4 wiring block  5 blast furnace",
        "legend2": u"6 controller  7 hopper  8 cauldron  9 heat sink  0 empty",
        "foot": u"Right-click with an empty hand to activate (it names the wrong cell); only then does right-click open the GUI. 5 inputs (ingots only) / 3 outputs / 2 consumable slots, 32768 FE, power enters through the ports only.",
    },
    "ja_jp": {
        "title": u"合金精錬炉の配置（コントローラーは図面の的ブロックの位置）",
        "legend1": u"1 一般金属ブロック  2 加熱装置  3 耐熱金属ブロック  4 接続ブロック  5 溶鉱炉",
        "legend2": u"6 コントローラー  7 ホッパー  8 大釜  9 放熱器  0 空",
        "foot": u"素手で右クリックして起動（違うマスを教えてくれます）。起動後に右クリックで画面が開きます。入力 5（インゴットのみ）/ 出力 3 / 消費 2、蓄電 32768 FE、電力は接続口からのみ。",
    },
    "ru_ru": {
        "title": u"Схема плавильни сплавов (контроллер — там, где в чертеже блок-мишень)",
        "legend1": u"1 блок обычного металла  2 нагреватель  3 теплостойкий блок  4 блок проводки  5 доменная печь",
        "legend2": u"6 контроллер  7 воронка  8 котёл  9 радиатор  0 пусто",
        "foot": u"Щёлкните правой кнопкой пустой рукой для активации (она назовёт неверную ячейку); интерфейс откроется только после этого. 5 входов (только слитки) / 3 выхода / 2 расходных слота, 32768 FE, энергия только через порты.",
    },
}

for code in CODES:
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    t = NEW[code]
    lines = [t["title"], t["legend1"], t["legend2"]]
    for left, right, lrows, rrows in GRID:
        lines.append(u"{0}|{1}".format(left, right))
        for a, b in zip(lrows, rrows):
            lines.append(u"{0}|{1}".format(a, b))
    lines.append(t["foot"])
    value = u"\\n".join(lines)          # 文件里存成 JSON 转义
    hit = 0
    src = text.split("\n")
    for i, l in enumerate(src):
        if ('"' + KEY + '"') in l:
            src[i] = u'    "%s":  "%s"%s' % (KEY, value, "," if l.rstrip().endswith(",") else "")
            hit += 1
    if hit != 1:
        raise SystemExit(u"%s: %s 找到 %d 处" % (code, KEY, hit))
    text = "\n".join(src)
    after = json.loads(text)
    if after[KEY].count("\n") != len(lines) - 1:
        raise SystemExit(u"%s: 行数 %d != %d" % (code, after[KEY].count("\n") + 1, len(lines)))
    if u"1111|4334" not in after[KEY]:
        raise SystemExit(u"%s: 摆放图没写进去" % code)
    if u"8339" not in after[KEY] or u"0330" not in after[KEY]:
        raise SystemExit(u"%s: 第三/四层的图不对" % code)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s：介绍改成 %d 行摆放图" % (code, len(lines)))

print(u"改完，跑 _zf52_verify.py 核对（图纸数字必须与 AlloySmelterStructure 逐格一致）。")
