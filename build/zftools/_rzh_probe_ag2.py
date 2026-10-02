import io, json, os
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
d = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
L = ["=== zh keys mentioning 银线 or 端子 (may be where a rate would live) ==="]
for k, v in d.items():
    if "银线" in v or "端子" in v:
        L.append("  %s -> %s" % (k, v.replace("\n","\\n")[:170]))
io.open(r"E:\PotatoST\build\zftools\_rzh_ag_zh.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
