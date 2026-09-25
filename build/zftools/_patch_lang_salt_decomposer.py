# -*- coding: utf-8 -*-
"""ZF32：四种语言补上盐分解构器 / 氯化钠的全部键。

新增：
  block.potato_s_t.salt_decomposer / item.potato_s_t.sodium_chloride
  tooltip.potato_s_t.salt_decomposer
  gui.potato_s_t.jei.salt_return / gui.potato_s_t.jei.raw_ore_chance   ← JEI 说明行用
  gui.potato_s_t.salt_decomposer.status.*（6 条，状态灯悬停）

口径沿用 ZF30 的 tooltip 规矩（**陈述句、不解释机制、不带括号公式、不写操作指引**）：
  · 概率与数量直接写进句子
  · 不提"c: 标签""不会吞产物"这类内部语言
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

# 顺序即插入顺序；值按语言给
KEYS = [
    ("block.potato_s_t.salt_decomposer", {
        "zh_cn": "盐分解构器",
        "en_us": "Salt Decomposer",
        "ja_jp": "塩分解装置",
        "ru_ru": "Разлагатель соли",
    }),
    ("item.potato_s_t.sodium_chloride", {
        "zh_cn": "氯化钠",
        "en_us": "Sodium Chloride",
        "ja_jp": "塩化ナトリウム",
        "ru_ru": "Хлорид натрия",
    }),
    ("tooltip.potato_s_t.salt_decomposer", {
        "zh_cn": "分解海盐制取氯化钠。\n"
                 "每次投入 64 个海盐，40 秒后产出 1 个氯化钠。\n"
                 "60% 概率返还 64 个海盐；5% 概率额外产出一个随机粗矿。\n"
                 "耗电 20 FE/t，自身储能仅 20 FE，需持续供电。\n"
                 "红石信号通入时停机，进度保留。",
        "en_us": "Decomposes sea salt into sodium chloride.\n"
                 "Consumes 64 sea salt and yields 1 sodium chloride every 40 seconds.\n"
                 "A 60% chance returns 64 sea salt; a 5% chance yields one random raw ore.\n"
                 "Consumes 20 FE/t and stores only 20 FE, so it needs a continuous supply.\n"
                 "A redstone signal halts operation; progress is kept.",
        "ja_jp": "海塩を分解して塩化ナトリウムを得ます。\n"
                 "1 回につき海塩 64 個を投入し、40 秒後に塩化ナトリウム 1 個を生産。\n"
                 "60% の確率で海塩 64 個が返却され、5% の確率でランダムな粗鉱が 1 個追加されます。\n"
                 "消費電力 20 FE/t、蓄電は 20 FE のみのため継続給電が必要です。\n"
                 "レッドストーン信号の入力中は停止し、進捗は保持されます。",
        "ru_ru": "Разлагает морскую соль на хлорид натрия.\n"
                 "За один цикл расходует 64 морской соли и через 40 секунд даёт 1 хлорид натрия.\n"
                 "С вероятностью 60% возвращает 64 морской соли; с вероятностью 5% даёт одну случайную руду.\n"
                 "Расход 20 FE/т, а запас всего 20 FE, поэтому нужно постоянное питание.\n"
                 "Сигнал красного камня останавливает работу; прогресс сохраняется.",
    }),
    ("gui.potato_s_t.jei.salt_return", {
        "zh_cn": "%s%% 概率返还 %s 个海盐",
        "en_us": "%s%% chance to return %s sea salt",
        "ja_jp": "%s%% の確率で海塩 %s 個を返却",
        "ru_ru": "%s%% шанс вернуть %s морской соли",
    }),
    ("gui.potato_s_t.jei.raw_ore_chance", {
        "zh_cn": "%s%% 概率额外产出一个随机粗矿",
        "en_us": "%s%% chance for one random raw ore",
        "ja_jp": "%s%% の確率でランダムな粗鉱を追加",
        "ru_ru": "%s%% шанс на одну случайную руду",
    }),
    ("gui.potato_s_t.salt_decomposer.status.running", {
        "zh_cn": "正在分解",
        "en_us": "Decomposing",
        "ja_jp": "分解中",
        "ru_ru": "Разложение",
    }),
    ("gui.potato_s_t.salt_decomposer.status.empty", {
        "zh_cn": "输入槽为空",
        "en_us": "Input slot is empty",
        "ja_jp": "入力スロットが空です",
        "ru_ru": "Входной слот пуст",
    }),
    ("gui.potato_s_t.salt_decomposer.status.invalid", {
        "zh_cn": "需要 64 个海盐",
        "en_us": "Requires 64 sea salt",
        "ja_jp": "海塩 64 個が必要です",
        "ru_ru": "Требуется 64 морской соли",
    }),
    ("gui.potato_s_t.salt_decomposer.status.no_power", {
        "zh_cn": "电力不足：需要持续供电",
        "en_us": "Not enough power: continuous supply needed",
        "ja_jp": "電力不足：継続的な給電が必要",
        "ru_ru": "Недостаточно энергии: нужно постоянное питание",
    }),
    ("gui.potato_s_t.salt_decomposer.status.output_full", {
        "zh_cn": "输出槽已满，等待腾出位置",
        "en_us": "Output slots are full, waiting for space",
        "ja_jp": "出力スロットが一杯です（空き待ち）",
        "ru_ru": "Выходные слоты полны, ожидание места",
    }),
    ("gui.potato_s_t.salt_decomposer.status.disabled", {
        "zh_cn": "已停机（红石信号）",
        "en_us": "Halted by redstone signal",
        "ja_jp": "停止中（レッドストーン信号）",
        "ru_ru": "Остановлено сигналом красного камня",
    }),
]


def json_escape(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]


def insert_before_closing(text, new_lines):
    lines = text.splitlines(keepends=True)
    close = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            close = i
            break
    assert close is not None, "找不到收尾的 }"
    j = close - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip("\r\n") + ",\n"
    lines[close:close] = new_lines
    return "".join(lines)


for fname in ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"):
    lang = fname[:-5]
    path = os.path.join(LANG_DIR, fname)
    text = io.open(path, encoding="utf-8").read()
    before = json.loads(text)
    add = []
    for idx, (key, per_lang) in enumerate(KEYS):
        assert key not in before, "%s 已有 %s" % (fname, key)
        comma = "," if idx < len(KEYS) - 1 else ""
        add.append('    "%s":  "%s"%s\n' % (key, json_escape(per_lang[lang]), comma))
    out = insert_before_closing(text, add)
    parsed = json.loads(out)
    assert len(parsed) == len(before) + len(KEYS), \
        "%s 键数 %d -> %d（应 +%d）" % (fname, len(before), len(parsed), len(KEYS))
    for key, per_lang in KEYS:
        assert parsed[key] == per_lang[lang], "%s：%s 落盘不符" % (fname, key)
    # 重复键自检
    import re
    src_keys = re.findall(r'^\s*"([^"]+)"\s*:', out, re.M)
    dup = [k for k in set(src_keys) if src_keys.count(k) > 1]
    assert not dup, "%s 有重复键：%s" % (fname, dup)
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-12s %d -> %d 键（+%d）" % (fname, len(before), len(parsed), len(KEYS)))
