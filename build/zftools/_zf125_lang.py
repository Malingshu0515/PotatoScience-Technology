# -*- coding: utf-8 -*-
u"""_zf125_lang.py —— ZF125 四语言加 11 个键（464 → 475）

键（11 个）：
  block.potato_s_t.diesel_generator_controller
  tooltip.potato_s_t.diesel_generator_controller          ← Shift 说明（30 格摆放图）
  gui.potato_s_t.diesel_generator.status.disabled / empty / output_full / running / no_structure
  gui.potato_s_t.diesel_generator.invalid                 ← 8 个 %s
  gui.potato_s_t.diesel_generator.pour.empty / rejected / full

四条自检（都是"四份必须完全一致"那条规矩的落地）：
  ① 每份键数 = 475，且四份**键集合完全相同**
  ② 占位符签名（%s / %% 的个数与顺序）四份一致
  ③ 每个键在原文里**只出现一次**（JSON 解析会把重复键悄悄吃掉，只能查原文）
  ④ 纯净 LF、无 BOM（§4.92 那条口径）

插到哪儿：**文件末尾、最后的 `}` 之前**。这不是我随便挑的 —— 四份 lang 的"最新键"
历来就堆在末尾（`_zf122` 的 star_chart / starfall_pendant 那几行就是），
按字母序插进去反而会打乱这条历史（而且 4 份文件的段落顺序本来就不一样）。

跑法：
    python build\\zftools\\_zf125_lang.py
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
LOCALES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")

EXPECT_KEYS = 475
OLD_KEYS = 464

# 四份的最后一行（追加锚点用；四份的键名相同、只有值不同）
LAST_KEY = u"tooltip.potato_s_t.starfall_pendant.5"

TOOLTIP_ZH = (u"大型柴油发电机摆放方式（控制器＝图上写着 9 的那一格：第 1 层、最前排、正中间）\n"
              u"1 耐热金属块　2 一般金属块　3 流体泵　4 低级发电机\n"
              u"5 燃烧反应室　6 铜块　7 铜格栅　8 接线块　9 柴油发电机控制器\n"
              u"第 1 层（底）｜第 2 层\n"
              u"1 3 1 ｜ 2 1 2\n"
              u"1 4 1 ｜ 6 7 6\n"
              u"1 5 1 ｜ 6 7 6\n"
              u"1 4 1 ｜ 6 7 6\n"
              u"1 9 1 ｜ 2 8 2\n"
              u"以控制器的朝向为正面，机器朝它背后铺 5 排、向上 2 层，一共 30 格，一格都不能少。\n"
              u"铜块与铜格栅：氧化到什么程度、打没打蜡都行（16 种全收）。\n"
              u"摆齐后控制器正上方那格接线块会变成接线口（贴图一样，挖掉掉回接线块）—— 电只从那里出。\n"
              u"界面：一个 8000 mB 柴油罐 ＋ 一盏工作指示灯；每 tick 烧 1 mB 柴油发 7200 FE，有红石信号即停机。\n"
              u"柴油怎么进：接泵灌（控制器本体或接线口都行），或拿柴油桶 / 装着柴油的油桶右键控制器。\n"
              u"⚠ 里面那台流体泵 / 两台低级发电机 / 一台燃烧反应室成型后照样是它们自己，不会被吃掉。")

TOOLTIP_EN = (u"How to build the large diesel generator (the controller is the cell marked 9: layer 1, front row, middle)\n"
              u"1 heat-resistant metal block  2 common metal block  3 fluid pump  4 low generator\n"
              u"5 combustion chamber  6 copper block  7 copper grate  8 wiring block  9 diesel generator controller\n"
              u"Layer 1 (bottom) | Layer 2\n"
              u"1 3 1 | 2 1 2\n"
              u"1 4 1 | 6 7 6\n"
              u"1 5 1 | 6 7 6\n"
              u"1 4 1 | 6 7 6\n"
              u"1 9 1 | 2 8 2\n"
              u"The controller's facing is the front; the machine extends 5 rows behind it and 2 layers up - 30 cells, none may be missing.\n"
              u"Copper blocks and copper grates: any oxidation or waxed state works (all 16 are accepted).\n"
              u"Once complete, the wiring block right above the controller becomes a port (same texture, drops a wiring block) - power only leaves there.\n"
              u"GUI: an 8000 mB diesel tank + a status lamp; 1 mB of diesel per tick makes 7200 FE, a redstone signal stops it.\n"
              u"Getting diesel in: pump it in (controller or the port), or right-click the controller with a diesel bucket / an oil bucket holding diesel.\n"
              u"Warning: the fluid pump, the two low generators and the combustion chamber inside stay yours - nothing is consumed.")

TOOLTIP_JA = (u"大型ディーゼル発電機の組み方（制御器＝図の 9 のマス：第 1 層・最前列・中央）\n"
              u"1 耐熱金属ブロック　2 一般金属ブロック　3 流体ポンプ　4 低級発電機\n"
              u"5 燃焼反応室　6 銅ブロック　7 銅格子　8 配線ブロック　9 ディーゼル発電機制御器\n"
              u"第 1 層（底）｜第 2 層\n"
              u"1 3 1 ｜ 2 1 2\n"
              u"1 4 1 ｜ 6 7 6\n"
              u"1 5 1 ｜ 6 7 6\n"
              u"1 4 1 ｜ 6 7 6\n"
              u"1 9 1 ｜ 2 8 2\n"
              u"制御器の向きが正面です。機械はその背後へ 5 列、上へ 2 層、合計 30 マス。1 マスも欠かせません。\n"
              u"銅ブロックと銅格子は酸化・ワックスの度合いを問いません（16 種すべて可）。\n"
              u"完成すると制御器の真上の配線ブロックが接続口に変わります（見た目は同じ、掘ると配線ブロックに戻る）—— 電力はそこからだけ出ます。\n"
              u"GUI：8000 mB の軽油タンク ＋ 状態ランプ。毎 tick 軽油 1 mB で 7200 FE、レッドストーン信号で停止します。\n"
              u"軽油の入れ方：ポンプで送る（制御器でも接続口でも可）、または軽油入りバケツ / 軽油の入ったオイル缶で制御器を右クリック。\n"
              u"⚠ 中の流体ポンプ・低級発電機 2 台・燃焼反応室はそのまま残ります（消費されません）。")

TOOLTIP_RU = (u"Как собрать большой дизельный генератор (контроллер - клетка с цифрой 9: слой 1, передний ряд, центр)\n"
              u"1 теплостойкий блок  2 обычный металлический блок  3 жидкостный насос  4 низкий генератор\n"
              u"5 камера сгорания  6 медный блок  7 медная решётка  8 блок проводки  9 контроллер дизельного генератора\n"
              u"Слой 1 (низ) | Слой 2\n"
              u"1 3 1 | 2 1 2\n"
              u"1 4 1 | 6 7 6\n"
              u"1 5 1 | 6 7 6\n"
              u"1 4 1 | 6 7 6\n"
              u"1 9 1 | 2 8 2\n"
              u"Направление контроллера - это перед; машина идёт на 5 рядов назад и на 2 слоя вверх, всего 30 клеток, ни одну нельзя пропустить.\n"
              u"Медные блоки и решётки: подойдёт любая степень окисления и вощения (принимаются все 16).\n"
              u"Когда структура собрана, блок проводки прямо над контроллером становится портом (та же текстура, при добыче выпадает блок проводки) - энергия выходит только оттуда.\n"
              u"Интерфейс: бак дизеля на 8000 mB + лампа состояния; 1 mB дизеля за тик даёт 7200 FE, сигнал редстоуна останавливает машину.\n"
              u"Как залить дизель: насосом (в контроллер или в порт) либо правым щелчком по контроллеру ведром дизеля / канистрой с дизелем.\n"
              u"Внимание: насос, два низких генератора и камера сгорания внутри остаются вашими - ничего не расходуется.")

KEYS = [
    (u"block.potato_s_t.diesel_generator_controller", {
        u"zh_cn": u"柴油发电机控制器",
        u"en_us": u"Diesel Generator Controller",
        u"ja_jp": u"ディーゼル発電機制御器",
        u"ru_ru": u"Контроллер дизельного генератора",
    }),
    (u"tooltip.potato_s_t.diesel_generator_controller", {
        u"zh_cn": TOOLTIP_ZH, u"en_us": TOOLTIP_EN, u"ja_jp": TOOLTIP_JA, u"ru_ru": TOOLTIP_RU,
    }),
    (u"gui.potato_s_t.diesel_generator.status.running", {
        u"zh_cn": u"正在发电",
        u"en_us": u"Generating",
        u"ja_jp": u"発電中",
        u"ru_ru": u"Вырабатывает энергию",
    }),
    (u"gui.potato_s_t.diesel_generator.status.disabled", {
        u"zh_cn": u"已停机（红石信号）",
        u"en_us": u"Halted (redstone signal)",
        u"ja_jp": u"停止中（レッドストーン信号）",
        u"ru_ru": u"Остановлен (сигнал редстоуна)",
    }),
    (u"gui.potato_s_t.diesel_generator.status.empty", {
        u"zh_cn": u"柴油罐是空的：接泵灌，或拿柴油桶右键",
        u"en_us": u"Diesel tank is empty: pump it in, or right-click with a diesel bucket",
        u"ja_jp": u"軽油タンクが空です：ポンプで送るか、軽油入りバケツで右クリック",
        u"ru_ru": u"Бак дизеля пуст: закачайте насосом или щёлкните ведром дизеля",
    }),
    (u"gui.potato_s_t.diesel_generator.status.output_full", {
        u"zh_cn": u"电送不出去：缓冲满了，在接线口旁边贴一个输入端子或接铜线",
        u"en_us": u"Power has nowhere to go: the buffer is full - put an input terminal or a copper wire next to the port",
        u"ja_jp": u"電力の行き先がありません：バッファが満杯です。接続口の隣に輸入端子か銅線を",
        u"ru_ru": u"Энергию некуда девать: буфер полон - поставьте входной терминал или медный провод рядом с портом",
    }),
    (u"gui.potato_s_t.diesel_generator.status.no_structure", {
        u"zh_cn": u"结构不完整：按住 Shift 看摆放图（缺哪几格已经打在聊天栏）",
        u"en_us": u"Structure incomplete: hold Shift for the blueprint (the missing cells are printed in chat)",
        u"ja_jp": u"構造が不完全です：Shift で配置図を（足りないマスはチャットに出ています）",
        u"ru_ru": u"Структура не собрана: удержите Shift для схемы (чего не хватает - написано в чате)",
    }),
    (u"gui.potato_s_t.diesel_generator.invalid", {
        u"zh_cn": u"结构缺口：第 %s 层 第 %s 排 第 %s 列 应该是 %s，现在那里是 %s（坐标 %s %s %s）",
        u"en_us": u"Gap in the structure: layer %s, row %s, column %s should be %s, but it is %s (at %s %s %s)",
        u"ja_jp": u"構造の欠け：第 %s 層 第 %s 列 第 %s 行 は %s であるべきですが %s です（座標 %s %s %s）",
        u"ru_ru": u"Пробел в структуре: слой %s, ряд %s, столбец %s должен быть %s, а там %s (координаты %s %s %s)",
    }),
    (u"gui.potato_s_t.diesel_generator.pour.empty", {
        u"zh_cn": u"手里的容器是空的",
        u"en_us": u"The container in your hand is empty",
        u"ja_jp": u"手に持っている容器が空です",
        u"ru_ru": u"Контейнер в руке пуст",
    }),
    (u"gui.potato_s_t.diesel_generator.pour.rejected", {
        u"zh_cn": u"倒不进去：%s（这台机器只烧柴油）",
        u"en_us": u"Cannot pour in: %s (this machine only burns diesel)",
        u"ja_jp": u"注げません：%s（この機械は軽油しか燃やしません）",
        u"ru_ru": u"Не залить: %s (эта машина работает только на дизеле)",
    }),
    (u"gui.potato_s_t.diesel_generator.pour.full", {
        u"zh_cn": u"柴油罐装不下：罐满了，或者这一桶（1000 mB）塞不进去",
        u"en_us": u"The diesel tank cannot take it: the tank is full, or this whole bucket (1000 mB) does not fit",
        u"ja_jp": u"軽油タンクに入りません：満杯か、この 1 バケツ（1000 mB）が入りきりません",
        u"ru_ru": u"В бак дизеля не помещается: бак полон или целое ведро (1000 mB) не влезает",
    }),
]

notes, fails = [], []


def placeholders(text):
    return tuple(re.findall(r"%[sd%]", text))


def main():
    tables = {}
    for loc in LOCALES:
        path = os.path.join(LANG, loc + u".json")
        raw = open(path, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s：有 BOM" % loc)
        text = raw.decode(u"utf-8")
        if u"\r" in text:
            fails.append(u"%s：不是纯净 LF" % loc)
        before = json.loads(text)
        if len(before) != OLD_KEYS:
            fails.append(u"%s：改前键数 %d（期望 %d）—— 有人动过，停手"
                         % (loc, len(before), OLD_KEYS))
            continue
        if LAST_KEY not in text:
            fails.append(u"%s：找不到末尾锚点键 %s" % (loc, LAST_KEY))
            continue

        # 追加到最后的 `}` 之前
        idx = text.rindex(u"}")
        body = text[:idx].rstrip()
        if not body.endswith(u"\""):
            fails.append(u"%s：末尾 `}` 之前不是键值行的结尾，别硬插" % loc)
            continue
        lines = [body + u","]
        for n, (key, table) in enumerate(KEYS):
            # ⚠ 除了最后一个键，行尾都要有逗号 —— 第一版漏了，四份文件里第一份当场 JSON 报错
            tail = u"," if n < len(KEYS) - 1 else u""
            lines.append(u"    \"%s\":  %s%s" % (key, json.dumps(table[loc], ensure_ascii=False), tail))
        out = u"\n".join(lines) + u"\n}\n"
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(out)

        back = json.loads(io.open(path, encoding=u"utf-8").read())
        tables[loc] = back
        if len(back) != EXPECT_KEYS:
            fails.append(u"%s：键数 %d（期望 %d）" % (loc, len(back), EXPECT_KEYS))

    if len(tables) == 4:
        base = set(tables[u"zh_cn"].keys())
        for loc in LOCALES:
            if set(tables[loc].keys()) != base:
                fails.append(u"%s：键集合与 zh_cn 不一致" % loc)
        if not fails:
            notes.append(u"四份键数都是 %d，键集合完全相同" % EXPECT_KEYS)
        for key, _ in KEYS:
            sigs = {loc: placeholders(tables[loc][key]) for loc in LOCALES}
            if len(set(sigs.values())) != 1:
                fails.append(u"%s：四份占位符签名不一致 %s" % (key, sigs))
        if not any(u"占位符" in f for f in fails):
            notes.append(u"11 个新键的占位符签名四份一致（invalid 8 个 %s、pour.rejected 1 个 %s）")
        for key, _ in KEYS:
            for loc in LOCALES:
                text = io.open(os.path.join(LANG, loc + u".json"), encoding=u"utf-8").read()
                if text.count(u"\"%s\"" % key) != 1:
                    fails.append(u"%s：%s 在原文里出现 %d 次（要 1 次）"
                                 % (loc, key, text.count(u"\"%s\"" % key)))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
