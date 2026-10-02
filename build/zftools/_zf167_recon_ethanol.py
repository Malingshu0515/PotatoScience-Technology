# -*- coding: utf-8 -*-
u"""_zf16x_recon_ethanol.py —— 从**盘上的 jar** 现抠「别的 mod 的乙醇」叫什么、挂什么标签

用户原话：「一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）」。

⇒ 不能靠记忆写 `c:ethanol`。盘上有两个联动 jar（`release/ImmersiveEngineering-*.jar`、
`libs/*.jar`），直接看它们的流体 id 与 `data/*/tags/fluid/*.json`。
"""
import glob
import io
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"

JARS = []
JARS += sorted(glob.glob(os.path.join(ROOT, "release", "*.jar")))
JARS += sorted(glob.glob(os.path.join(ROOT, "libs", "*.jar")))
JARS += sorted(glob.glob(os.path.join(ROOT, "run", "server", "mods", "*.jar")))

for j in JARS:
    try:
        z = zipfile.ZipFile(j)
    except Exception as e:
        continue
    names = z.namelist()
    # ① 流体 id 里带 ethanol / alcohol 的
    fluids = [n for n in names
              if n.startswith(u"data/") and u"/tags/fluid" in n]
    hits = [n for n in names if u"ethanol" in n.lower() or u"alcohol" in n.lower()]
    tags = []
    for n in fluids:
        try:
            d = json.loads(z.read(n).decode("utf-8"))
        except Exception:
            continue
        vals = d.get(u"values", [])
        txt = json.dumps(vals, ensure_ascii=False)
        if u"ethanol" in txt.lower() or u"alcohol" in txt.lower():
            tags.append((n, txt[:160]))
    if hits or tags:
        print(u"\n================ %s ================" % os.path.basename(j))
        for n in sorted(hits)[:20]:
            print(u"  条目  %s" % n)
        for n, t in tags[:12]:
            print(u"  标签  %s\n        %s" % (n, t))
print(u"\n（以上为盘上所有 jar 里带 ethanol/alcohol 的条目与流体标签）")
