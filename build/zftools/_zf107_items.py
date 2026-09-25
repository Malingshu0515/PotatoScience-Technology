import re,os
base="src/main/java/com/potatost/mod/"
t=open(base+"ModItems.java",encoding="utf-8").read()
for m in re.finditer(r'ITEMS\.register\("([a-z_0-9]+)",\s*\n?\s*\(\)\s*->\s*([^\n]{0,110})', t):
    if m.group(1) in ("oil_bucket","diesel_bucket","gasoline_bucket","high_pressure_tank","wrench","terminal"):
        print(m.group(1), "->", m.group(2).strip())
print("--- classes ---")
for cls in ["OilBucketItem.java","HighPressureTankItem.java"]:
    L=open(base+cls,encoding="utf-8").read().splitlines()
    print("="*10, cls)
    for i,l in enumerate(L[:24],1): print("%3d| %s" % (i, l.rstrip()[:140]))
print("=== machine power intake pattern (one machine) ===")
L=open(base+"MicroCrusherBlockEntity.java",encoding="utf-8").read()
for m in re.finditer(r'[^\n]*(Capabilities\.EnergyStorage|receiveEnergy|extractEnergy|IEnergyStorage)[^\n]*', L):
    print("   ", m.group(0).strip()[:150])
