# -*- coding: utf-8 -*-
"""ZF42 只读复核：确认 4 个语言里的新说明**真的是新内容**。

⚠ 上一版 `_zf42_lang.py` 的断言又写错了（和 ZF38 同款）：
   我把"期望值"写成 Python 字面量 `u"...\\n..."`（= 反斜杠+n 两个字符），
   可 `json.loads` 早就把它还原成**真换行**了 ⇒ `==` 永远不成立、`count("\\n")` 恒为 0。
   数据本身是对的（写盘前 `json.loads` 校验通过、且 320 已经不在文案里），错的是断言。
   这条已经第二次栽，值得单独记进档案。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = "tooltip.potato_s_t.electric_blast_furnace"

EXPECT = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\n空手 Shift 右键原版高炉即可成型；手持扳手 Shift 右键可拆解。\n12 个输入槽、32 个输出槽，每个槽位 3 秒烧完。\n每件物品耗电 80 FE，12 槽塞满时约 1024 FE/t。\n储电 4096 FE，产物会自动送进紧邻的容器。",
    "en_us": u"Assembled from a 3x3x3 structure.\nShift-right-click a blast furnace with an empty hand to form it; hold a wrench and shift-right-click to take it apart.\n12 input slots and 32 output slots; each slot finishes in 3 seconds.\nEach item costs 80 FE, and a fully loaded furnace draws about 1024 FE/t.\nStores 4096 FE, and output is pushed into adjacent containers.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\n素手でスニーク+右クリック（溶鉱炉）で組み立て、レンチを持ってスニーク+右クリックで解体できます。\n入力 12 スロット、出力 32 スロット。1 スロットは 3 秒で完成します。\nアイテム 1 個あたり 80 FE、12 スロット満載で約 1024 FE/t を消費します。\n蓄電 4096 FE、産物は隣接するコンテナへ自動搬出されます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать; с гаечным ключом — чтобы разобрать.\n12 входных и 32 выходных слота; каждый слот обрабатывается 3 секунды.\nКаждый предмет стоит 80 FE; полностью загруженная печь потребляет около 1024 FE/т.\nХранит 4096 FE, продукция отправляется в соседние контейнеры.",
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
    check(got == EXPECT[code], "%s 说明内容与预期逐字一致" % code)
    if got != EXPECT[code]:
        print("     实际: " + repr(got[:120]))
        print("     期望: " + repr(EXPECT[code][:120]))
    check(got.count("\n") == 4, "%s 是 5 行（真换行 4 个）" % code)
    check(u"4096" in got and u"320" not in got, "%s 数字已更新（4096 在、320 不在）" % code)
    check(u"扳手" in got or u"wrench" in got or u"レンチ" in got or u"ключ" in got,
          "%s 提到了扳手（拆解方式改了）" % code)
    line = [l for l in raw.split("\n") if ('"' + KEY + '"') in l]
    check(len(line) == 1 and "\\n" in line[0] and line[0].count("\\n") == 4,
          "%s 文件里是 JSON 转义 \\n ×4（单行合法 JSON）" % code)

if fail:
    print("有 %d 项失败" % len(fail))
    sys.exit(1)
print("说明文案复核通过。")
