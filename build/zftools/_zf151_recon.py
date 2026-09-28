# -*- coding: utf-8 -*-
u"""_zf151_recon.py —— ZF151 侦察：机器方块的「挖掘口径」现状盘点。

三件事一次说清：
  ① 盘上注册了哪些方块（从 ModBlocks / PotatoSTOres 扫）；
  ② `minecraft:tags/block/mineable/pickaxe.json` 里现在有哪些（谁漏了）；
  ③ 谁**自带 loot_table**、谁在 Java 里覆写了 `getDrops`、谁两样都没有（= 挖了不掉）。
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(ROOT, "src", "main", "resources")
TAG = os.path.join(RES, "data", "minecraft", "tags", "block", "mineable", "pickaxe.json")
LOOT = os.path.join(RES, "data", "potato_s_t", "loot_table", "blocks")

# ---- ① 注册的方块 ----
blocks = {}
for fn in sorted(os.listdir(JAVA)):
    if not fn.endswith(u".java") or not os.path.isfile(os.path.join(JAVA, fn)):
        continue
    t = io.open(os.path.join(JAVA, fn), encoding=u"utf-8").read()
    for m in re.finditer(r'BLOCKS\.register\(\s*"([a-z0-9_]+)"', t):
        blocks[m.group(1)] = fn

# ---- ③ Java 里覆写了 getDrops 的类 ----
drops_cls = set()
for fn in sorted(os.listdir(JAVA)):
    if not fn.endswith(u".java") or not os.path.isfile(os.path.join(JAVA, fn)):
        continue
    t = io.open(os.path.join(JAVA, fn), encoding=u"utf-8").read()
    if u"public List<ItemStack> getDrops(" in t:
        drops_cls.add(fn[:-5])

# ---- 方块 → 类名（从 ModBlocks 的 `new XxxBlock(` 抓） ----
owner = {}
t = io.open(os.path.join(JAVA, u"ModBlocks.java"), encoding=u"utf-8").read()
for m in re.finditer(r'BLOCKS\.register\(\s*"([a-z0-9_]+)"\s*,\s*\n?\s*\(\)\s*->\s*new\s+([A-Za-z0-9_]+)\(', t):
    owner[m.group(1)] = m.group(2)
for m in re.finditer(r'BLOCKS\.register\(\s*"([a-z0-9_]+)"[\s\S]{0,200}?new\s+([A-Za-z0-9_]+)\(', t):
    owner.setdefault(m.group(1), m.group(2))
t2 = io.open(os.path.join(JAVA, u"PotatoSTOres.java"), encoding=u"utf-8").read()
for m in re.finditer(r'BLOCKS\.register\(\s*"([a-z0-9_]+)"[\s\S]{0,200}?new\s+([A-Za-z0-9_]+)\(', t2):
    owner.setdefault(m.group(1), m.group(2))

# ---- ② 标签 ----
tag = set(json.loads(io.open(TAG, encoding=u"utf-8").read())[u"values"])
tag = set(x.split(u":", 1)[1] if x.startswith(u"potato_s_t:") else x for x in tag)

loot = set(f[:-5] for f in os.listdir(LOOT) if f.endswith(u".json"))

print(u"注册方块 %d 个" % len(blocks))
print(u"标签里 %d 个；有 loot_table %d 份；Java 覆写 getDrops 的类 %d 个"
      % (len(tag), len(loot), len(drops_cls)))

print(u"\n================ 谁不在 mineable/pickaxe 标签里 ================")
miss = sorted(b for b in blocks if b not in tag)
for b in miss:
    cls = owner.get(b, u"?")
    print(u"  %-34s 类 %-32s getDrops=%s loot=%s"
          % (b, cls, u"是" if cls in drops_cls else u"否", u"有" if b in loot else u"无"))

print(u"\n================ 两样都没有的（挖了不掉） ================")
for b in sorted(blocks):
    cls = owner.get(b, u"?")
    if b not in loot and cls not in drops_cls:
        print(u"  %-34s 类 %-32s 在标签里=%s" % (b, cls, u"是" if b in tag else u"否"))

print(u"\n================ 不在标签里、但也不在盘上的（标签里的野项） ================")
for b in sorted(tag):
    if b not in blocks and not b.startswith(u"#"):
        print(u"  " + b)

print(u"\n================ 方块 → 类 对照（供人工核对） ================")
for b in sorted(blocks):
    print(u"  %-36s %s" % (b, owner.get(b, u"?")))
