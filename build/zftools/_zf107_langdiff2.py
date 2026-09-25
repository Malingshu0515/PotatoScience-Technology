import io,json,sys,os
sys.stdout.reconfigure(encoding="utf-8")
BK=r"C:\PotatoST救援\zf107_pre\src\main\resources\assets\potato_s_t\lang"
LIVE=r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
for l in ("zh_cn","en_us","ja_jp","ru_ru"):
    a=json.load(io.open(os.path.join(BK,l+".json"),encoding="utf-8"))
    b=json.load(io.open(os.path.join(LIVE,l+".json"),encoding="utf-8"))
    ch=[(k,a[k],b.get(k)) for k in a if k in b and a[k]!=b[k]]
    print("==",l,"改值",len(ch))
    for k,x,y in ch: print("   ",k,"\n      改前:",x,"\n      现在:",y)
print("=== mtime ===")
for l in ("zh_cn","en_us"):
    print(l, os.path.getmtime(os.path.join(LIVE,l+".json")))
