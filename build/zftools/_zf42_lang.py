# -*- coding: utf-8 -*-
"""ZF42：把电力高炉的 Shift 说明改成新的数值与扳手操作。"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

NEW = {
    "zh_cn": u"用 3×3×3 的结构装配而成。\\n空手 Shift 右键原版高炉即可成型；手持扳手 Shift 右键可拆解。\\n12 个输入槽、32 个输出槽，每个槽位 3 秒烧完。\\n每件物品耗电 80 FE，12 槽塞满时约 1024 FE/t。\\n储电 4096 FE，产物会自动送进紧邻的容器。",
    "en_us": u"Assembled from a 3x3x3 structure.\\nShift-right-click a blast furnace with an empty hand to form it; hold a wrench and shift-right-click to take it apart.\\n12 input slots and 32 output slots; each slot finishes in 3 seconds.\\nEach item costs 80 FE, and a fully loaded furnace draws about 1024 FE/t.\\nStores 4096 FE, and output is pushed into adjacent containers.",
    "ja_jp": u"3×3×3 の構造物から組み上げます。\\n素手でスニーク+右クリック（溶鉱炉）で組み立て、レンチを持ってスニーク+右クリックで解体できます。\\n入力 12 スロット、出力 32 スロット。1 スロットは 3 秒で完成します。\\nアイテム 1 個あたり 80 FE、12 スロット満載で約 1024 FE/t を消費します。\\n蓄電 4096 FE、産物は隣接するコンテナへ自動搬出されます。",
    "ru_ru": u"Собирается из конструкции 3×3×3.\\nПрисядьте и щёлкните правой кнопкой по доменной печи пустой рукой, чтобы собрать; с гаечным ключом — чтобы разобрать.\\n12 входных и 32 выходных слота; каждый слот обрабатывается 3 секунды.\\nКаждый предмет стоит 80 FE; полностью загруженная печь потребляет около 1024 FE/т.\\nХранит 4096 FE, продукция отправляется в соседние контейнеры.",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


key = "tooltip.potato_s_t.electric_blast_furnace"
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    old = before.get(key, "")
    if old == NEW[code]:
        check(True, "%s 已经是新文案" % code)
        continue
    lines = text.split("\n")
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + key + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (key, NEW[code], "," if l.rstrip().endswith(",") else "")
            hit += 1
    check(hit == 1, "%s 找到 %d 处" % (code, hit))
    out = "\n".join(lines)
    after = json.loads(out)
    check(after[key] == NEW[code], "%s 替换后值正确" % code)
    check(after[key].count("\\n") == 4, "%s 仍是 5 行（4 个转义换行）" % code)
    check(u"320" not in after[key], "%s 旧数字 320 已经不在文案里" % code)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

if fail:
    print("有 %d 项失败" % len(fail))
    sys.exit(1)
print("说明文案已更新。")
