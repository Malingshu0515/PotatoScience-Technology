import io,os,re,sys
sys.stdout.reconfigure(encoding="utf-8")
T=r"E:\PotatoST\build\zftools"
files=["_zf71_verify.py","_zf73_verify.py","_zf73_repro.py","_zf75_verify.py","_zf78_verify.py","_zf79_verify.py","_zf80_verify.py","_zf81_verify.py","_zf82_verify.py","_zf93_verify.py","_zf95_verify.py","_zf96_verify.py","_zf97_verify.py","_zf98_verify.py","_zf100_verify.py","_zf100_recipe_guard.py","_zf101_verify.py","_zf102_verify.py","_zf103_verify.py"]
for f in files:
    p=os.path.join(T,f)
    if not os.path.exists(p):
        print("MISSING",f); continue
    L=io.open(p,encoding="utf-8").read().split("\n")
    hits=[(i+1,l) for i,l in enumerate(L) if re.search(r"\b350\b",l)]
    print("=== %s  (%d 处)" % (f,len(hits)))
    for i,l in hits: print("   %4d| %s" % (i,l.strip()[:170]))
