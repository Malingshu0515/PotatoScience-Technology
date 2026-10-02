# -*- coding: utf-8 -*-
u"""_zf167_texture.py —— 饮料罐装机的模型与贴图 + 两个物品的模型（ZF167）

用户没给这一轮的贴图（原话里只有配方与数值）⇒ 按本工程的老规矩：
**自己起名字的占位文件**（不是让模型去指别人的贴图），并在 `docs/贴图清单.md` 的「待画」表里挂号。

  机器两张：`beverage_canning_machine_{top,side}.png` = `micro_crusher_{top,side}.png` 的
           **逐字节副本**（占位；一个像素都没改 ⇒ 回读必须字节相同）
  两个物品：空铝罐 → `minecraft:item/glass_bottle`；可乐 → `minecraft:item/honey_bottle`
           （**借原版**，与振金套当初借铁套同一条口径；「借原版」的活体数字 13 → 15，门要跟平）

跑法：python build\\zftools\\_zf167_texture.py
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
BTEX = os.path.join(ASSETS, "textures", "block")
MODEL_B = os.path.join(ASSETS, "models", "block")
MODEL_I = os.path.join(ASSETS, "models", "item")
BSTATE = os.path.join(ASSETS, "blockstates")

PAIRS = [(u"micro_crusher_top.png", u"beverage_canning_machine_top.png"),
         (u"micro_crusher_side.png", u"beverage_canning_machine_side.png")]

BLOCK_MODEL = u"""{
  "parent": "minecraft:block/block",
  "textures": {
    "top": "potato_s_t:block/beverage_canning_machine_top",
    "side": "potato_s_t:block/beverage_canning_machine_side",
    "particle": "potato_s_t:block/beverage_canning_machine_side"
  },
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "up": { "uv": [0, 0, 16, 16], "texture": "#top" },
        "down": { "uv": [0, 0, 16, 16], "texture": "#top" },
        "north": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "south": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "east": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "west": { "uv": [0, 0, 16, 16], "texture": "#side" }
      }
    }
  ]
}
"""

JSONS = [
    (os.path.join(BSTATE, u"beverage_canning_machine.json"),
     u'{ "variants": { "": { "model": "potato_s_t:block/beverage_canning_machine" } } }\n'),
    (os.path.join(MODEL_B, u"beverage_canning_machine.json"), BLOCK_MODEL),
    (os.path.join(MODEL_I, u"beverage_canning_machine.json"),
     u'{ "parent": "potato_s_t:block/beverage_canning_machine" }\n'),
    (os.path.join(MODEL_I, u"empty_aluminum_can.json"),
     u'{\n  "parent": "minecraft:item/generated",\n  "textures": {\n'
     u'    "layer0": "minecraft:item/glass_bottle"\n  }\n}\n'),
    (os.path.join(MODEL_I, u"cola.json"),
     u'{\n  "parent": "minecraft:item/generated",\n  "textures": {\n'
     u'    "layer0": "minecraft:item/honey_bottle"\n  }\n}\n'),
]

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    print(u"① 机器两张占位贴图（micro_crusher 的逐字节副本）")
    for src_name, dst_name in PAIRS:
        src, dst = os.path.join(BTEX, src_name), os.path.join(BTEX, dst_name)
        if not os.path.exists(src):
            check(u"源贴图在（%s）" % src_name, False)
            continue
        if os.path.exists(dst):
            same = sha(src) == sha(dst)
            check(u"%s 已存在且与源逐字节相同（幂等）" % dst_name, same)
            continue
        io.open(dst, "wb").write(open(src, "rb").read())
        check(u"写出 %s（%d 字节）" % (dst_name, os.path.getsize(dst)),
              sha(src) == sha(dst), u"sha256 与源相同")
        notes.append(u"%s = %s 的副本（**占位**，已挂贴图清单待画）" % (dst_name, src_name))

    print(u"\n② 模型 / blockstate（5 个 JSON）")
    for path, text in JSONS:
        rel = os.path.relpath(path, ROOT)
        if os.path.exists(path):
            cur = io.open(path, encoding="utf-8").read()
            check(u"%s 已存在且内容相同（幂等）" % os.path.basename(path), cur == text)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        check(u"写出 %s" % rel, os.path.exists(path))

    print(u"\n③ 回读：JSON 能解析 + 指向的贴图/模型真的在")
    for path, _text in JSONS:
        d = json.loads(io.open(path, encoding="utf-8").read())
        name = os.path.basename(path)
        if name == u"beverage_canning_machine.json" and u"textures" in d:
            for key in (u"top", u"side", u"particle"):
                tex = d[u"textures"][key].split(u":", 1)[1]
                p = os.path.join(ASSETS, "textures", (tex + u".png").replace(u"/", os.sep))
                check(u"方块模型 %s → %s 在盘上" % (key, tex), os.path.exists(p))
        if name in (u"empty_aluminum_can.json", u"cola.json"):
            layer0 = d.get(u"textures", {}).get(u"layer0", u"")
            check(u"%s 借原版 %s（本工程「待画」口径）" % (name, layer0),
                  layer0.startswith(u"minecraft:item/"), layer0)

    print(u"\n④ 借原版物品贴图的活体数字（门要跟平）")
    borrowed = []
    for fn in sorted(os.listdir(MODEL_I)):
        if not fn.endswith(u".json"):
            continue
        d = json.loads(io.open(os.path.join(MODEL_I, fn), encoding="utf-8").read())
        layer0 = d.get(u"textures", {}).get(u"layer0", u"")
        if isinstance(layer0, str) and layer0.startswith(u"minecraft:"):
            borrowed.append(fn[:-5])
    print(u"   借原版的物品模型 %d 个：%s" % (len(borrowed), u"、".join(sorted(borrowed))))
    check(u"空铝罐与可乐都在借原版名单里",
          u"empty_aluminum_can" in borrowed and u"cola" in borrowed)

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
