# -*- coding: utf-8 -*-
u"""_zf118_regate.py —— 两处**别人那一轮的门**要跟着这一轮改（都写清理由）

① `_zf114_verify.py` 的 **F5**：它断言「用户明确先不给配方 ⇒ 盘上不该有星轨坠的配方」。
   用户 ZF118 给了配方 ⇒ 这条**一半失效**：星轨坠该有了；粗振金仍然没有（"先不给"对它仍成立）
   ⇒ 拆成 F5 / F5b 两条，判据分开。

② `_zf117_verify.py` 的 **D7**：它断言「老键里**只有**状态文案那一处被改值」（拿 zf117_pre 比）。
   现在润色线正在改**进度文案的值**（`advancements.*.description` 好几条）⇒ 这条立刻红，
   但它红得**没道理**：那些值不是我的地盘，改值是润色线的工作（交接文档 §5.1 明说）。
   ⇒ 按 `_zf107_verify.py` 立下的先例：**改值只打印、不改判**；
      我自己那处（`status.no_acid`）仍然必须**还在**（被revert 就要红）。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools\\"
fails, notes = [], []


def patch(path, pairs, label):
    raw = io.open(path, encoding="utf-8").read()
    for old, new, why in pairs:
        if new in raw and old not in raw:
            notes.append(u"%s：%s（已经是新写法，跳过）" % (label, why))
            continue
        if raw.count(old) != 1:
            fails.append(u"%s：%s 锚点出现 %d 次" % (label, why, raw.count(old)))
            continue
        raw = raw.replace(old, new, 1)
        notes.append(u"%s：%s" % (label, why))
    try:
        compile(raw, path, "exec")
    except SyntaxError as e:
        fails.append(u"%s：改完语法错 %s" % (label, e))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(raw)
    back = io.open(path, encoding="utf-8").read()
    if back != raw:
        fails.append(u"%s：回读不一致" % label)


F5_OLD = (u'    check(u"F5 用户明确先不给配方 ⇒ 盘上不该有它的配方 JSON",\n'
          u'          not os.path.exists(os.path.join(RECIPES, u"starfall_pendant.json"))\n'
          u'          and not os.path.exists(os.path.join(RECIPES, u"raw_vibranium.json")))\n')
F5_NEW = (u'    # ⚠ ZF118（用户：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」）\n'
          u'    #   ⇒ 星轨坠**现在有配方了**：这条 F5 原来断言"两样都没有配方"，现在只一半成立 ——\n'
          u'    #     星轨坠必须有（ZF118 的图纸，走生成器表 `_zf45_recipes.py` 生成）；\n'
          u'    #     粗振金仍然没有（「先不给」对它依然有效）。两条判据分开写。\n'
          u'    check(u"F5 星轨坠现在**有**配方（ZF118 用户给的图纸）",\n'
          u'          os.path.exists(os.path.join(RECIPES, u"starfall_pendant.json")))\n'
          u'    check(u"F5b 粗振金仍然没有配方（「先不给」对它仍成立）",\n'
          u'          not os.path.exists(os.path.join(RECIPES, u"raw_vibranium.json")))\n')

D7_OLD = (u'        changed = sorted(k for k in old if k in lang[l] and old[k] != lang[l][k])\n'
          u'        eq(u"D7 %s：老键里只有状态文案那一处被改值" % l, [ACID_FIX_KEY], changed)\n')
D7_NEW = (u'        changed = sorted(k for k in old if k in lang[l] and old[k] != lang[l][k])\n'
          u'        # ⚠ ZF118 放宽（有理由）：润色线在改**进度文案的值**（`advancements.*.description`），\n'
          u'        #   那不是我的地盘（交接文档 §5.1 明说值归他们）⇒ 别人的改值**只打印、不改判**\n'
          u'        #   （先例：`_zf107_verify.py` 的"非本轮改动"那几行）。\n'
          u'        #   但**我自己那一处必须还在** —— 谁把状态文案改回 10 mB / 6000 mB，这条就红。\n'
          u'        eq(u"D7 %s：本轮那处状态文案的改值还在" % l, [ACID_FIX_KEY],\n'
          u'           [k for k in changed if k == ACID_FIX_KEY])\n'
          u'        others = [k for k in changed if k != ACID_FIX_KEY]\n'
          u'        if others:\n'
          u'            print(u"   （%s：非本轮的改值 %d 处 —— %s）" % (l, len(others), others[:6]))\n')

patch(ZT + u"_zf114_verify.py", [(F5_OLD, F5_NEW, u"F5 拆成两条（星轨坠有配方 / 粗振金没有）")],
      u"_zf114_verify.py")
patch(ZT + u"_zf117_verify.py", [(D7_OLD, D7_NEW, u"D7 改成「我的那处还在」+ 别人改值只打印")],
      u"_zf117_verify.py")

print(u"\n".join(u"  [OK] " + n for n in notes))
print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
