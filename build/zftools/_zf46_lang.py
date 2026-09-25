# -*- coding: utf-8 -*-
"""_zf46_lang.py —— ZF46 四语言新增 3 个键（黑钨矿 / 深层黑钨矿 / 粗钨）

**只追加、不重排**：`json.dump` 会把整个文件重写、diff 变成全文件，那样没人能复核这次改了什么。
追加前先查"这个键是不是已经在里面了" ⇒ **幂等**，重复跑不会插两遍（ZF45 那次的教训）。

命名风格跟既有矿石对齐（见 ja/ru 里 `manganese_ore` / `raw_manganese`）：
  · 英文：Wolframite Ore / Deepslate Wolframite Ore / Raw Tungsten
  · 日文：タングステン鉱石 / 深層岩のタングステン鉱石 / 粗タングステン
  · 俄文：Вольфрамовая руда / …в глубинном сланце / Необработанный вольфрам
矿物名（黑钨矿 = wolframite）只在**中文**里保留，其余语言用"钨"这个材料名 ——
和 マンガン鉱石 / Литиевая руда 的处理一致。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
CODES = tuple(sys.argv[1:]) or ALL_CODES

NEW_KEYS = [
    ("block.potato_s_t.wolframite_ore", {
        "zh_cn": u"黑钨矿",
        "en_us": u"Wolframite Ore",
        "ja_jp": u"タングステン鉱石",
        "ru_ru": u"Вольфрамовая руда",
    }),
    ("block.potato_s_t.deepslate_wolframite_ore", {
        "zh_cn": u"深层黑钨矿",
        "en_us": u"Deepslate Wolframite Ore",
        "ja_jp": u"深層岩のタングステン鉱石",
        "ru_ru": u"Вольфрамовая руда в глубинном сланце",
    }),
    ("item.potato_s_t.raw_tungsten", {
        "zh_cn": u"粗钨",
        "en_us": u"Raw Tungsten",
        "ja_jp": u"粗タングステン",
        "ru_ru": u"Необработанный вольфрам",
    }),
]

for code in CODES:
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    todo = [(k, t) for k, t in NEW_KEYS if ('"' + k + '"') not in text]
    if not todo:
        print(u"[跳过] %s：%d 个键都已在（%d 键）" % (code, len(NEW_KEYS), len(before)))
        continue
    lines = text.split("\n")
    last = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('"'):
            last = i
            break
    if last is None:
        raise SystemExit(u"%s: 找不到最后一个键行" % code)
    if not lines[last].rstrip().endswith(","):
        lines[last] = lines[last].rstrip() + ","
    add = [u'    "%s":  "%s",' % (k, t[code]) for k, t in todo]
    add[-1] = add[-1][:-1]                      # 最后一个后面直接跟收尾的 "}"
    lines[last + 1:last + 1] = add
    text = "\n".join(lines)

    after = json.loads(text)
    if len(after) != len(before) + len(todo):
        raise SystemExit(u"%s: 键数 %d -> %d（应加 %d）" % (code, len(before), len(after), len(todo)))
    for k, t in todo:
        if after[k] != t[code]:
            raise SystemExit(u"%s: %s = %r" % (code, k, after[k]))
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(u"[OK] %s: %d -> %d 键" % (code, len(before), len(after)))

print(u"改完，跑 _zf46_verify.py 复核。")
