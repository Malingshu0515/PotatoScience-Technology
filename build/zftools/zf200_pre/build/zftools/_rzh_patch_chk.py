import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
K = "potato_s_t.guide.entry.materials.blast_alloy.p1"
for f, loc in (("_rzh_patch_A_en_us.json","en_us"),("_rzh_patch_A_ru_ru.json","ru_ru"),
               ("_rzh_patch_B_ja_jp.json","ja_jp"),("_rzh_patch_B_lzh.json","lzh")):
    p = json.load(io.open(os.path.join(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools", f), encoding="utf-8"))
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    same = p[K] == d[K]
    print("%-30s untouched? %s   len=%d" % (f, same, len(p[K])))
