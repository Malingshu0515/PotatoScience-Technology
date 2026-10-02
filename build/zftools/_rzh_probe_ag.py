import io, json, os
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
K = ["tooltip.potato_s_t.silver_wire","item.potato_s_t.silver_wire",
     "tooltip.potato_s_t.silver_wire_spool","item.potato_s_t.silver_wire_spool",
     "advancements.potato_s_t.silver_wire.description"]
d = dict((l, json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8")))
         for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"))
L = []
for k in K:
    if k not in d["zh_cn"]:
        L.append("### %s  <key not in zh_cn>" % k); L.append("")
        continue
    L.append("### %s" % k)
    for l in ("zh_cn","en_us","ja_jp","ru_ru","lzh"):
        L.append("%-6s: %s" % (l, d[l].get(k,"<MISSING>").replace("\n","\\n")))
    L.append("")
# which zh keys mention 16134 / 2048
L.append("=== zh keys containing 16134 or 2048 ===")
for k, v in d["zh_cn"].items():
    if "16134" in v or "2048" in v:
        L.append("  %s -> %s" % (k, v.replace("\n","\\n")[:160]))
io.open(r"E:\PotatoST\build\zftools\_rzh_ag_probe.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
