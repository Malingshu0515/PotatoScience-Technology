# -*- coding: utf-8 -*-
"""_zf154_gatefix.py —— 把 `_zf109_verify.py` 那两条采油机模型判据跟到新事实

`_zf109_verify.py`（采油机那一轮的门）原来钉的是：

    eq(u"方块模型父级 = cube_all", "minecraft:block/cube_all", bm.get("parent"))
    eq(u"方块模型贴图", "potato_s_t:block/oil_pump", bm.get("textures", {}).get("all"))

而 ZF154 按用户给的素材把模型改成了 `cube_bottom_top`（顶/底 = 新贴图、侧面 = 原贴图）
⇒ 这两条必然红。

**处理原则：判据不删、按新事实收紧**（不是放宽）：
  父级改成 `cube_bottom_top`；
  贴图从"一个 all 槽"改成"三个槽各自点名"（top / bottom / side）——
  这比原来那条**更严**：原来只查一个槽，现在三个都查，而且顶/底必须是新贴图、
  侧面必须仍是原贴图（这样"有没有偷懒把六面都换成新的"也被钉住了）。
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf109_verify.py"

OLD = (u'    eq(u"方块模型父级 = cube_all", "minecraft:block/cube_all", bm.get("parent"))\n'
       u'    eq(u"方块模型贴图", "potato_s_t:block/oil_pump", bm.get("textures", {}).get("all"))')
NEW = (u'    # 【0.12 ZF154 收紧】采油机按用户给的「顶部和底部」素材加上了顶/底渲染：\n'
       u'    #   父级 cube_all -> cube_bottom_top；贴图从"一个 all 槽"改成"三个槽各自点名"。\n'
       u'    #   ⚠ 这比原来**更严**：原来只查一个槽，现在三个都查，而且顶/底必须是新贴图、\n'
       u'    #     侧面必须仍是原贴图 ⇒ "有没有偷懒把六面都换成新的"也被钉住。\n'
       u'    eq(u"方块模型父级 = cube_bottom_top（0.12 ZF154 起）",\n'
       u'       "minecraft:block/cube_bottom_top", bm.get("parent"))\n'
       u'    eq(u"方块模型顶/底 = oil_pump_top", "potato_s_t:block/oil_pump_top",\n'
       u'       bm.get("textures", {}).get("top"))\n'
       u'    eq(u"方块模型底面 = oil_pump_top（顶底同一张）", "potato_s_t:block/oil_pump_top",\n'
       u'       bm.get("textures", {}).get("bottom"))\n'
       u'    eq(u"方块模型侧面 = oil_pump（原贴图，一个字节没动）", "potato_s_t:block/oil_pump",\n'
       u'       bm.get("textures", {}).get("side"))')

t = io.open(P, encoding="utf-8").read()
if NEW in t:
    print(u"  [幂等] 已经收紧过")
    sys.exit(0)
if t.count(OLD) != 1:
    print(u"  !! 锚点出现 %d 次，没写盘" % t.count(OLD))
    sys.exit(1)
out = t.replace(OLD, NEW)
try:
    ast.parse(out)
except SyntaxError as e:
    print(u"  !! 改后语法错误，没写盘：%s" % e)
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print(u"  [OK] 两条判据已跟到新事实（且更严）+ 语法自检通过")
