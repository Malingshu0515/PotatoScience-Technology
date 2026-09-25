# -*- coding: utf-8 -*-
"""ZF44 只读复核（期望值独立再写一遍，见档案 §4.28）。"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "tooltip.potato_s_t.electric_blast_furnace"

EXPECT = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\n空手 Shift 右键原版高炉即可成型；手持扳手 Shift 右键可拆解。\n12 个输入槽、32 个输出槽，每个槽位 10 秒烧完。\n每件物品耗电 800 FE，储电 4096 FE，满载时约 3072 FE/t。\n除本模组的矿物处理外，高炉能烧的东西这里都能烧。",
    "en_us": u"Assembled from a 3x3x3 structure.\nShift-right-click a blast furnace with an empty hand to form it; hold a wrench and shift-right-click to take it apart.\n12 input slots and 32 output slots; each slot finishes in 10 seconds.\nEach item costs 800 FE, it stores 4096 FE, and a full load draws about 3072 FE/t.\nIt also handles everything a blast furnace can smelt.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\n素手でスニーク+右クリック（溶鉱炉）で組み立て、レンチを持ってスニーク+右クリックで解体できます。\n入力 12 スロット、出力 32 スロット。1 スロットは 10 秒で完成します。\nアイテム 1 個あたり 800 FE、蓄電 4096 FE、満載時は約 3072 FE/t を消費します。\n溶鉱炉で焼けるものはすべて扱えます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать; с гаечным ключом — чтобы разобрать.\n12 входных и 32 выходных слота; каждый слот обрабатывается 10 секунд.\nКаждый предмет стоит 800 FE, запас — 4096 FE, полная загрузка потребляет около 3072 FE/т.\nОбрабатывает всё, что умеет доменная печь.",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    raw = io.open(path, encoding="utf-8").read()
    got = json.loads(raw).get(KEY, "")
    check(got == EXPECT[code], "%s 说明逐字一致" % code)
    if got != EXPECT[code]:
        print("     实际: " + repr(got[:110]))
    check(got.count("\n") == 4, "%s 是 5 行" % code)
    check(u"800" in got and u"4096" in got and u"3072" in got, "%s 三个新数字都在" % code)
    check(u"320" not in got.replace(u"3072", u""), "%s 没有残留的旧数字 320" % code)
    line = [l for l in raw.split("\n") if ('"' + KEY + '"') in l]
    check(len(line) == 1 and line[0].count("\\n") == 4, "%s 文件里是 JSON 转义 \\n ×4" % code)

if fail:
    print("有 %d 项失败" % len(fail))
    sys.exit(1)
print("说明文案复核通过。")
