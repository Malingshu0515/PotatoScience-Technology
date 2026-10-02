# -*- coding: utf-8 -*-
u"""_zf172_cap.py —— 说明里的上限字样 1200 → 1500（ZF170b 已把上限提到 1500，五语言漏改了）"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
KEY = u"tooltip.potato_s_t.gravity_device"
REPL = [(u"1200", u"1500"), (u"1,200", u"1,500"), (u"千二百", u"千五百")]
for c in CODES:
    p = os.path.join(LANG, c + u".json")
    d = json.loads(io.open(p, encoding="utf-8").read())
    v = d.get(KEY, u"")
    nv = v
    for a, b in REPL:
        nv = nv.replace(a, b)
    if nv != v:
        d[KEY] = nv
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        print(u"  %-6s 已改" % c)
tabs = [frozenset(json.loads(io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read()))
        for c in CODES[:4]]
print(u"  [%s] 四语言键集合仍一致" % (u"OK" if len(set(tabs)) == 1 else u"!!"))
sys.exit(0 if len(set(tabs)) == 1 else 1)
