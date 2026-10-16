import io, json, os, re
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
for loc in ("en_us","zh_cn","ja_jp","ru_ru"):
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    hits = {k: v for k, v in d.items() if re.search(r"[Oo]il (Pump|Extractor)|Нефтяной насос|採油|采油|オイルポンプ|採掘機", v)}
    print("=== %s ===" % loc)
    for k, v in sorted(hits.items()):
        if k == "block.potato_s_t.oil_pump": continue
        print("  %-56s %s" % (k.split(".")[-2:], v[:100]))
    print("  block.oil_pump =", d["block.potato_s_t.oil_pump"])
    print()
