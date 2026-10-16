import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
for f, loc in (("_rzh_patch_B_ja_jp.json","ja_jp"),("_rzh_patch_B_lzh.json","lzh"),
               ("_rzh_patch_A_en_us.json","en_us"),("_rzh_patch_A_ru_ru.json","ru_ru")):
    p = json.load(io.open(os.path.join(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools", f), encoding="utf-8"))
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    ch = sum(1 for k in p if p[k] != d.get(k))
    print("%-30s keys=%d changed=%d" % (f, len(p), ch))
