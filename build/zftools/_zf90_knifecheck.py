# -*- coding: utf-8 -*-
u"""_zf90_knifecheck.py —— 上线前自检：新加的那几把刀的锚点必须**正好命中一次**

反证脚本自己也会断言（命中数 != 1 就报 FAIL），但那要等整套跑完（十来分钟）才知道；
这里先花一秒查一遍。只读。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
CHECKS = [
    (u"K29 银板 layer0", r"src\main\resources\assets\potato_s_t\models\item\silver_plate.json",
     u'"layer0": "potato_s_t:item/iron_plate"'),
    (u"K30 柴油桶 layer0", r"src\main\resources\assets\potato_s_t\models\item\diesel_bucket.json",
     u'"layer0": "potato_s_t:item/diesel_bucket"'),
    (u"K32 汽油桶 layer0", r"src\main\resources\assets\potato_s_t\models\item\gasoline_bucket.json",
     u'"layer0": "potato_s_t:item/gasoline_bucket"'),
    (u"K31 公告活体数字", r"docs\UpdateAnnouncement_EN.md",
     u"(5 models still do this)"),
    (u"K26 凭据 sha1", os.path.join("build", u"用户素材", u"_来源凭据.json"),
     u'"sha1": "f2885b6208dfb09c51df12172f4f6264031e0237"'),
    (u"K27 档案 ZF89 行", r"docs\开发档案.md", u"| ZF89 | **新建 `zf89_pre`**"),
    (u"K28 高炉 OBJ UV", r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj",
     u"v 2.000000 0.000000 3.000000\nvt 1 1"),
]
fails = []
for label, rel, anchor in CHECKS:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        fails.append(u"%s：文件不在 %s" % (label, rel))
        continue
    t = io.open(p, encoding="utf-8", errors="replace").read()
    n = t.count(anchor)
    print(u"  %-18s 命中 %d 次  %s" % (label, n, u"OK" if n == 1 else u"!! 必须正好 1 次"))
    if n != 1:
        fails.append(u"%s：命中 %d 次" % (label, n))
print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
