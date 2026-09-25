# -*- coding: utf-8 -*-
"""ZF24 第二步：共享储能那一行消息补上"本块存量"，让玩家一眼看出"池子大、本块小"。

`solar_pool` 从 2 个占位符变成 4 个（共享池 + 本块缓冲），语言文件与 Java 必须同时改，
否则 LangCheck 的「占位符签名一致」能过、但游戏里会显示不出数字（占位符对不上不报错，
只是格式化失败）。所以这里连"本块"一起印出来 —— 也是给共享储能留的**肉眼证据**。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

EDITS = [
    ("zh_cn.json",
     '"message.potato_s_t.solar_pool":  "共享储能 %s / %s FE",',
     '"message.potato_s_t.solar_pool":  "共享储能 %s / %s FE（本块缓冲 %s / %s FE）",'),
    ("en_us.json",
     '"message.potato_s_t.solar_pool":  "Shared storage %s / %s FE",',
     '"message.potato_s_t.solar_pool":  "Shared storage %s / %s FE (this panel holds %s / %s FE)",'),
    ("ja_jp.json",
     '"message.potato_s_t.solar_pool":  "共有蓄電 %s / %s FE",',
     '"message.potato_s_t.solar_pool":  "共有蓄電 %s / %s FE（このパネル内 %s / %s FE）",'),
    ("ru_ru.json",
     '"message.potato_s_t.solar_pool":  "Общий запас %s / %s FE",',
     '"message.potato_s_t.solar_pool":  "Общий запас %s / %s FE (в этой панели %s / %s FE)",'),
]

for name, old, new in EDITS:
    path = os.path.join(LANG_DIR, name)
    text = io.open(path, encoding="utf-8").read()
    count = text.count(old)
    assert count == 1, "锚点不唯一/找不到：%s 命中 %d 次" % (name, count)
    text = text.replace(old, new)
    parsed = json.loads(text)
    assert parsed["message.potato_s_t.solar_pool"].count("%s") == 4, name
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("OK  %-12s  solar_pool 占位符 = %d" % (name, parsed["message.potato_s_t.solar_pool"].count("%s")))
