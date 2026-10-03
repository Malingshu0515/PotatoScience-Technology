# -*- coding: utf-8 -*-
"""ZF43 只读复核（期望值**在这里独立再写一遍**，不复用补丁脚本的变量 —— 见档案 §4.28）。"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "tooltip.potato_s_t.electric_blast_furnace"

EXPECT = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\n空手 Shift 右键原版高炉即可成型；手持扳手 Shift 右键可拆解。\n12 个输入槽、32 个输出槽，每个槽位 10 秒烧完。\n每件物品耗电 80 FE，储电 320 FE。\n除本模组的矿物处理外，高炉能烧的东西这里都能烧。",
    "en_us": u"Assembled from a 3x3x3 structure.\nShift-right-click a blast furnace with an empty hand to form it; hold a wrench and shift-right-click to take it apart.\n12 input slots and 32 output slots; each slot finishes in 10 seconds.\nEach item costs 80 FE, and it stores 320 FE.\nIt also handles everything a blast furnace can smelt.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\n素手でスニーク+右クリック（溶鉱炉）で組み立て、レンチを持ってスニーク+右クリックで解体できます。\n入力 12 スロット、出力 32 スロット。1 スロットは 10 秒で完成します。\nアイテム 1 個あたり 80 FE、蓄電は 320 FE です。\n溶鉱炉で焼けるものはすべて扱えます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать; с гаечным ключом — чтобы разобрать.\n12 входных и 32 выходных слота; каждый слот обрабатывается 10 секунд.\nКаждый предмет стоит 80 FE, запас — 320 FE.\nОбрабатывает всё, что умеет доменная печь.",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    raw = io.open(path, encoding="utf-8").read()
    data = json.loads(raw)
    got = data.get(KEY, "")
    check(got == EXPECT[code], "%s 说明逐字一致" % code)
    if got != EXPECT[code]:
        print("     实际: " + repr(got[:100]))
        print("     期望: " + repr(EXPECT[code][:100]))
    check(got.count("\n") == 4, "%s 是 5 行" % code)
    check(u"10" in got and u"320" in got, "%s 含新数字（10 秒 / 320 FE）" % code)
    check(u"4096" not in got and u"3 秒" not in got and u"3 seconds" not in got,
          "%s 旧数字已清干净" % code)
    line = [l for l in raw.split("\n") if ('"' + KEY + '"') in l]
    check(len(line) == 1 and line[0].count("\\n") == 4, "%s 文件里是 JSON 转义 \\n ×4" % code)

if fail:
    print("有 %d 项失败" % len(fail))
    sys.exit(1)
print("说明文案复核通过。")
