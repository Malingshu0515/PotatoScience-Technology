# -*- coding: utf-8 -*-
"""ZF24：太阳能板「共享储能」文案改写。

改 4 个语言文件，每处替换都带断言（找不到就停，不写盘）—— 见档案 §4.17
「能失败的检查才算检查」。写盘前统一 json.loads 验一遍语法。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

# (文件, 旧串, 新串)
EDITS = [
    # ---------- zh_cn ----------
    ("zh_cn.json",
     r"自身储能 512 FE，会自动供电给正下方的设备\n水平相邻的太阳能板自动并联，共享发电量（不共享储能）",
     r"自身储能 512 FE，会自动供电给正下方的设备\n水平相邻的太阳能板自动并联：共享发电量、也共享储能（储能上限 = 块数 × 512 FE）"),
    ("zh_cn.json",
     r'"message.potato_s_t.solar_detail":  "本块分到 %s FE/t，储能 %s / %s FE，状态：%s",',
     '"message.potato_s_t.solar_self":  "本块分到 %s FE/t，状态：%s",\n'
     '    "message.potato_s_t.solar_pool":  "共享储能 %s / %s FE",'),

    # ---------- en_us ----------
    ("en_us.json",
     r"Stores 512 FE and feeds the block directly below\nHorizontally adjacent panels connect in parallel and share generation (not storage)",
     r"Stores 512 FE and feeds the block directly below\nHorizontally adjacent panels connect in parallel: they share both generation and energy storage (capacity = panels x 512 FE)"),
    ("en_us.json",
     r'"message.potato_s_t.solar_detail":  "This panel gets %s FE/t, buffer %s / %s FE, status: %s",',
     '"message.potato_s_t.solar_self":  "This panel gets %s FE/t, status: %s",\n'
     '    "message.potato_s_t.solar_pool":  "Shared storage %s / %s FE",'),

    # ---------- ja_jp ----------
    ("ja_jp.json",
     r"蓄電 512 FE、真下の装置へ自動給電\n水平に隣接するパネルは並列接続し発電量を共有（蓄電は共有しない）",
     r"蓄電 512 FE、真下の装置へ自動給電\n水平に隣接するパネルは並列接続：発電量も蓄電も共有（容量 = 枚数 × 512 FE）"),
    ("ja_jp.json",
     r'"message.potato_s_t.solar_detail":  "このパネルは %s FE/t、蓄電 %s / %s FE、状態：%s",',
     '"message.potato_s_t.solar_self":  "このパネルは %s FE/t、状態：%s",\n'
     '    "message.potato_s_t.solar_pool":  "共有蓄電 %s / %s FE",'),

    # ---------- ru_ru ----------
    ("ru_ru.json",
     r"Хранит 512 FE и питает блок прямо под собой\nПанели в ряд соединяются параллельно и делят выработку (не запас)",
     r"Хранит 512 FE и питает блок прямо под собой\nПанели в ряд соединяются параллельно: общая выработка и общий запас (ёмкость = число панелей x 512 FE)"),
    ("ru_ru.json",
     r'"message.potato_s_t.solar_detail":  "Панель получает %s FE/т, буфер %s / %s FE, состояние: %s",',
     '"message.potato_s_t.solar_self":  "Панель получает %s FE/т, состояние: %s",\n'
     '    "message.potato_s_t.solar_pool":  "Общий запас %s / %s FE",'),
]

by_file = {}
for name, old, new in EDITS:
    by_file.setdefault(name, []).append((old, new))

for name in sorted(by_file):
    path = os.path.join(LANG_DIR, name)
    text = io.open(path, encoding="utf-8").read()
    for old, new in by_file[name]:
        count = text.count(old)
        assert count == 1, "锚点不唯一/找不到：%s 命中 %d 次\n%r" % (name, count, old[:60])
        text = text.replace(old, new)
    parsed = json.loads(text)          # 语法没通过就抛，绝不写盘
    assert "message.potato_s_t.solar_detail" not in parsed, name
    for key in ("message.potato_s_t.solar_self", "message.potato_s_t.solar_pool"):
        assert key in parsed, "%s 缺 %s" % (name, key)
    assert parsed["message.potato_s_t.solar_pool"].count("%s") == 2, name
    assert parsed["message.potato_s_t.solar_self"].count("%s") == 2, name
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("OK  %-12s  %d 处替换，键数 %d" % (name, len(by_file[name]), len(parsed)))
