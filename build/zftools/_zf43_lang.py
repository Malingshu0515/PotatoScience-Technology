# -*- coding: utf-8 -*-
"""ZF43：电力高炉 Shift 说明改成 10 秒 / 320 FE / 支持原版高炉配方。
（按 §4.28：本脚本只负责改；复核另用 _zf43_verify.py，期望值在那里独立再写一遍。）
"""
import io
import json
import os

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "tooltip.potato_s_t.electric_blast_furnace"

NEW = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\\n空手 Shift 右键原版高炉即可成型；手持扳手 Shift 右键可拆解。\\n12 个输入槽、32 个输出槽，每个槽位 10 秒烧完。\\n每件物品耗电 80 FE，储电 320 FE。\\n除本模组的矿物处理外，高炉能烧的东西这里都能烧。",
    "en_us": u"Assembled from a 3x3x3 structure.\\nShift-right-click a blast furnace with an empty hand to form it; hold a wrench and shift-right-click to take it apart.\\n12 input slots and 32 output slots; each slot finishes in 10 seconds.\\nEach item costs 80 FE, and it stores 320 FE.\\nIt also handles everything a blast furnace can smelt.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\\n素手でスニーク+右クリック（溶鉱炉）で組み立て、レンチを持ってスニーク+右クリックで解体できます。\\n入力 12 スロット、出力 32 スロット。1 スロットは 10 秒で完成します。\\nアイテム 1 個あたり 80 FE、蓄電は 320 FE です。\\n溶鉱炉で焼けるものはすべて扱えます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать; с гаечным ключом — чтобы разобрать.\\n12 входных и 32 выходных слота; каждый слот обрабатывается 10 секунд.\\nКаждый предмет стоит 80 FE, запас — 320 FE.\\nОбрабатывает всё, что умеет доменная печь.",
}

for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    json.loads(text)                      # 改前必须合法
    lines = text.split("\n")
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + KEY + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (KEY, NEW[code], "," if l.rstrip().endswith(",") else "")
            hit += 1
    if hit != 1:
        raise SystemExit("%s: 找到 %d 处，停" % (code, hit))
    out = "\n".join(lines)
    after = json.loads(out)               # 写前必须合法
    assert after[KEY].count("\n") == 4, code
    assert u"10 秒" in after[KEY] or u"10 seconds" in after[KEY] or u"10 秒" in after[KEY] or u"10 секунд" in after[KEY], code
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("[OK] %s 已更新" % code)
print("改完，请跑 _zf43_verify.py 复核。")
