import re,os
base=r"src\main\java\com\potatost\mod"
files=["PressRecipes.java","MicroCrusherRecipes.java","MachineRecipes.java","BlastFurnaceRecipes.java","AlloySmelterRecipes.java","SaltDecomposerRecipes.java","SaltDryerBlockEntity.java","GeneratorBlockEntity.java","LowGeneratorBlockEntity.java"]
for f in files:
    p=os.path.join(base,f)
    if not os.path.exists(p): print("MISSING",f); continue
    txt=open(p,encoding="utf-8").read()
    print("="*20,f,len(txt),"chars")
    for i,l in enumerate(txt.splitlines(),1):
        s=l.strip()
        if not s or s.startswith("//") or s.startswith("*") or s.startswith("/*"): continue
        if re.search(r'(add|register|put|new |\bNeed\b|\brecipe\b|Result|ItemStack|->)', s) and not s.startswith("import") and not s.startswith("package"):
            print(f"{i:5d}| {s[:150]}")
