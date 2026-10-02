import io, re, collections
t = io.open(r"docs\开发档案.md", encoding="utf-8").read()
c = collections.Counter()
for m in re.finditer(r"(?m)^### (4\.\d+)", t):
    c[m.group(1)] += 1
out = ["duplicates:"]
for k, v in sorted(c.items(), key=lambda kv: [int(x) for x in kv[0].split(".")]):
    if v > 1:
        out.append("  %s x%d" % (k, v))
out.append("")
out.append("4.15x present: %s" % [k for k in c if k.startswith("4.15")])
io.open(r"build\zftools\_rzh_num_probe.txt","w",encoding="utf-8",newline="\n").write("\n".join(out))
print("ok")
