import io, json
cur = json.load(io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang\en_us.json", encoding="utf-8"))
sub = json.load(io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_patch_A_en_us.json", encoding="utf-8"))
diff = [k for k in sub if sub[k] != cur.get(k)]
print("en_us: subagent 稿 vs 已提交，不同的键 = %d" % len(diff))
for k in diff[:6]:
    print("  %s" % k)
    print("     已提交: %s" % cur.get(k, "")[:110])
    print("     它的稿: %s" % sub[k][:110])
