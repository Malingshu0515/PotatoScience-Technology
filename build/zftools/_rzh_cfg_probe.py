# -*- coding: utf-8 -*-
"""Which config tooltips still carry AI flavour (dash / colloquial / filler) per locale?"""
import io
import json
import os

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
LOCS = ["zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"]

BAD = {
    "zh_cn": ["！", "——", "—", "……", "...", "可以", "能够", "就能", "即", "想想", "别", "吧", "呢"],
    "en_us": ["!", " - ", "—", "–", "...", " you can ", " can be ", " just ", "merely", "don't"],
    "ja_jp": ["！", "—", "……", "...", "できます", "ことができ", "ましょう", "ください"],
    "ru_ru": ["!", "—", "–", "...", "…", " можно ", " можете ", "просто ", "кстати"],
    "lzh": ["！", "——", "……", "...", "即可", "則可", "亦能"],
}

out = []
for loc in LOCS:
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    ks = sorted(k for k in d if k.startswith("potato_s_t.configuration"))
    out.append("===== %s（%d 条）=====" % (loc, len(ks)))
    for k in ks:
        v = d[k]
        hit = [b for b in BAD[loc] if b in v]
        if hit:
            out.append("  %-62s %s" % (k.replace("potato_s_t.configuration.", ""), ",".join(hit)))
            out.append("      %s" % v)
    out.append("")

# also dump full text of the config tooltips for the 3 languages, for rewriting
out.append("===== 全文（四语并列）=====")
data = {l: json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8")) for l in LOCS}
for k in sorted(data["zh_cn"]):
    if not k.startswith("potato_s_t.configuration"):
        continue
    out.append("### %s" % k)
    for l in LOCS:
        out.append("  %-6s %s" % (l, data[l][k]))
    out.append("")

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_cfg_probe.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
