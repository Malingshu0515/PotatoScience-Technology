# -*- coding: utf-8 -*-
import io, json, re
a = json.load(io.open(r"E:\PotatoST\build\zftools\_rzh_lzh_in2.json", encoding="utf-8"))
b = json.load(io.open(r"E:\PotatoST\build\zftools\_rzh_lzh_out2.json", encoding="utf-8"))
print("keys equal:", list(a) == list(b), len(a), len(b))
for k in a:
    pa = re.findall(r"%[sd]|%%", a[k]); pb = re.findall(r"%[sd]|%%", b.get(k, ""))
    if pa != pb:
        print("PLACEHOLDER", k, pa, pb)
    if a[k].count("\\n") != b.get(k, "").count("\\n"):
        print("NEWLINE", k, a[k].count("\\n"), b.get(k, "").count("\\n"))
for tok in ["FE", "mB", "tick", "JEI", "Shift", "Y=", "c:"]:
    na = sum(a[k].count(tok) for k in a); nb = sum(b.get(k, "").count(tok) for k in b)
    if na != nb:
        print("TOKEN", tok, na, nb)
print("done")

# 附加：与原文逐字相同者、图纸网格、编码体检
same = [k for k in a if a[k] == b[k]]
print("\nidentical-to-source (%d):" % len(same))
for k in same:
    print("   ", k, "=", a[k])
for k in ["tooltip.potato_s_t.alloy_smelter", "tooltip.potato_s_t.diesel_generator_controller"]:
    la = [l for l in a[k].split("\n") if re.match(r"^[0-9 |\uff5c]+$", l)]
    lb = [l for l in b[k].split("\n") if re.match(r"^[0-9 |\uff5c]+$", l)]
    print("\nGRID", k, "lines", len(la), "identical:", la == lb)
    for x, y in zip(la, lb):
        if x != y:
            print("   DIFF", repr(x), repr(y))
raw = io.open(r"E:\PotatoST\build\zftools\_rzh_lzh_out2.json", "rb").read()
print("\nBOM:", raw[:3] == b"\xef\xbb\xbf", "CR:", b"\r" in raw, "bytes:", len(raw))
# 繁体/简体混用体检：正文里是否残留常见简体形
SIMP = u"电气钢铁铜铝钛钨铀钴镍锰银锂矿锭盐层发动机结构时间开关无这们来会后与车转输过进还让说请记设认识别对应该实际检测范围图纸划线终极热压滤剂氢温冻带块区场类种样单双顶头视复击弹减坠寻处换权态护费"
hits = {}
for k, v in b.items():
    h = sorted(set(c for c in v if c in SIMP))
    if h:
        hits[k] = u"".join(h)
print("\nsimplified-glyph residue in %d keys:" % len(hits))
for k, h in list(hits.items())[:20]:
    print("   ", k, h)
