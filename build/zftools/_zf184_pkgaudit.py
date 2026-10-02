# -*- coding: utf-8 -*-
u"""_zf184_pkgaudit.py —— 0.14 成品体检（用户问「打包了吗 没打的话打一遍 jar」时用）。

跑法：python build\\zftools\\_zf184_pkgaudit.py
"""
import hashlib
import io
import json
import os
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
A = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
B = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


ha, hb = sha(A), sha(B)
print(u"release  %s  %d B" % (ha, os.path.getsize(A)))
print(u"build    %s  %d B" % (hb, os.path.getsize(B)))
print(u"逐字节一致（成品 == 构建产物）：%s" % (ha == hb))
print(u"与 .sha1 文件一致：%s" % (io.open(A + u".sha1", encoding="ascii").read().strip() == ha))
z = zipfile.ZipFile(A)
n = z.namelist()
zh = json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
lzh = json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8"))
print(u"class %d ｜ 配方 %d ｜ 进度 %d ｜ 键 zh_cn %d ｜ lzh %d"
      % (len([x for x in n if x.endswith(u".class")]),
         len([x for x in n if x.startswith(u"data/potato_s_t/recipe/") and x.endswith(u".json")]),
         len([x for x in n if x.startswith(u"data/potato_s_t/advancement/") and x.endswith(u".json")]),
         len(zh), len(lzh)))
print(u"探针 class：%s" % ([x for x in n if u"Check.class" in x] or u"无"))
checks = {
    u"ZF184 猛砸吃附魔（伤害类型 + 斩首处理器）":
        u"data/potato_s_t/damage_type/vibranium_slam.json" in n
        and any(u"VibraniumBeheading.class" in x for x in n),
    u"ZF182 斩首 tooltip 第 4 行": u"tooltip.potato_s_t.vibranium_sword.4" in zh,
    u"ZF180 装备可附魔（9 个类型标签）":
        all(u"data/minecraft/tags/item/%s.json" % t in n for t in
            (u"head_armor", u"chest_armor", u"leg_armor", u"foot_armor", u"swords",
             u"pickaxes", u"axes", u"shovels", u"hoes")),
    u"ZF178 磁铁块 + 6 个粗矿块贴图":
        all(u"assets/potato_s_t/textures/block/%s.png" % i in n for i in
            (u"magnet_block", u"raw_aluminum_block", u"raw_cobalt_block", u"raw_nickel_block",
             u"raw_silver_block", u"raw_tungsten_block", u"raw_uranium_block")),
    u"ZF166 流体转化器": any(u"FluidConverterBlockEntity.class" in x for x in n),
    u"版本号 0.14": u'version="0.14"' in z.read(u"META-INF/neoforge.mods.toml").decode("utf-8"),
}
bad = 0
for k, v in checks.items():
    print((u"  [OK]   " if v else u"  [FAIL] ") + k)
    bad += 0 if v else 1
print(u"失败 = %d" % bad)
sys.exit(1 if bad else 0)
