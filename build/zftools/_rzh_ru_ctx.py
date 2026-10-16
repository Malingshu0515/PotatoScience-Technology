import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "ru_ru.json"), encoding="utf-8"))
for k in ("potato_s_t.guide.entry.getting_started.rules.p1",
          "potato_s_t.guide.entry.power.fluids.p2",
          "potato_s_t.guide.entry.power.wiring.p2"):
    v = d[k]
    i = v.find("именно")
    print("### %s" % k)
    print(v[max(0,i-110):i+110])
    print()
