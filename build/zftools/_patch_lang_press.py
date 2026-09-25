# -*- coding: utf-8 -*-
"""ZF30：四种语言补上液压机与铜板的键（键数 141 → 144）。

**放在文件末尾**（`itemGroup.potato_s_t` 之后）并保留原有缩进与逗号风格：
这个项目的 lang 文件是逐行手写的，脚本只做"在最后一个键后面追加"这一件事，
绝不去重排 —— 重排会让以后每次 diff 都面目全非。

断言：
  ① 追加前后**键数 +3**；
  ② 新键四种语言都存在；
  ③ JSON 语法过（json.loads），且**没有重复键**（Python 的 json 会静默丢重复键，
     所以先手工数一遍 `"key":` 出现次数）。
"""
import io
import json
import os
import re

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

# 键 → 四种语言的值
NEW_KEYS = {
    "block.potato_s_t.hydraulic_press": {
        "zh_cn": "液压机",
        "en_us": "Hydraulic Press",
        "ja_jp": "油圧プレス",
        "ru_ru": "Гидравлический пресс",
    },
    "item.potato_s_t.copper_plate": {
        "zh_cn": "铜板",
        "en_us": "Copper Plate",
        "ja_jp": "銅板",
        "ru_ru": "Медная пластина",
    },
    "tooltip.potato_s_t.hydraulic_press": {
        "zh_cn": "把矿物锭锻压成板材：\\n400 FE/t，3 秒压出一块板（一块板共 24000 FE）\\n"
                 "可压：铜 / 铁 / 镍 / 钴 / 银 / 铝 / 钢 的锭，原料走 c: 通用标签（别的 mod 的锭也能用）\\n"
                 "红石信号 = 关机（进度保留）；输出槽放不下时会卡住等你取走，不会吞产物\\n"
                 "配方清单在 JEI 里搜\\u003c液压机\\u003e",
        "en_us": "Presses mineral ingots into plates:\\n400 FE/t, 3 seconds per plate (24000 FE each)\\n"
                 "Accepts copper / iron / nickel / cobalt / silver / aluminum / steel ingots, matched by c: tags (other mods' ingots work too)\\n"
                 "Redstone signal = off (progress kept); it waits if the output slot is full and never voids the product\\n"
                 "See JEI for the full recipe list",
        "ja_jp": "鉱物インゴットを板材に鍛圧します：\\n400 FE/t、1 枚 3 秒（1 枚あたり 24000 FE）\\n"
                 "銅・鉄・ニッケル・コバルト・銀・アルミ・鋼のインゴットに対応（c: タグ判定なので他 MOD のインゴットも可）\\n"
                 "レッドストーン信号で停止（進捗は保持）。出力スロットが一杯なら待機し、成果物は消えません\\n"
                 "レシピ一覧は JEI で\\u003c油圧プレス\\u003eを検索",
        "ru_ru": "Прессует слитки в пластины:\\n400 FE/т, 3 секунды на пластину (24000 FE за штуку)\\n"
                 "Принимает слитки меди / железа / никеля / кобальта / серебра / алюминия / стали по тегам c: (слитки других модов тоже подходят)\\n"
                 "Сигнал красного камня = выключено (прогресс сохраняется); при полном выходном слоте ждёт и не уничтожает продукт\\n"
                 "Список рецептов — в JEI",
    },
}

FILES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]

for fname in FILES:
    path = os.path.join(LANG_DIR, fname)
    text = io.open(path, encoding="utf-8").read()
    lang = fname[:-5]
    before = json.loads(text)
    assert "block.potato_s_t.hydraulic_press" not in before, "%s 已经有这个键了" % fname

    # 在最后一个 "key": "value" 行之后追加。逐行找最后一行以 `":` 结尾的键行。
    lines = text.splitlines(keepends=True)
    last = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*"[^"]+"\s*:', line):
            last = i
    assert last is not None, "%s 找不到任何键行" % fname
    # ⚠ 这里踩过一个小坑：必须**写回 lines[last]**。
    #   第一版写的是 `lines[last] = ...` 之外的 `lines[last] = lines[last]...` 没问题，
    #   但我当时用的是 `text = text.replace(...)` 式的思路，结果只改了局部变量没改列表。
    if not lines[last].rstrip().endswith(","):
        lines[last] = lines[last].rstrip("\r\n") + ",\n"
    # ⚠ 追加的每一行**自己也要带逗号**，最后一行不带 ——
    #   第一版忘了给前两行加逗号，json.loads 在第 144 行报 "Expecting ',' delimiter" 拦住（幸好拦住了）。
    keys = list(NEW_KEYS)
    add = []
    for idx, key in enumerate(keys):
        tail = "," if idx < len(keys) - 1 else ""
        add.append('    "%s":  "%s"%s\n' % (key, NEW_KEYS[key][lang], tail))
    lines[last + 1:last + 1] = add
    out = "".join(lines)
    parsed = json.loads(out)                      # 语法不过就抛，绝不写盘
    assert len(parsed) == len(before) + 3, "%s 键数 %d -> %d（应 +3）" % (fname, len(before), len(parsed))
    for key in NEW_KEYS:
        assert key in parsed and parsed[key].strip(), "%s 缺 %s" % (fname, key)
    # 重复键自检：源码里 `"key":` 出现次数必须等于 json 解析出的键数
    src_keys = re.findall(r'^\s*"([^"]+)"\s*:', out, re.M)
    dup = [k for k in set(src_keys) if src_keys.count(k) > 1]
    assert not dup, "%s 有重复键：%s" % (fname, dup)
    assert len(src_keys) == len(parsed), "%s 键数对不上：源码 %d vs 解析 %d" % (fname, len(src_keys), len(parsed))
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-12s %d -> %d 键（+3），无重复键" % (fname, len(before), len(parsed)))
