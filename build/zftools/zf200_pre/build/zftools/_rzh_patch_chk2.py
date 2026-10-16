import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
p = json.load(io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_patch_B_ja_jp.json", encoding="utf-8"))
d = json.load(io.open(os.path.join(LANG, "ja_jp.json"), encoding="utf-8"))
ch = [k for k in p if p[k] != d.get(k)]
print("ja_jp patch: %d keys total, %d changed" % (len(p), len(ch)))
for k in ch[:12]:
    print("  %s" % k)
    print("     now : %s" % d.get(k, "")[:100])
    print("     new : %s" % p[k][:100])
