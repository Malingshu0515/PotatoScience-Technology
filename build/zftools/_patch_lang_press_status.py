# -*- coding: utf-8 -*-
"""ZF30 补丁③：液压机需要**自己那套**状态灯文案（原来借了微型粉碎机的）。

用户截图指出：液压机界面上悬停状态灯显示「正在粉碎」。
根因不是文案写错，是 `StatusLampPart` 的 key 前缀**写死在类里**（微型粉碎机的），
液压机复用该部件时没传前缀 ⇒ 拿的是粉碎机的键。

这里补 6 个键 × 4 语言（键数 144 → 150）：
    gui.potato_s_t.hydraulic_press.status.{disabled,empty,invalid,no_power,output_full,running}
用词与液压机的 tooltip 保持一致（"锻压"而不是"粉碎"）。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

NEW = {
    "disabled": {
        "zh_cn": "已停机（红石信号）",
        "en_us": "Halted by redstone signal",
        "ja_jp": "停止中（レッドストーン信号）",
        "ru_ru": "Остановлено сигналом красного камня",
    },
    "empty": {
        "zh_cn": "输入槽为空",
        "en_us": "Input slot is empty",
        "ja_jp": "入力スロットが空です",
        "ru_ru": "Входной слот пуст",
    },
    "invalid": {
        "zh_cn": "该物品不可锻压",
        "en_us": "This item cannot be pressed",
        "ja_jp": "このアイテムは鍛圧できません",
        "ru_ru": "Этот предмет нельзя прессовать",
    },
    "no_power": {
        "zh_cn": "电力不足：需要持续供电",
        "en_us": "Not enough power: continuous supply needed",
        "ja_jp": "電力不足：継続的な給電が必要",
        "ru_ru": "Недостаточно энергии: нужно постоянное питание",
    },
    "output_full": {
        "zh_cn": "输出槽已满，等待腾出位置",
        "en_us": "Output slot is full, waiting for space",
        "ja_jp": "出力スロットが一杯です（空き待ち）",
        "ru_ru": "Выходной слот полон, ожидание места",
    },
    "running": {
        "zh_cn": "正在锻压",
        "en_us": "Pressing",
        "ja_jp": "鍛圧中",
        "ru_ru": "Прессование",
    },
}

PREFIX = "gui.potato_s_t.hydraulic_press.status."
LINES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]


def json_escape(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]


def insert_before_closing(text, new_lines):
    """在最后一个 } 之前插入若干行，并保证前一行有逗号。"""
    lines = text.splitlines(keepends=True)
    close = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            close = i
            break
    assert close is not None, "找不到收尾的 }"
    # 往上找最后一行非空行，补逗号
    j = close - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    assert j >= 0, "文件是空的？"
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip("\r\n") + ",\n"
    lines[close:close] = new_lines
    return "".join(lines)


for fname in LINES:
    lang = fname[:-5]
    path = os.path.join(LANG_DIR, fname)
    text = io.open(path, encoding="utf-8").read()
    before = json.loads(text)
    keys = list(NEW)
    add = []
    for idx, suffix in enumerate(keys):
        key = PREFIX + suffix
        assert key not in before, "%s 已有 %s" % (fname, key)
        comma = "," if idx < len(keys) - 1 else ""
        add.append('    "%s":  "%s"%s\n' % (key, json_escape(NEW[suffix][lang]), comma))
    out = insert_before_closing(text, add)
    parsed = json.loads(out)                      # 语法不过就抛，绝不写盘
    assert len(parsed) == len(before) + 6, "%s 键数 %d -> %d（应 +6）" % (fname, len(before), len(parsed))
    for suffix in keys:
        assert parsed[PREFIX + suffix] == NEW[suffix][lang], "%s：%s 落盘不符" % (fname, suffix)
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-12s %d -> %d 键（+6）  正在锻压 = %r"
          % (fname, len(before), len(parsed), parsed[PREFIX + "running"]))
