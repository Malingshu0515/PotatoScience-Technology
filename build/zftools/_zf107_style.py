import json,re
for f in ["zh_cn","en_us","ja_jp","ru_ru"]:
    d=json.load(open("src/main/resources/assets/potato_s_t/lang/%s.json"%f,encoding="utf-8"))
    print("="*8,f,len(d))
    n=0
    for k,v in d.items():
        if k.startswith("gui.potato_s_t.recipe") or "tooltip.potato_s_t.titanium_alloy_set" in k or k.startswith("block.potato_s_t.acidic") or k.startswith("fluid_type"):
            print("  ",k,"=",v); n+=1
            if n>=6: break
print("=== EBF structure constants ===")
t=open("src/main/java/com/potatost/mod/ElectricBlastFurnaceStructure.java",encoding="utf-8").read()
for m in re.finditer(r'[^\n]*(SIZE|WIDTH|HEIGHT|RADIUS|25|3x3|结构)[^\n]*', t):
    s=m.group(0).strip()
    if s.startswith("import"): continue
    print("   ",s[:150])
