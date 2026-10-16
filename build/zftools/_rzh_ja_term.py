import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "ja_jp.json"), encoding="utf-8"))
for term in ("引力装置", "重力装置"):
    ks = [k for k, v in d.items() if term in v]
    print("%s : %d keys" % (term, len(ks)))
    for k in ks[:8]:
        print("    %s" % k)
