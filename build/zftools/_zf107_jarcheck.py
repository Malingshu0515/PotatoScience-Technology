import zipfile,sys,hashlib,io,json
sys.stdout.reconfigure(encoding="utf-8")
J=r"E:\PotatoST\build\libs\potato_s_t-0.11.jar"
z=zipfile.ZipFile(J)
names=z.namelist()
adv=[n for n in names if n.startswith("data/potato_s_t/advancement/") and n.endswith(".json")]
lang=[n for n in names if n.startswith("assets/potato_s_t/lang/")]
print("jar =",J)
print("size =",__import__("os").path.getsize(J))
print("sha1 =",hashlib.sha1(open(J,"rb").read()).hexdigest())
print("advancement 条目 =",len(adv))
print("lang 条目 =",len(lang),lang)
print("探针残留 =",[n for n in names if "Zf107" in n or "Check" in n])
bad=[n for n in names if any(ord(ch)>127 for ch in n)]
print("非 ASCII 路径 =",bad)
d=json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
print("zh_cn 键数 =",len(d))
print("成就键 =",len([k for k in d if k.startswith("advancements.")]))
# 与盘上逐字节比
import glob,os
same=diff=0
for n in adv:
    p=os.path.join(r"E:\PotatoST\src\main\resources",n)
    if open(p,"rb").read()==z.read(n): same+=1
    else: diff+=1; print("  差异:",n)
print("与盘上逐字节相同 =",same,"不同 =",diff)
