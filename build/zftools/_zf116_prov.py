# -*- coding: utf-8 -*-
u"""_zf116_prov.py —— 把 ZF116 三件素材登进 `build/用户素材/_来源凭据.json`

（ZF110 那轮的四张 PNG 已登记；本轮三件盔甲漏了，这轮补上 —— 凭据是"原字节可追"的账本。）
只加键，不动别条；写完回读断言。
"""
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
USERART = r"E:\PotatoST\build\用户素材"
PROV = os.path.join(USERART, "_来源凭据.json")

JOBS = [
    ("星璨钢胸甲.png", "star_steel_chestplate.png"),
    ("星璨钢护腿.png", "star_steel_leggings.png"),
    ("星璨钢靴子.png", "star_steel_boots.png"),
]

raw = io.open(PROV, encoding="utf-8").read()
prov = json.loads(raw)
before = len(prov)

for srcname, dstname in JOBS:
    p = os.path.join(USERART, srcname)
    if not os.path.exists(p):
        print(u"  !! 找不到 %s" % srcname)
        continue
    blob = open(p, "rb").read()
    key = dstname
    if key in prov:
        print(u"  [幂等] %s 已在凭据里" % key)
        continue
    prov[key] = {
        "原名": srcname,
        "sha1": hashlib.sha1(blob).hexdigest(),
        "bytes": len(blob),
        "说明": (u"用户 ZF116 放的素材（%s）⇒ 原字节复制成 textures/item/%s"
                 u"（16x16/8位/RGBA，零半透明）；模型 layer0 从 minecraft:item/iron_* "
                 u"改成 potato_s_t:item/star_steel_*" % (srcname, dstname)),
    }
    print(u"  [OK] 登记 %-28s %d B  sha1 %s"
          % (key, len(blob), hashlib.sha1(blob).hexdigest()[:12]))

io.open(PROV, "w", encoding="utf-8", newline="\n").write(
    json.dumps(prov, indent=2, ensure_ascii=False) + "\n")

back = json.loads(io.open(PROV, encoding="utf-8").read())
print(u"\n  凭据条目 %d -> %d" % (before, len(back)))
ok = all(j[1] in back for j in JOBS)
print(u"  %s 回读断言：三件都进凭据了" % (u"[OK]" if ok else u"[!!]"))
# 顺带确认老条目没被弄丢
print(u"  %s 老条目仍在（oil_bucket.jpg / star_steel_helmet.png / music_disc_jasmine_flower.png）"
      % (u"[OK]" if all(k in back for k in
                        ("oil_bucket.jpg", "star_steel_helmet.png",
                         "music_disc_jasmine_flower.png")) else u"[!!]"))
sys.exit(0 if ok else 1)
