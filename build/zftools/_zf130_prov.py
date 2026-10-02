# -*- coding: utf-8 -*-
# _zf130_prov.py —— 把 ZF130 四件素材登进 build/用户素材/_来源凭据.json
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
USERART = r"E:\PotatoST\build\用户素材"
PROV = os.path.join(USERART, "_来源凭据.json")

JOBS = [
    (u"锂电池构造器上和下面_001.png", "lithium_battery_plant_top.png",
     u"原字节复制成 textures/block/lithium_battery_plant_top.png；"
     u"lithium_battery_plant 的模型 cube_all -> cube_bottom_top，top/bottom 指这张、side 指原有的"),
    (u"柴油发电机控制器顶部&底部_001.png", "diesel_generator_controller_top.png",
     u"原字节复制成 textures/block/diesel_generator_controller_top.png；"
     u"diesel_generator_controller 的模型 cube_all -> cube_bottom_top，top/bottom 指这张"),
    (u"银线_001.png", "silver_wire.png",
     u"原字节复制成 textures/item/silver_wire.png；"
     u"silver_wire 的模型 layer0 从 minecraft:item/iron_nugget 改成自己的图"),
    (u"银线轴_001.png", "silver_wire_spool.png",
     u"原字节复制成 textures/item/silver_wire_spool.png；"
     u"silver_wire_spool 的模型 layer0 从 minecraft:item/iron_ingot 改成自己的图"),
]

raw = io.open(PROV, encoding="utf-8").read()
prov = json.loads(raw)
before = len(prov)

for srcname, key, note in JOBS:
    p = os.path.join(USERART, srcname)
    if not os.path.exists(p):
        print(u"  !! 找不到 %s" % srcname)
        continue
    key2 = key if key.endswith(".png") else key + ".png"
    if key2 in prov:
        print(u"  [幂等] %s 已在凭据里" % key2)
        continue
    blob = open(p, "rb").read()
    prov[key2] = {
        u"原名": srcname,
        "sha1": hashlib.sha1(blob).hexdigest(),
        "bytes": len(blob),
        u"说明": note,
    }
    print(u"  [OK] 登记 %-36s %d B  sha1 %s"
          % (key2, len(blob), hashlib.sha1(blob).hexdigest()[:12]))

io.open(PROV, "w", encoding="utf-8", newline="\n").write(
    json.dumps(prov, indent=2, ensure_ascii=False) + "\n")

back = json.loads(io.open(PROV, encoding="utf-8").read())
print(u"\n  凭据条目 %d -> %d" % (before, len(back)))
ok = all((k if k.endswith(".png") else k + ".png") in back for _, k, _ in JOBS)
print(u"  %s 回读：四件都在" % (u"[OK]" if ok else u"[!!]"))
print(u"  %s 老条目未丢（oil_bucket.jpg / star_steel_helmet.png）"
      % (u"[OK]" if all(k in back for k in ("oil_bucket.jpg", "star_steel_helmet.png")) else u"[!!]"))
sys.exit(0 if ok else 1)
