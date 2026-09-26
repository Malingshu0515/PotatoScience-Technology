# -*- coding: utf-8 -*-
u"""_zf139_langdump.py —— 把四语言里振金那条说明 + 附近的锚点原样导出（只读），
给 ZF139 的新文案当底稿。"""
import io, json, sys

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
OUT = []
for loc in LOCALES:
    raw = io.open(LANG % loc, encoding="utf-8", newline=u"").read()
    obj = json.loads(raw)
    OUT.append(u"===== %s（%d 键）=====" % (loc, len(obj)))
    for k in (u"tooltip.potato_s_t.vibranium_set", u"tooltip.potato_s_t.star_steel_set"):
        OUT.append(u"--- %s ---" % k)
        OUT.append(obj[k])
    ks = list(obj.keys())
    i = ks.index(u"tooltip.potato_s_t.vibranium_set")
    OUT.append(u"--- 前后相邻键 ---")
    OUT.append(u"%s | %s | %s" % (ks[i - 1], ks[i], ks[i + 1]))
txt = u"\n".join(OUT)
io.open(u"build/zftools/_zf139_langdump.txt", u"w", encoding="utf-8", newline=u"\n").write(txt + u"\n")
print(u"ok")
