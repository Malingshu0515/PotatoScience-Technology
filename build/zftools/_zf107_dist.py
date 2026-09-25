import re
t=open("src/main/java/com/potatost/mod/DistillationOperatorBlockEntity.java",encoding="utf-8").read()
print("--- distillation outputs ---")
for m in re.finditer(r'[^\n]*(ModFluids\.[A-Z_]+|DIESEL|GASOLINE|NAPHTHA|BITUMEN|output|Output)[^\n]*', t):
    s=m.group(0).strip()
    if s.startswith("import"): continue
    print("  ", s[:150])
