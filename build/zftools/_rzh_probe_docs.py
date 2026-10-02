import io, re
p = r"docs\开发档案.md"
t = io.open(p, encoding="utf-8").read()
L = []
L.append("=== headings containing 5 or 日志 or 变更 ===")
for m in re.finditer(r"(?m)^(#{1,4})\s*(.+)$", t):
    h = m.group(2)
    if "日志" in h or "变更" in h or h.startswith("§5") or h.startswith("5"):
        L.append("%-6s %s" % (m.group(1), h))
L.append("")
L.append("=== last lines mentioning ZF147 ===")
for m in re.finditer(r"(?m)^.*ZF147.*$", t):
    L.append(m.group(0)[:200])
L.append("")
L.append("=== tail 40 lines ===")
L.extend(t.split("\n")[-40:])
io.open(r"build\zftools\_rzh_docs_probe.txt","w",encoding="utf-8",newline="\n").write("\n".join(L))
print("ok len=%d" % len(t))
