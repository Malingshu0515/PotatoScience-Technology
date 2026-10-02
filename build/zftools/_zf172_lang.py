# -*- coding: utf-8 -*-
u"""_zf172_lang.py —— 范围从 3×3 区块改成 5×5×5 区块后，把说明里的字样跟平（五语言）"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
KEYS = (u"tooltip.potato_s_t.gravity_device",)

PATS = [(u"3×3 区块", u"5×5×5 区块"), (u"3×3 チャンク", u"5×5×5 チャンク"),
        (u"3x3 чанк", u"5x5x5 чанк"), (u"3x3 chunks", u"5x5x5 chunks"),
        (u"三乘三區", u"五乘五乘五區"), (u"3×3 區", u"5×5×5 區")]

changed = 0
for c in CODES:
    p = os.path.join(LANG, c + u".json")
    d = json.loads(io.open(p, encoding="utf-8").read())
    hit = False
    for k in KEYS:
        v = d.get(k)
        if not isinstance(v, str):
            continue
        nv = v
        for a, b in PATS:
            nv = nv.replace(a, b)
        if nv != v:
            d[k] = nv
            hit = True
            print(u"  %-6s %s" % (c, nv[:74]))
    if hit:
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        changed += 1
print(u"改了 %d 份" % changed)
ok = True
for c in CODES:
    d = json.loads(io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read())
    for k in KEYS:
        v = d.get(k, u"")
        if u"3×3" in v or u"3x3" in v or u"三乘三" in v:
            print(u"  [!!] %s 还有旧字样：%s" % (c, k))
            ok = False
four = True
tabs = [frozenset(json.loads(io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read()))
        for c in CODES[:4]]
four = len(set(tabs)) == 1
print(u"  [%s] 旧字样清零" % (u"OK" if ok else u"!!"))
print(u"  [%s] 四语言键集合仍一致" % (u"OK" if four else u"!!"))
sys.exit(0 if (ok and four) else 1)
