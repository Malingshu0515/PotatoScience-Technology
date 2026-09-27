# -*- coding: utf-8 -*-
u"""_zf148_recon4.py —— ZF148 侦察⑥：写书要用到的**真实**素材（配方 id / 机器名 / 关键文案）。

教程书里的每一句都要有出处，不能编。这里把：
  ① 全部配方 id（73 条）
  ② 机器 / 电力 / 化工 / 星际 相关的中文名与 tooltip 原文
  ③ 相关方块与物品的注册名
捞成一份可读清单（stdout，UTF-8），写书时对照着用。
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang", "zh_cn.json")
RECIPE = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
BLOCKSTATE = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "blockstates")
MODELS_ITEM = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "models", "item")

lang = json.load(open(LANG, encoding=u"utf-8"))


def pr(s=u""):
    print(s)


pr(u"================ ① 配方 id 全表（%d 条） ================" % len(os.listdir(RECIPE)))
by_type = {}
for fn in sorted(os.listdir(RECIPE)):
    if not fn.endswith(u".json"):
        continue
    d = json.load(open(os.path.join(RECIPE, fn), encoding=u"utf-8"))
    t = d.get(u"type", u"?")
    by_type.setdefault(t, []).append(fn[:-5])
for t in sorted(by_type):
    pr(u"---- %s（%d）----" % (t, len(by_type[t])))
    for n in sorted(by_type[t]):
        pr(u"   " + n)

pr()
pr(u"================ ② 机器 / 电力 相关文案（zh_cn 原文） ================")
TERMS = [u"micro_crusher", u"hydraulic_press", u"terminal", u"low_generator", u"generator",
         u"solar", u"lithium", u"battery", u"cable", u"wire", u"power_capturer", u"group_energy",
         u"filling", u"fluid_pump", u"fluid_exchanger", u"tank", u"oil_pump", u"distillation",
         u"combustion", u"hydrodesulfurization", u"air_separator", u"ammonia", u"acidic",
         u"electrolyzer", u"blast_furnace", u"alloy", u"salt", u"starfall", u"star_chart",
         u"star_steel", u"vibranium", u"guide"]
seen = set()
for k in sorted(lang):
    kl = k.lower()
    if any(t in kl for t in TERMS):
        if k in seen:
            continue
        seen.add(k)
        pr(u"  %-62s %s" % (k, lang[k]))

pr()
pr(u"================ ③ 方块 / 物品注册名（只列机器类） ================")
mods = open(os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod", "ModItems.java"),
            encoding=u"utf-8").read()
modb = open(os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod", "ModBlocks.java"),
            encoding=u"utf-8").read()
pat = re.compile(r'register(?:Block|Vibranium|Armor)?\(?\s*"([a-z0-9_]+)"')
names = sorted(set(pat.findall(mods)) | set(pat.findall(modb)))
pr(u"  共 %d 个" % len(names))
pr(u"  " + u", ".join(names))
