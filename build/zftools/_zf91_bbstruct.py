# -*- coding: utf-8 -*-
r"""_zf91_bbstruct.py —— 看清 `.bbmodel` 的结构：分组/原点/旋转，以及"到底是不是同一版模型"

要点：Free/mesh 模型里，mesh 的顶点可能是**相对该元素原点**的；分组还可能带 origin/rotation。
不算清楚这些，"包围盒"就是错的（第一版就差点被这一点带偏）。
顺便跟我们手里那份 OBJ 的 19 个盒子逐个比尺寸。
只读。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"
OBJ = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"

d = json.loads(io.open(BB, encoding="utf-8").read())

print(u"== 顶层键 ==")
print(u"  %s" % sorted(d.keys()))
print(u"\n== outliner（前两层）==")
for item in d.get("outliner", [])[:6]:
    if isinstance(item, dict):
        print(u"  group: name=%s  origin=%s  rotation=%s  children=%d  keys=%s"
              % (item.get("name"), item.get("origin"), item.get("rotation"),
                 len(item.get("children", [])), sorted(item.keys())))
    else:
        print(u"  元素 uuid=%s" % item)

print(u"\n== 第一个 mesh 的完整结构（截断打印）==")
els = d.get("elements", [])
e0 = els[0]
print(u"  键：%s" % sorted(e0.keys()))
for k in sorted(e0.keys()):
    v = e0[k]
    s = json.dumps(v, ensure_ascii=False)
    print(u"    %-14s %s" % (k, s[:300]))

print(u"\n== 19 个 mesh 的 origin / rotation / 顶点范围 ==")
for i, e in enumerate(els):
    vs = list(e.get("vertices", {}).values())
    xs = [v[0] for v in vs]; ys = [v[1] for v in vs]; zs = [v[2] for v in vs]
    print(u"  #%02d %-16s origin=%-22s rot=%-8s X %7.2f..%-7.2f Y %7.2f..%-7.2f Z %7.2f..%-7.2f"
          % (i, (e.get("name") or u"")[:16], str(e.get("origin")), str(e.get("rotation")),
             min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

print(u"\n== 我们那份 OBJ 的 19 个盒子（块）==")
vs, quads = [], []
for raw in io.open(OBJ, encoding="utf-8", errors="replace"):
    t = raw.split()
    if not t:
        continue
    if t[0] == "v":
        vs.append(tuple(float(x) for x in t[1:4]))
    elif t[0] == "f":
        quads.append([vs[int(a.split("/")[0]) - 1] for a in t[1:]])
for i in range(0, len(quads), 6):
    grp = quads[i:i + 6]
    xs = [p[0] for q in grp for p in q]
    ys = [p[1] for q in grp for p in q]
    zs = [p[2] for q in grp for p in q]
    print(u"  #%02d  块  X %6.3f..%-6.3f Y %6.3f..%-6.3f Z %6.3f..%-6.3f  = %5.3f x %5.3f x %5.3f"
          % (i // 6, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
