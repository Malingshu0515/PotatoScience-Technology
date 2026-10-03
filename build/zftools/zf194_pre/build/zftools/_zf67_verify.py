# -*- coding: utf-8 -*-
"""_zf67_verify.py —— ZF67 常驻校验：**工具必须挂原版的"能附魔"标签**

用户报：「附魔台不给钛合金附魔」。根因不是附魔能力（我们给的是 25，比金的 22 还高），
而是附魔台挑附魔时用的是 `EnchantmentHelper.getAvailableEnchantmentResults()` 里那句
`stack.isPrimaryItemFor(enchantment)` —— 判据是原版那几张 **物品标签**：
`#minecraft:swords` / `#minecraft:pickaxes`（再串到 `enchantable/sword`、`enchantable/sharp_weapon`、
`enchantable/mining`、`enchantable/mining_loot`、`enchantable/durability`、`enchantable/vanishing`）。
ZF66 那两把工具一个都没挂 ⇒ **附魔能力再高也挑不出任何一条附魔**（探针实测：花费 30 级、候选 0 条）。

⚠ 这里的标签是**原版功能标签**，与"默认只兼容粗矿/矿石/锭"那条 `c:` 兼容规则无关 ——
不挂 = 连原版附魔都用不了，属于"功能缺失"而不是"兼容性取舍"。

退出码 0 = 全过。
"""
import io
import json
import os
import re
import sys

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, r"src\main\resources")
ITEM_TAGS = os.path.join(RES, r"data\minecraft\tags\item")
MODITEMS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java")

# 工具 id -> 该进的原版标签（原版就是靠这两张串起整条附魔链的）
WANT = {
    "titanium_alloy_sword": "swords",
    "titanium_alloy_pickaxe": "pickaxes",
}

fails = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


items = read(MODITEMS)
print("== ① 两个 id 真的注册了（标签里写的名字必须存在）==")
for tool in WANT:
    check(re.search(r'ITEMS\.register\("%s"' % tool, items) is not None,
          "ModItems 注册了 %s" % tool)

print()
print("== ② 原版功能标签文件（data/minecraft/tags/item/）==")
for tool, tag in WANT.items():
    p = os.path.join(ITEM_TAGS, tag + ".json")
    if not os.path.isfile(p):
        check(False, "缺 data/minecraft/tags/item/%s.json（少了它 = 这条工具附不了魔）" % tag)
        continue
    d = json.loads(read(p))
    vals = d.get("values", [])
    check(d.get("replace") is False,
          "%s.json 用 replace:false（= 追加到原版那张表，不是整张覆盖）" % tag)
    check("potato_s_t:" + tool in vals, "%s.json 里有 potato_s_t:%s" % (tag, tool))
    check(len(vals) == 1,
          "%s.json 只加我们自己这一条（读到 %d 条，别顺手覆盖原版）" % (tag, len(vals)))
    check(all(v.startswith("potato_s_t:") for v in vals),
          "%s.json 里没有别的命名空间的东西" % tag)

print()
print("== ③ 反查：每个工具都必须在某张功能标签里（不许有漏的）==")
tagged = set()
for tag in WANT.values():
    p = os.path.join(ITEM_TAGS, tag + ".json")
    if os.path.isfile(p):
        for v in json.loads(read(p)).get("values", []):
            tagged.add(v.split(":")[-1])
for tool in WANT:
    check(tool in tagged, "%s 挂在原版功能标签上" % tool)

print()
print("== ④ 记录一下对照（原版这两张标签都指向一整套 enchantable/*）==")
print("     swords   -> enchantable/sword -> sharp_weapon / fire_aspect / durability / vanishing")
print("     pickaxes -> enchantable/mining / mining_loot / durability / vanishing")

print()
print("失败项 = %d" % len(fails))
for m in fails:
    print("   - " + m)
sys.exit(1 if fails else 0)
