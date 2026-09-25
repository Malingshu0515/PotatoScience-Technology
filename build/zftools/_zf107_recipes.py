import json,os,glob
d=r"src\main\resources\data\potato_s_t\recipe"
def nm(x):
    if isinstance(x,str): return x
    if isinstance(x,dict):
        if "item" in x: return x["item"]
        if "tag" in x: return "#"+x["tag"]
    return str(x)
rows=[]
for f in sorted(glob.glob(os.path.join(d,"*.json"))):
    j=json.load(open(f,encoding="utf-8"))
    t=j.get("type","")
    res=j.get("result") or j.get("results")
    if isinstance(res,dict):
        r=res.get("id","?")+" x"+str(res.get("count",1))
    elif isinstance(res,list):
        r=";".join((x.get("id","?")+" x"+str(x.get("count",1))) for x in res)
    else: r=str(res)
    if "shaped" in t:
        ing=[]
        for row in j.get("pattern",[]):
            for ch in row:
                if ch!=" ":
                    k=nm(j.get("key",{}).get(ch,"?"))
                    if k not in ing: ing.append(k)
        ing="+".join(ing)
    elif "shapeless" in t:
        ing="+".join(dict.fromkeys(nm(i) for i in j.get("ingredients",[])))
    elif "smelting" in t or "blasting" in t:
        ing="[cook] "+nm(j.get("ingredient"))+" "+str(j.get("cookingtime"))+"t"
    else:
        ing="?"
    rows.append((os.path.basename(f)[:-5],t.replace("minecraft:","").replace("crafting_",""),r,ing))
print(f"{'file':46s} {'type':10s} {'result':44s} ingredients")
for a,b,c2,d2 in rows:
    print(f"{a:46s} {b:10s} {c2:44s} {d2}")
