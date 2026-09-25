import json,os,re
root=r"src\main\resources\assets\potato_s_t\lang\en_us.json"
d=json.load(open(root,encoding="utf-8"))
items={}
for k,v in d.items():
    m=re.match(r"^(item|block)\.potato_s_t\.(.+)$",k)
    if m: items[m.group(2)]=(m.group(1),v)
print("items/blocks in lang =",len(items))
java=""
for f in ("ModItems.java","ModBlocks.java"):
    java+=open(os.path.join(r"src\main\java\com\potatost\mod",f),encoding="utf-8").read()+"\n"
reg=re.findall(r'register\(\s*"([a-z0-9_]+)"',java)
print("registered ids =",len(reg))
missing=[r for r in reg if r not in items]
print("registered but no lang name:",missing)
only=[k for k in items if k not in reg]
print("lang but not in ModItems/ModBlocks:",only)
print("---- registered ids with names ----")
for r in reg:
    t,n=items.get(r,("?","?"))
    print(f"{r:34s} {t:5s} {n}")
