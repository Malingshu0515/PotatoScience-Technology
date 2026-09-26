# -*- coding: utf-8 -*-
u"""_zf134_survey.py —— 只读摸底：配方目录现状 + 生成器表里有没有斧子 + 活体数字

ZF134 要做的只有一件事：给 ZF133 的**星璨钢斧**补一张**原版斧头图纸**（材料换成星璨钢锭）。
动手前先把三件事数清楚：
  ① 盘上 recipe 目录现在几份、各类型几条（`crafting_shaped` 是活体数字，别照抄旧值）；
  ② 生成器表 `_zf45_recipes.py` 里 RECIPES / SMITHING 各几条；
  ③ 有没有已经存在的斧子配方（有的话就不是"新增"而是"改"）。
"""
import collections
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
GEN = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")

names = sorted(n for n in os.listdir(RDIR) if n.endswith(u".json"))
types = collections.Counter(
    json.loads(io.open(os.path.join(RDIR, n), encoding="utf-8").read()).get("type")
    for n in names)
print(u"盘上 recipe 目录：%d 份" % len(names))
for k, v in types.most_common():
    print(u"   %-34s %d" % (k, v))
print(u"含 axe 的配方文件：%s" % ([n for n in names if u"axe" in n] or u"（没有）"))

src = io.open(GEN, encoding="utf-8").read()
print(u"\n生成器表 `_zf45_recipes.py`：")
print(u"   RECIPES 条目（dict(name=...)）：%d" % len(re.findall(r"(?m)^\s*dict\(name=", src)))
print(u"   里面提到 axe 的：%s" % (re.findall(r".*axe.*", src) or u"（没有）"))

for key in (u"star_steel_ingot", u"star_steel_axe"):
    print(u"   提到 %-16s 的行：%d" % (key, len(re.findall(key, src))))

print(u"\n物品是否已注册（ModItems.java）：")
items = io.open(os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java"),
                encoding="utf-8").read()
for ident in (u"star_steel_axe", u"titanium_alloy_axe"):
    print(u"   %-20s %s" % (ident, u"有" if (u'register("%s"' % ident) in items else u"没有"))
