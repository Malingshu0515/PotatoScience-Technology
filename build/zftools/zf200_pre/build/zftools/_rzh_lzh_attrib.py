# -*- coding: utf-8 -*-
"""Are the 3 lzh_verify/facts failures MINE, or pre-existing from other lines?
Compare lzh vs zh for the flagged keys, and check the 3 fact-diff nodes against HEAD."""
import io
import json
import subprocess

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = ROOT + r"\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"

L = []
zh = json.load(io.open(LANG + r"\zh_cn.json", encoding="utf-8"))
lzh = json.load(io.open(LANG + r"\lzh.json", encoding="utf-8"))
head = {}
for loc in ("zh_cn", "lzh"):
    head[loc] = json.loads(subprocess.run(
        [GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/%s.json" % loc],
        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))

L.append("=== B5 flagged keys: lzh vs zh (value identical == same-as-Chinese) ===")
for k in ("potato_s_t.guide.category.materials", "message.potato_s_t.gravity.charging"):
    L.append("%s" % k)
    L.append("   zh  now: %r" % zh.get(k))
    L.append("   lzh now: %r" % lzh.get(k))
    L.append("   zh  HEAD: %r   (lzh HEAD: %r)" % (head["zh_cn"].get(k), head["lzh"].get(k)))
    L.append("   identical now? %s   |  was identical at HEAD? %s"
             % (zh.get(k) == lzh.get(k), head["zh_cn"].get(k) == head["lzh"].get(k)))
    L.append("")

L.append("=== B4 flagged key: newline count ===")
k = "tooltip.potato_s_t.fluid_converter"
L.append("   zh  now: %d newlines" % zh.get(k, "").count("\n"))
L.append("   lzh now: %d newlines" % lzh.get(k, "").count("\n"))
L.append("   zh  HEAD: %d newlines" % head["zh_cn"].get(k, "").count("\n"))
L.append("   lzh HEAD: %d newlines" % head["lzh"].get(k, "").count("\n"))
L.append("   zh changed vs HEAD? %s" % (zh.get(k) != head["zh_cn"].get(k)))
L.append("   lzh changed vs HEAD? %s" % (lzh.get(k) != head["lzh"].get(k)))
L.append("")

L.append("=== the 3 fact-diff nodes: did ZH change vs HEAD (rewritten as jokes)? ===")
for node in ("diesel_generator", "oil_pump", "starfall"):
    k = "advancements.potato_s_t.%s.description" % node
    L.append("%s" % node)
    L.append("   zh  HEAD: %s" % head["zh_cn"].get(k, "").replace("\n", "\\n")[:110])
    L.append("   zh  now : %s" % zh.get(k, "").replace("\n", "\\n")[:110])
    L.append("   lzh HEAD: %s" % head["lzh"].get(k, "").replace("\n", "\\n")[:110])
    L.append("   lzh now : %s" % lzh.get(k, "").replace("\n", "\\n")[:110])
    L.append("   → zh rewritten as a joke? %s" % (zh.get(k) != head["zh_cn"].get(k)))
    L.append("   → lzh untouched by this round? %s" % (lzh.get(k) == head["lzh"].get(k)))
    L.append("")

io.open(ROOT + r"\build\zftools\_rzh_lzh_attrib.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
