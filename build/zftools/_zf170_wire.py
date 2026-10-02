# -*- coding: utf-8 -*-
u"""_zf170_wire.py —— ZF170：给引力装置补两条**模式**文案（五语言），并核对键集合一致"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")

KEYS = {
    u"message.potato_s_t.gravity.mode.swallow": {
        u"zh_cn": u"模式：吞噬搬运 —— 方块搬到黑洞脚下码起来（原位置变空）",
        u"en_us": u"Mode: Swallow - blocks are moved to the black hole and stacked there",
        u"ja_jp": u"モード：捕食搬送 —— ブロックはブラックホールの下に積まれます",
        u"ru_ru": u"Режим: поглощение — блоки переносятся и складываются у дыры",
        u"lzh": u"模式：吞噬搬運 —— 方塊移於黑洞之下而積之"},
    u"message.potato_s_t.gravity.mode.tow": {
        u"zh_cn": u"模式：引力牵引 —— 方块变成下落方块飞过来，落地还是方块，绝不消失",
        u"en_us": u"Mode: Gravity Tow - blocks fly over as falling blocks, land as blocks, never vanish",
        u"ja_jp": u"モード：重力牽引 —— ブロックは落下ブロックとして飛び、着地すれば元に戻ります",
        u"ru_ru": u"Режим: гравитационная тяга — блоки летят как падающие и приземляются, не исчезая",
        u"lzh": u"模式：引力牽引 —— 方塊化為墜塊飛來，落地復為方塊，終不消滅"},
}

tables = {}
for c in CODES:
    p = os.path.join(LANG, c + u".json")
    d = json.loads(io.open(p, encoding="utf-8").read())
    added = 0
    for k, vals in KEYS.items():
        if k not in d:
            d[k] = vals[c]
            added += 1
    if added:
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
    tables[c] = json.loads(io.open(p, encoding="utf-8").read())
    print(u"  %-6s +%d 键（现 %d）" % (c, added, len(tables[c])))

ok = all(all(k in tables[c] for k in KEYS) for c in CODES)
four = len(set(frozenset(tables[c]) for c in CODES[:4])) == 1
lzh = set(tables[u"lzh"]) - set(tables[u"zh_cn"]) == {u"language.name", u"language.region"}
print(u"  [%s] 新键五份齐全" % (u"OK" if ok else u"!!"))
print(u"  [%s] 四语言键集合一致（各 %d）" % (u"OK" if four else u"!!", len(tables[u"zh_cn"])))
print(u"  [%s] lzh 差集仍是那两把（lzh %d）" % (u"OK" if lzh else u"!!", len(tables[u"lzh"])))
sys.exit(0 if (ok and four and lzh) else 1)
