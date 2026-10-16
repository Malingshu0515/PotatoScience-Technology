import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "en_us.json"), encoding="utf-8"))
for k, v in d.items():
    if "Oil Pump" in v or "Oil Extractor" in v:
        print("  %-52s %s" % (k, v[:60]))
