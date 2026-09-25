import re
L=open("src/main/java/com/potatost/mod/TerminalBlock.java",encoding="utf-8").read().splitlines()
for i,l in enumerate(L,1):
    s=l.strip()
    if re.search(r'(use\(|useWithoutItem|InteractionResult|cycle|nextMode|shift|Mode\.|wrench|Wrench|setMode|player)', s) and not s.startswith("import"):
        print("%4d| %s" % (i, s[:150]))
