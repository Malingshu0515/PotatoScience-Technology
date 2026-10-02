import io
t = io.open(r"docs\开发档案.md", encoding="utf-8").read()
lines = t.split("\n")
out = []
for i, l in enumerate(lines):
    if l.startswith("### 4.15") or l.startswith("### 4.86") or l.startswith("### 4.87"):
        out.append("line %d | %s" % (i+1, l[:95]))
io.open(r"build\zftools\_rzh_docs_probe3.txt","w",encoding="utf-8",newline="\n").write("\n".join(out))
print("ok")
