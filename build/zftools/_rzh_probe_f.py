import io, json, os
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
K = "advancements.potato_s_t.oil_pump.description"
L = []
for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"):
    d = json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8"))
    L.append("%-6s: %s" % (l, d[K]))
io.open(r"E:\PotatoST\build\zftools\_rzh_zfail_vals.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
