# -*- coding: utf-8 -*-
"""ZF29：太阳能板发电量 ×3（20/45/60 → 60/135/180），四个语言的 tooltip 同步。

**只乘"三档速率"，不碰"雨天 60% / 雷暴 20%"** —— 那是**百分比**，不是速率。
把 60% 也乘 3 会变成 180%，是个很典型的"看见数字就改"的错误，所以脚本里专门断言
雨天/雷暴的百分比**原样保留**。

LangCheck 查不出"数值写死在文案里"，所以这里自己断言：
  ① 三档新值都在、旧值不再作为速率出现
  ② 天气百分比没被动过
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

# (文件, 旧串, 新串, 必须保留的天气片段, 不许再出现的旧速率片段)
EDITS = [
    ("zh_cn.json",
     "只在白天发电：日出/傍晚 20、上午/下午 45、正午 60 FE/t",
     "只在白天发电：日出/傍晚 60、上午/下午 135、正午 180 FE/t",
     "雨天为其 60%、雷暴为其 20%",
     ("日出/傍晚 20", "上午/下午 45")),
    ("en_us.json",
     "Generates only in daytime: dawn/dusk 20, morning/afternoon 45, noon 60 FE/t",
     "Generates only in daytime: dawn/dusk 60, morning/afternoon 135, noon 180 FE/t",
     "Rain 60% of that, thunder 20%",
     ("dawn/dusk 20", "morning/afternoon 45")),
    ("ja_jp.json",
     "昼のみ発電：夜明け/夕方 20、午前/午後 45、正午 60 FE/t",
     "昼のみ発電：夜明け/夕方 60、午前/午後 135、正午 180 FE/t",
     "雨はその 60%、雷雨は 20%",
     ("夜明け/夕方 20", "午前/午後 45")),
    ("ru_ru.json",
     "Работает только днём: рассвет/закат 20, утро/полдень 45, полдень 60 FE/т",
     "Работает только днём: рассвет/закат 60, утро/полдень 135, полдень 180 FE/т",
     "Дождь — 60% от этого, гроза — 20%",
     ("рассвет/закат 20", "утро/полдень 45")),
]

for name, old, new, weather, stale_rates in EDITS:
    path = os.path.join(LANG_DIR, name)
    text = io.open(path, encoding="utf-8").read()
    count = text.count(old)
    assert count == 1, "锚点不唯一/找不到：%s 命中 %d 次\n%r" % (name, count, old)
    text = text.replace(old, new)
    parsed = json.loads(text)                       # 语法不过就抛，绝不写盘
    tip = parsed["tooltip.potato_s_t.solar_panel"]
    for v in ("60", "135", "180"):
        assert v in tip, "%s 缺 %s：%s" % (name, v, tip)
    for s in stale_rates:
        assert s not in tip, "%s 旧速率还在（%s）：%s" % (name, s, tip)
    assert weather in tip, "%s 天气百分比被改动了！应为 %r：%s" % (name, weather, tip)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("OK  %-12s  keys=%d" % (name, len(parsed)))
