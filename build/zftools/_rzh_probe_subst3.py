import io, json, os
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
L = []
for loc, needles in (("ja_jp", ["粗チタン","粗ヴィブラニウム","チタンの原石","ヴィブラニウムの原石"]),
                     ("ru_ru", ["Рудный титан","Рудный вибраниум"])):
    d = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    for n in needles:
        hits = [(k, v.count(n)) for k, v in d.items() if n in v]
        L.append("%s  %-24s total=%d  keys=%s" % (loc, n, sum(c for _, c in hits), [k for k, _ in hits]))
io.open(r"E:\PotatoST\build\zftools\_rzh_subst_recount.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
