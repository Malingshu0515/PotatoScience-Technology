# -*- coding: utf-8 -*-
"""ZF139 取证（六）：NeoForge 里到底哪个事件是「每个活体每 tick」。只读。"""
import io, re, zipfile

NF = r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235\4566e557485e2cf5843d29a9c44795f5f731d36d\neoforge-21.1.235-sources.jar"
z = zipfile.ZipFile(NF)
names = z.namelist()
OUT = []
hits = [n for n in names if "LivingTickEvent" in n or re.search(r"event/tick/.*TickEvent", n)]
OUT.append("=== 文件名命中 ===")
OUT.extend(hits)
OUT.append("")
for n in names:
    if not n.endswith(".java"):
        continue
    s = z.read(n).decode("utf-8", "replace")
    if "LivingTickEvent" in s:
        OUT.append("=== 提到 LivingTickEvent 的文件：%s ===" % n)
        for m in re.finditer(r"[^\n]*LivingTickEvent[^\n]*", s):
            OUT.append("   " + m.group(0).strip())
        if "class LivingTickEvent" in s:
            i = s.find("class LivingTickEvent")
            OUT.append(s[max(0, i - 200):i + 700])
OUT.append("")
OUT.append("=== event/tick 包下的类 ===")
OUT.extend(sorted(n for n in names if "/event/tick/" in n))
txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src6.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok")
