# -*- coding: utf-8 -*-
"""ZF28：动力能源捕获器的数值改了，四种语言的 tooltip 必须同步。

  流动水      16 → 8
  熔炉/烟熏炉  4 → 8    （翻倍）
  高炉        8 → 16   （翻倍）

**LangCheck 只查键集与占位符签名，查不出"数值写死在文案里"** ——
所以这里除了锚点唯一性，还断言两件事：
  ① 新串里的 8 / 16 都在
  ② **旧串的 "16"(水) 不能再作为水的数值出现**、旧值 4 不能留
     （用"变换后的串必须整串等于期望值"来断言，比 grep 数字可靠：
       因为 16 现在合法地出现在高炉上）
"""
import io
import json
import os

LANG_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"

# (文件, 旧串, 新串)   —— 整行值，逐字给出期望结果，避免"数字对不对"靠猜
EDITS = [
    ("zh_cn.json",
     "检测到紧邻的6个面有的流动水 或燃烧的熔炉 高炉 烟熏炉 产生动力 每格流动水+16动力 熔炉 烟熏炉+4 高炉+8(动力)",
     "检测到紧邻的6个面有的流动水 或燃烧的熔炉 高炉 烟熏炉 产生动力 每格流动水+8动力 熔炉 烟熏炉+8 高炉+16(动力)"),
    ("en_us.json",
     "Produces power from flowing water or burning furnaces on its 6 adjacent faces: flowing water +16, furnace/smoker +4, blast furnace +8.",
     "Produces power from flowing water or burning furnaces on its 6 adjacent faces: flowing water +8, furnace/smoker +8, blast furnace +16."),
    ("ja_jp.json",
     "隣接する6面の流水、または燃焼中のかまど・溶鉱炉・燻製器を検出して動力を生成します。流水1マスにつき+16、かまど・燻製器+4、溶鉱炉+8（動力）。",
     "隣接する6面の流水、または燃焼中のかまど・溶鉱炉・燻製器を検出して動力を生成します。流水1マスにつき+8、かまど・燻製器+8、溶鉱炉+16（動力）。"),
    ("ru_ru.json",
     "Обнаруживает на 6 прилегающих гранях текущую воду или горящие печи и вырабатывает энергию: текущая вода +16, печь и коптильня +4, доменная печь +8 (энергии).",
     "Обнаруживает на 6 прилегающих гранях текущую воду или горящие печи и вырабатывает энергию: текущая вода +8, печь и коптильня +8, доменная печь +16 (энергии)."),
]

for name, old, new in EDITS:
    path = os.path.join(LANG_DIR, name)
    text = io.open(path, encoding="utf-8").read()
    count = text.count(old)
    assert count == 1, "锚点不唯一/找不到：%s 命中 %d 次\n%r" % (name, count, old)
    text = text.replace(old, new)
    parsed = json.loads(text)
    tip = parsed["tooltip.potato_s_t.power_capturer"]
    assert tip == new, "%s 落盘内容与期望不一致：%s" % (name, tip)
    # 三个数值都在，且"水的旧值"不会以任何形态残留
    assert "16" in tip, "%s 缺高炉的 16" % name
    for stale in ("+16动力", "water +16", "につき+16", "вода +16"):
        assert stale not in tip, "%s 水的数值没改（残留 %s）：%s" % (name, stale, tip)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("OK  %-12s  keys=%d" % (name, len(parsed)))
    print("      %s" % tip)
