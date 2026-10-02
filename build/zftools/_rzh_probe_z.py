import io, json, os
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEYS = ["message.potato_s_t.battery_not_formed",
        "gui.potato_s_t.oil_pump.status.output_full",
        "item.potato_s_t.star_chart_tome",
        "advancements.potato_s_t.star_chart_tome.title",
        "advancements.potato_s_t.star_chart_tome.description",
        "tooltip.potato_s_t.oil_pump",
        "gui.potato_s_t.air_separator.status.output_full",
        "gui.potato_s_t.distillation.status.product_full"]
d = dict((l, json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8")))
         for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"))
L = []
for k in KEYS:
    L.append("### %s" % k)
    for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"):
        L.append("%-6s: %s" % (l, d[l].get(k, "<MISSING>").replace("\n","\\n")))
    L.append("")
io.open(r"E:\PotatoST\build\zftools\_rzh_zprobe.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
