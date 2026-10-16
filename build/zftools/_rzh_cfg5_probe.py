import io, json, os
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
KEYS = ["potato_s_t.configuration.black_hole.scan_radius_blocks.tooltip",
        "potato_s_t.configuration.black_hole.lifetime_seconds.tooltip",
        "potato_s_t.configuration.black_hole.pull_entities.tooltip",
        "potato_s_t.configuration.black_hole.void_damage.tooltip",
        "potato_s_t.configuration.black_hole.one_shot.tooltip"]
d = {l: json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8"))
     for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh")}
L = []
for k in KEYS:
    L.append("### %s" % k.replace("potato_s_t.configuration.",""))
    for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"):
        L.append("  %-6s %s" % (l, d[l][k]))
    L.append("")
io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_cfg5.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
