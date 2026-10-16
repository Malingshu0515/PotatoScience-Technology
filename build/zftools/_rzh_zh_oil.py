import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
print("zh 指南 crude.p1:", d["potato_s_t.guide.entry.oil.crude.p1"][-90:])
print()
print("zh 手册里提到这台机器的所有位置：")
for k, v in d.items():
    if "采油机" in v:
        print("  %-56s %s" % (k, v[:120]))
