import io, json, os, re, sys
sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
from _rzh_guide_merge import BANNED, nums, PH
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
p = json.load(io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_patch_B_ja_jp.json", encoding="utf-8"))
out = []
bad = 0
for k, v in sorted(p.items()):
    src = zh.get(k, "")
    probs = []
    if not v.strip(): probs.append("EMPTY")
    if v == src: probs.append("SAME-AS-ZH")
    for rule, needles in BANNED["ja_jp"]:
        h = [n for n in needles if n in v]
        if h: probs.append("%s:%s" % (rule, ",".join(h)))
    if v.count("$(br2)") != src.count("$(br2)"):
        probs.append("br2 %d!=%d" % (v.count("$(br2)"), src.count("$(br2)")))
    if sorted(PH.findall(v)) != sorted(PH.findall(src)):
        probs.append("ph")
    ms = [n for n in nums(src) if n not in nums(v)]
    if ms and len(ms) > max(1, len(nums(src))//2): probs.append("nums %s" % ms)
    if probs:
        bad += 1
        out.append("FAIL %s" % k)
        out.append("     %s" % ",".join(probs))
        out.append("     %s" % v[:130])
out.insert(0, "ja_jp patch: %d keys, %d with problems" % (len(p), bad))
io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_ja_check.txt","w",encoding="utf-8",newline="\n").write("\n".join(out))
print("problems=%d / %d" % (bad, len(p)))
