# -*- coding: utf-8 -*-
"""_zf48_lang.py —— ZF48 四语言新增 5 个键（钛矿 / 深层钛矿 / 粗钛 / 钛粉 / 钛锭）

命名风格照既有条目对齐（先 grep 过 cobalt_ingot / raw_cobalt / iron_powder）：
  锭：Cobalt Ingot / コバルトインゴット / Кобальтовый слиток  ⇒ Titanium Ingot / チタンインゴット / Титановый слиток
  粗矿：Raw Cobalt / 粗コバルト / Необработанный кобальт      ⇒ Raw Titanium / 粗チタン / Необработанный титан
  粉：Iron Dust / 鉄粉 / Железная пыль                        ⇒ Titanium Dust / チタン粉 / Титановая пыль

只追加、不重排；先查"键是不是已经在里面了" ⇒ **幂等**。
"""
import io
import json
import os
import sys

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
ALL_CODES = ("zh_cn", "en_us", "ja_jp", "ru_ru")
CODES = tuple(sys.argv[1:]) or ALL_CODES

NEW_KEYS = [
    ("block.potato_s_t.titanium_ore", {
        "zh_cn": u"钛矿", "en_us": u"Titanium Ore", "ja_jp": u"チタン鉱石", "ru_ru": u"Титановая руда"}),
    ("block.potato_s_t.deepslate_titanium_ore", {
        "zh_cn": u"深层钛矿", "en_us": u"Deepslate Titanium Ore",
        "ja_jp": u"深層岩のチタン鉱石", "ru_ru": u"Титановая руда в глубинном сланце"}),
    ("item.potato_s_t.raw_titanium", {
        "zh_cn": u"粗钛", "en_us": u"Raw Titanium", "ja_jp": u"粗チタン",
        "ru_ru": u"Необработанный титан"}),
    ("item.potato_s_t.titanium_powder", {
        "zh_cn": u"钛粉", "en_us": u"Titanium Dust", "ja_jp": u"チタン粉",
        "ru_ru": u"Титановая пыль"}),
    ("item.potato_s_t.titanium_ingot", {
        "zh_cn": u"钛锭", "en_us": u"Titanium Ingot", "ja_jp": u"チタンインゴット",
        "ru_ru": u"Титановый слиток"}),
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
    add[-1] = add[-1][:-1]
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

print(u"改完，跑 _zf48_verify.py 复核。")
