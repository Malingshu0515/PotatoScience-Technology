import io, json, os
p = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_patch_B_ja_jp.json"
d = json.load(io.open(p, encoding="utf-8"))
n = 0
for k in ("potato_s_t.configuration.section.gravity_device",
          "potato_s_t.configuration.section.gravity_device.button"):
    if d[k] == "引力装置":
        d[k] = "重力装置"
        n += 1
io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("fixed %d keys" % n)
