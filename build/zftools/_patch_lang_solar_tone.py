# -*- coding: utf-8 -*-
"""ZF30 补丁②：太阳能板的 Shift 说明也收成书面体（同一条毛病）。

毛病和液压机一样 —— 我在里面塞了"给开发者看的解释"：
  · "（染色玻璃、遮光玻璃都不行）"   ← 括号补充，玩家只需要知道"必须是空气或无色玻璃"
  · "（储能上限 = 块数 × 512 FE）"   ← 公式，玩家不需要
  · "Shift+右键 查看并联数量与总发电量" ← 祈使句，像操作便条
改成陈述句 + 无括号 + 去掉操作指引（操作说明放 JEI/百科更合适）。
四种语言同步；同时把 `state.blocked` 那条消息的括号也去掉（保持同一副口吻）。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

NEW = {
    "zh_cn": {
        "tooltip.potato_s_t.solar_panel":
            "仅在白天发电：日出与傍晚 60、上午与下午 135、正午 180 FE/t。\n"
            "雨天出力降至 60%，雷暴降至 20%。\n"
            "正上方须为空气或无色玻璃。\n"
            "自身储能 512 FE，自动为下方设备供电。\n"
            "水平相邻的太阳能板自动并联，发电量与储能均为整组共享。",
        "message.potato_s_t.solar.state.blocked": "上方被遮挡",
    },
    "en_us": {
        "tooltip.potato_s_t.solar_panel":
            "Generates power in daytime only: 60 FE/t at dawn and dusk, 135 in the morning and afternoon, 180 at noon.\n"
            "Output drops to 60% in rain and 20% in thunderstorms.\n"
            "The block directly above must be air or colorless glass.\n"
            "Stores 512 FE and feeds the block below automatically.\n"
            "Horizontally adjacent panels connect automatically, sharing generation and storage across the group.",
        "message.potato_s_t.solar.state.blocked": "blocked above",
    },
    "ja_jp": {
        "tooltip.potato_s_t.solar_panel":
            "昼間のみ発電：夜明けと夕方 60、午前と午後 135、正午 180 FE/t。\n"
            "雨天は 60%、雷雨は 20% に低下。\n"
            "真上は空気か無色ガラスである必要があります。\n"
            "蓄電 512 FE、真下の装置へ自動給電。\n"
            "水平に隣接するパネルは自動で並列接続し、発電量と蓄電を組全体で共有します。",
        "message.potato_s_t.solar.state.blocked": "上方が遮られている",
    },
    "ru_ru": {
        "tooltip.potato_s_t.solar_panel":
            "Вырабатывает энергию только днём: 60 FE/т на рассвете и закате, 135 утром и днём, 180 в полдень.\n"
            "В дождь выработка падает до 60%, в грозу — до 20%.\n"
            "Блок прямо над панелью должен быть воздухом или бесцветным стеклом.\n"
            "Хранит 512 FE и автоматически питает блок под собой.\n"
            "Панели, стоящие в ряд, соединяются автоматически: выработка и запас общие для всей группы.",
        "message.potato_s_t.solar.state.blocked": "сверху перекрыто",
    },
}


def json_escape(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]


for lang, changes in NEW.items():
    path = os.path.join(LANG_DIR, lang + ".json")
    lines = io.open(path, encoding="utf-8").read().splitlines(keepends=True)
    before = json.loads("".join(lines))
    for key, value in changes.items():
        hits = [i for i, l in enumerate(lines) if '"%s"' % key in l]
        assert len(hits) == 1, "%s：%s 命中 %d 行" % (lang, key, len(hits))
        # ⚠ **必须保住行尾那个逗号**：它不是键的一部分，但少了它 JSON 就断在下一行
        #   （第一版把整行换成不带逗号的新行 ⇒ json.loads 在第 126 行报 "Expecting ','"，
        #    又一次被自己的断言拦在写盘之前）。
        comma = "," if lines[hits[0]].rstrip().endswith(",") else ""
        lines[hits[0]] = '    "%s":  "%s"%s\n' % (key, json_escape(value), comma)
    out = "".join(lines)
    parsed = json.loads(out)
    for key, value in changes.items():
        assert parsed[key] == value, "%s：%s 落盘不符" % (lang, key)
    assert len(parsed) == len(before), "%s 键数变了" % lang
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("OK  %-8s %d 键，改了 %d 条" % (lang, len(parsed), len(changes)))
