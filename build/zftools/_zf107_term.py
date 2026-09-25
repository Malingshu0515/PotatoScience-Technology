import re
L=open("src/main/java/com/potatost/mod/TerminalBlockEntity.java",encoding="utf-8").read().splitlines()
print("total lines",len(L))
for i,l in enumerate(L,1):
    s=l.strip()
    if any(k in s for k in (u"端子",u"网络",u"INPUT",u"OUTPUT",u"注入",u"分配",u"接收",u"推送",u"//",u"*")):
        if s.startswith("import") or s.startswith("package"): continue
        print("%4d| %s" % (i, s[:150]))
