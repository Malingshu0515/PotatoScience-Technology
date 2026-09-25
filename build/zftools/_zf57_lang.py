# -*- coding: utf-8 -*-
"""_zf57_lang.py —— 四语言"合金炉摆放方式"换成 ZF57 新图纸（用户自己的编号）

用户的图例：耐热金属块=1 一般金属块=2 加热装置=3 高炉=4
            （接线块/散热装置/合金炉主控 他写的是全名，这里给它们 5/6/7，0=空）

⚠ 只替换 `tooltip.potato_s_t.alloy_smelter` **那一行**，其余字节一个都不动
  （整份重排 json 会打乱键顺序/排版，LangCheck 与 diff 都会难看）。
数字行是**共享常量**：四语言用同一份，避免抄错。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = u"tooltip.potato_s_t.alloy_smelter"

# 10 行数字图（左列 = 第1+2层，右列 = 第3+4层）—— 唯一权威，四个语言共用
ROWS = [
    u"2222|5115",
    u"2332|4004",
    u"2332|4004",
    u"2332|4004",
    u"2222|6117",
    u"1111|0110",
    u"1001|0110",
    u"1001|0110",
    u"1001|0110",
    u"1111|0110",     # ZF58：第 4 层第 5 排也是【空·耐热·耐热·空】（ZF57 时按 0000 补的）
]

TEXT = {
    "zh_cn": {
        "head": u"合金炉摆放方式（主控＝图上写着 7 的那格：第2层 最前排 最右边）",
        "leg1": u"1 耐热金属块  2 一般金属块  3 加热装置  4 高炉",
        "leg2": u"5 接线块  6 散热装置  7 合金炉主控  0 空",
        "lab1": u"第1层（底）|第2层",
        "lab2": u"第3层|第4层（顶）",
        "rule": u"照图纸把 4 层摆完（要查 58 格：底面 + 三格高的墙 + 顶面那两列耐热金属块）、"
                u"且外壳上至少有 1 个接线块，才会自动激活（内部随便放，顶面其余格子不管）；"
                u"右键主控也能激活（缺哪格会说）；激活后右键才开界面。"
                u"5 输入只收锭 / 3 输出 / 2 消耗槽，储能 32768 FE，电只从接线口进。",
    },
    "en_us": {
        "head": u"Alloy Smelter layout (the controller is the cell marked 7: layer 2, front row, right column)",
        "leg1": u"1 Heat-Resistant Metal Block  2 Common Metal Block  3 Heater  4 Blast Furnace",
        "leg2": u"5 Wiring Block  6 Heat Sink  7 Alloy Smelter Controller  0 empty",
        "lab1": u"Layer 1 (bottom)|Layer 2",
        "lab2": u"Layer 3|Layer 4 (top)",
        "rule": u"The machine activates on its own once the whole 4-layer drawing is built "
                u"(58 cells are checked: floor + three lower wall layers + the two heat-resistant "
                u"columns on the roof) and at least one wiring block is in the shell "
                u"(the inside is free, the rest of the roof does not matter); right-clicking the "
                u"controller also activates it (it names the missing cell); only then does right-click "
                u"open the GUI. 5 inputs (ingots only) / 3 outputs / 2 consumable slots, 32768 FE, "
                u"power enters through the ports only.",
    },
    "ja_jp": {
        "head": u"合金精錬炉の配置（コントローラーは 7 のマス：第2層 最前列 右端）",
        "leg1": u"1 耐熱金属ブロック  2 一般金属ブロック  3 加熱装置  4 溶鉱炉",
        "leg2": u"5 配線ブロック  6 放熱装置  7 合金精錬炉コントローラー  0 空",
        "lab1": u"第1層（底）|第2層",
        "lab2": u"第3層|第4層（上）",
        "rule": u"設計図の 4 層をすべて置くと（検査するのは 58 マス：底面 + 三段の壁 + 屋根の耐熱金属 2 列）、"
                u"外殻に接続ブロックが 1 個以上あれば自動で起動します（内部は自由、屋根の残りは不問）。"
                u"コントローラーを右クリックしても起動できます（足りないマスを教えてくれます）。"
                u"起動後に右クリックで画面が開きます。"
                u"入力 5（インゴットのみ）/ 出力 3 / 消費 2、蓄電 32768 FE、電力は接続口からのみ。",
    },
    "ru_ru": {
        "head": u"Схема плавильни сплавов (контроллер — клетка с цифрой 7: слой 2, передний ряд, правый столбец)",
        "leg1": u"1 Жаростойкий металлический блок  2 Обычный металлический блок  3 Нагреватель  4 Доменная печь",
        "leg2": u"5 Соединительный блок  6 Радиатор  7 Контроллер плавильни сплавов  0 пусто",
        "lab1": u"Слой 1 (низ)|Слой 2",
        "lab2": u"Слой 3|Слой 4 (верх)",
        "rule": u"Плавильня активируется сама, когда выстроены все 4 слоя чертежа "
                u"(проверяются 58 клеток: пол + три нижних слоя стен + два столбца теплостойких "
                u"блоков на крыше) и в оболочке есть хотя бы один блок проводки "
                u"(внутренность свободна, остальная крыша не важна); щелчок правой кнопкой "
                u"по контроллеру тоже активирует (он назовёт недостающую клетку); интерфейс "
                u"откроется только после этого. 5 входов (только слитки) / 3 выхода / "
                u"2 расходных слота, 32768 FE, энергия только через порты.",
    },
}


def build(lang):
    t = TEXT[lang]
    lines = [t["head"], t["leg1"], t["leg2"], t["lab1"]]
    lines += ROWS[:5]
    lines.append(t["lab2"])
    lines += ROWS[5:]
    lines.append(t["rule"])
    return u"\n".join(lines)


def main():
    fails = []
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, lang + ".json")
        raw = io.open(path, "rb").read()
        text = raw.decode("utf-8")
        crlf = "\r\n" in text
        eol = u"\r\n" if crlf else u"\n"
        lines = text.split(eol)
        prefix = u'    "' + KEY + u'":  '
        idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        if len(idx) != 1:
            fails.append(u"%s: 找到 %d 行 %s" % (lang, len(idx), KEY))
            continue
        value = build(lang)
        lines[idx[0]] = prefix + json.dumps(value, ensure_ascii=False) + u","
        out = eol.join(lines)
        # 先自检：解析得回来、键集不变
        data = json.loads(out)
        if data[KEY] != value:
            fails.append(u"%s: 写回后值不一致" % lang)
            continue
        body = value.split(u"\n")
        io.open(path, "wb").write(out.encode("utf-8"))
        print(u"  [OK] %-8s 行数 %2d  数字行 %d  %s" % (
            lang, len(body), sum(1 for x in body if x[:4].isdigit()), u"CRLF" if crlf else u"LF"))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
