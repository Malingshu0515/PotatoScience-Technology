import io, re
t = io.open(r"docs\开发档案.md", encoding="utf-8").read()
lines = t.split("\n")
L = []
L.append("total lines=%d" % len(lines))
L.append("")
L.append("=== all '### ' headings (first 120) ===")
for i, l in enumerate(lines):
    if l.startswith("### "):
        L.append("%6d  %s" % (i+1, l[:110]))
L.append("")
L.append("=== all lines containing 'ZF147' ===")
for i, l in enumerate(lines):
    if "ZF147" in l:
        L.append("%6d  %s" % (i+1, l[:180]))
L.append("")
L.append("=== lines containing '| ZF1' ===")
for i, l in enumerate(lines):
    if re.match(r"^\|\s*ZF1", l):
        L.append("%6d  %s" % (i+1, l[:150]))
io.open(r"build\zftools\_rzh_docs_probe2.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok")
