# -*- coding: utf-8 -*-
"""ZF30 补丁：液压机的 Shift 说明写得太"口语"了，改成书面体。

用户原话：「哎呀shift介绍没必要写成那样是给玩家看的 稍微书面一点」

问题出在我塞了太多"给你（开发者）解释"的话：
  · "原料走 c: 通用标签（别的 mod 的锭也能用）"  ← 玩家不需要知道标签机制
  · "输出槽放不下时会卡住等你取走，不会吞产物"    ← "不会吞产物"是内部事故的语言
  · "配方清单在 JEI 里搜<液压机>"                ← 祈使句，像便条
  · "共 24000 FE" 这种括号补充
改成与项目其它 tooltip 同一副口吻（对照 electrolyzer / salt_dryer / generator：
陈述句、技术名词直说、不长篇解释）。四种语言同步。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

NEW = {
    "zh_cn": "把矿物锭锻压成对应板材。\n"
             "耗电 400 FE/t，3 秒产出一块板。\n"
             "可加工：铜、铁、镍、钴、银、铝、钢。\n"
             "红石信号通入时停机，进度保留。\n"
             "配方一览见 JEI。",
    "en_us": "Presses mineral ingots into the corresponding plates.\n"
             "Consumes 400 FE/t and produces one plate every 3 seconds.\n"
             "Accepts copper, iron, nickel, cobalt, silver, aluminium and steel.\n"
             "A redstone signal halts operation; progress is kept.\n"
             "See JEI for the recipe list.",
    "ja_jp": "鉱物インゴットを対応する板材に鍛圧します。\n"
             "消費電力 400 FE/t、3 秒で 1 枚を生産。\n"
             "加工可能：銅・鉄・ニッケル・コバルト・銀・アルミ・鋼。\n"
             "レッドストーン信号の入力中は停止し、進捗は保持されます。\n"
             "レシピ一覧は JEI を参照。",
    "ru_ru": "Прессует слитки в соответствующие пластины.\n"
             "Расход 400 FE/т, одна пластина за 3 секунды.\n"
             "Обрабатывает медь, железо, никель, кобальт, серебро, алюминий и сталь.\n"
             "Сигнал красного камня останавливает работу; прогресс сохраняется.\n"
             "Список рецептов — в JEI.",
}

KEY = "tooltip.potato_s_t.hydraulic_press"

def json_escape(value):
    """按 JSON 规范把值转义成"文件里那一行长什么样"（换行 -> \\n）。"""
    return json.dumps(value, ensure_ascii=False)[1:-1]


for lang, value in NEW.items():
    path = os.path.join(LANG_DIR, lang + ".json")
    lines = io.open(path, encoding="utf-8").read().splitlines(keepends=True)
    before = json.loads("".join(lines))

    # 直接**逐行**找：命中含该键的那一行，整行换成新值。
    # （比"拼一个锚点字符串去 count"稳：不用猜缩进/空格的细节 —— 上一版就是这么栽的）
    hits = [i for i, l in enumerate(lines) if '"%s"' % KEY in l]
    assert len(hits) == 1, "%s 命中 %d 行（应为 1）" % (lang, len(hits))
    idx = hits[0]
    lines[idx] = '    "%s":  "%s"\n' % (KEY, json_escape(value))
    out = "".join(lines)

    parsed = json.loads(out)                       # 语法不过就抛，绝不写盘
    assert parsed[KEY] == value, "%s 落盘内容不符" % lang
    assert len(parsed) == len(before), "%s 键数变了：%d -> %d" % (lang, len(before), len(parsed))
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-8s %d 键  新说明 %d 行 / %d 字"
          % (lang, len(parsed), value.count("\n") + 1, len(value)))
