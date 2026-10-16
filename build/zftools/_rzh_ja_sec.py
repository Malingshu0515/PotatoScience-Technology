import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "ja_jp.json"), encoding="utf-8"))
for k in sorted(x for x in d if x.startswith("potato_s_t.configuration.section")):
    print("%-58s %s" % (k.replace("potato_s_t.configuration.section.",""), d[k]))
print()
print("引力装置 count in ja:", sum(1 for v in d.values() if "引力装置" in v))
print("重力装置 count in ja:", sum(1 for v in d.values() if "重力装置" in v))
