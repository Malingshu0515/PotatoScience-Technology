# -*- coding: utf-8 -*-
"""_zf53b_lang.py —— 报错文案再加"坐标"（用户截图里那行还是旧文案，说明还没装上上一版）

`gui.potato_s_t.alloy_smelter.invalid` 现在是 8 个 %s：
  第 %s 层 第 %s 排 第 %s 格应为 %s，现在是 %s（坐标 %s %s %s）
"""
import io
import json
import os

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "gui.potato_s_t.alloy_smelter.invalid"

NEW = {
    "zh_cn": u"结构不成立：第 %s 层 第 %s 排 第 %s 格应为 %s，现在是 %s（坐标 %s %s %s）",
    "en_us": u"Structure incomplete: layer %s, row %s, column %s should be %s but is %s (at %s %s %s)",
    "ja_jp": u"構造が不完全：%s 層 %s 列目 %s 番目は %s であるべきですが %s です（座標 %s %s %s）",
    "ru_ru": u"Конструкция неполная: слой %s, ряд %s, столбец %s — ожидается %s, а стоит %s (координаты %s %s %s)",
}

for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + KEY + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (KEY, NEW[code], "," if l.rstrip().endswith(",") else "")
            hit += 1
    if hit != 1:
        raise SystemExit(u"%s: 找到 %d 处" % (code, hit))
    text = "\n".join(lines)
    after = json.loads(text)
    if after[KEY].count("%s") != 8:
        raise SystemExit(u"%s: %%s 个数 = %d（应为 8）" % (code, after[KEY].count("%s")))
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s" % code)
print(u"改完。")
