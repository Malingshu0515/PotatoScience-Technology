# -*- coding: utf-8 -*-
"""ZF27：发电机 1 动力 = 16 FE → **2 FE**，四个语言的 tooltip 同步。

只改一个数字，但**四个语言都得改**：LangCheck 只查键集与占位符签名，
**查不出"数值写死在文案里"** —— 那种不一致只能靠人（或这种脚本）盯。
所以脚本里除了锚点唯一性，还断言"新串里必须有 2 FE"。
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

EDITS = [
    ("zh_cn.json",
     "依靠动力进行发电，每点动力 16 FE/t，动力产生见",
     "依靠动力进行发电，每点动力 2 FE/t，动力产生见"),
    ("en_us.json",
     "Generates FE from power: 1 power = 16 FE/t.",
     "Generates FE from power: 1 power = 2 FE/t."),
    ("ja_jp.json",
     "動力1につき16 FE/t。",
     "動力1につき2 FE/t。"),
    ("ru_ru.json",
     "1 единица энергии = 16 FE/т.",
     "1 единица энергии = 2 FE/т."),
]

for name, old, new in EDITS:
    path = os.path.join(LANG_DIR, name)
    text = io.open(path, encoding="utf-8").read()
    count = text.count(old)
    assert count == 1, "锚点不唯一/找不到：%s 命中 %d 次\n%r" % (name, count, old)
    text = text.replace(old, new)
    parsed = json.loads(text)                      # 语法不过就抛，绝不写盘
    tip = parsed["tooltip.potato_s_t.generator"]
    assert "16" not in tip, "%s 里还留着 16：%s" % (name, tip)
    assert "2 FE" in tip or "2 FE/т" in tip, "%s 没写上新值：%s" % (name, tip)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("OK  %-12s  %d 处替换，键数 %d" % (name, 1, len(parsed)))
