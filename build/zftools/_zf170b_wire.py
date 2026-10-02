# -*- coding: utf-8 -*-
u"""_zf170b_wire.py —— ZF170b：坍缩那句改三个数（搬走 / 码下 / 变掉落物），五语言"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
KEY = u"message.potato_s_t.gravity_done"
VALS = {
    u"zh_cn": u"黑洞坍缩：吸走 %s 个方块，码下 %s 个，放不下变成掉落物 %s 个",
    u"en_us": u"Black hole collapsed: %s blocks pulled, %s placed, %s dropped as items",
    u"ja_jp": u"ブラックホール崩壊：%s 個吸引、%s 個設置、%s 個はドロップになりました",
    u"ru_ru": u"Чёрная дыра схлопнулась: втянуто %s, размещено %s, выпало предметами %s",
    u"lzh": u"黑洞坍縮：吸 %s 塊，碼 %s 塊，不能置者墮為物 %s",
}
tables = {}
for c in CODES:
    p = os.path.join(LANG, c + u".json")
    d = json.loads(io.open(p, encoding="utf-8").read())
    old = d.get(KEY)
    d[KEY] = VALS[c]
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
    tables[c] = json.loads(io.open(p, encoding="utf-8").read())
    print(u"  %-6s %s → %s" % (c, (old or u"（无）")[:22], VALS[c][:34]))
ok = all(tables[c][KEY] == VALS[c] for c in CODES)
four = len(set(frozenset(tables[c]) for c in CODES[:4])) == 1
print(u"  [%s] 五份都改成三个数；四语言键集合一致（各 %d）" % (u"OK" if (ok and four) else u"!!",
                                                        len(tables[u"zh_cn"])))
sys.exit(0 if (ok and four) else 1)
