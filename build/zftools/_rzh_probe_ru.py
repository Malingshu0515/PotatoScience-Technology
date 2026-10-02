import io, json, os, re
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
K = "tooltip.potato_s_t.electric_blast_furnace"
for loc in ("zh_cn","en_us","ja_jp","ru_ru","lzh"):
    p = os.path.join(LANG, loc + ".json")
    d = json.load(io.open(p, encoding="utf-8"))
    print(loc, "injson=", K in d, "keys=", len(d))
    if K in d:
        v = d[K]
        print("   ru-line-marker=", repr(v[:60]))
        print("   mentions wrench:",
              any(w in v for w in ("ключ","wrench","レンチ","扳手","扳鉗")))
