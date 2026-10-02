import io, re
t = io.open(r"docs\UpdateAnnouncement_EN.md", encoding="utf-8").read()
lines = t.split("\n")
out = ["total lines=%d" % len(lines), ""]
for i, l in enumerate(lines):
    if re.match(r"^#{1,4}\s", l):
        out.append("%5d | %s" % (i+1, l[:110]))
out.append("")
out.append("=== last 30 lines ===")
out.extend(lines[-30:])
io.open(r"build\zftools\_rzh_ann_probe.txt","w",encoding="utf-8",newline="\n").write("\n".join(out))
print("ok")
