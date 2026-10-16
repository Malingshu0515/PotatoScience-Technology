import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
L = []
for k in ("po.landing",):
    pass
print("=== zh 手册：这些位置现在写了什么 ===")
for k, why in (("potato_s_t.guide.entry.materials.blast_alloy.p2", "合金炉配方"),
               ("potato_s_t.guide.entry.power.generation.p2", "太阳能板"),
               ("potato_s_t.guide.entry.starfall.sky_and_star.p1", "星图"),
               ("potato_s_t.guide.entry.starfall.star_steel.p2", "星璨钢/振金")):
    print("### %s (%s)" % (k.split(".")[-2:], why))
    print(d[k][:200])
    print()
