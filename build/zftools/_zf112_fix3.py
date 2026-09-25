# -*- coding: utf-8 -*-
u"""_zf112_fix3.py —— 修 ZF112 之后变红的三门（都是我自己写的断言/基准被后一轮作废）

1. `_zf107_verify.py` 的 F3：查档案里写着「417 键」这个字样 —— ZF112 的 §9 只写了「417」，
   补上「键」字（**改文档，不改断言**）。
2. `_zf109_verify.py`：它把「ModBlocks 的方块物品一共 35 个」当成账目基准 ——
   ZF112 加了锂电池构造间 ⇒ 36。**基准跟着涨**（这条本来就是防漏挂的，本意不变）。
3. `_zf111_verify.py`：「键序与改前件完全相同」—— 那条是给 ZF111 自己那轮写的；
   ZF112 在**中间**插了 9 个键 ⇒ 顺序必然变。改成正确的不变量：
   **改前件那份键序必须是今天键序的子序列**（相对顺序没被打乱）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
fails = []


def patch(path, pairs, name):
    t = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        if t.count(old) != 1:
            fails.append(u"%s：锚点命中 %d 次（%s）" % (name, t.count(old), old[:40]))
            continue
        t = t.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"  [OK] %s" % name)


# ① 档案：补「417 键」字样
patch(DOC, [(u"四语言 408 → **417**（9 个新键）", u"四语言 408 → **417 键**（9 个新键）")], u"档案 F3")

# ② _zf109 的基准 35 → 36
patch(os.path.join(ZT, u"_zf109_verify.py"), [
    (u'check(u"ModBlocks 的方块物品一共 35 个（账目基准）", len(registered) == 35,',
     u'check(u"ModBlocks 的方块物品一共 36 个（账目基准；ZF112 加了锂电池构造间）",\n'
     u'          len(registered) == 36,'),
], u"_zf109 基准")

# ③ _zf111 的键序检查：改成子序列
t = io.open(os.path.join(ZT, u"_zf111_verify.py"), encoding="utf-8").read()
old = u'        eq(u"%s 键序与改前件完全相同" % name, list(before), list(now))'
new = (u'        # ⚠ ZF112 起改成「相对顺序」：后一轮会在中间插键，键序必然变\n'
       u'        now_keys = list(now)\n'
       u'        eq(u"%s 改前件那份键序仍是今天键序的子序列（相对顺序没乱）" % name,\n'
       u'           list(before), [k for k in now_keys if k in before])')
if t.count(old) != 1:
    fails.append(u"_zf111 键序锚点命中 %d 次" % t.count(old))
else:
    io.open(os.path.join(ZT, u"_zf111_verify.py"), "w", encoding="utf-8",
            newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK] _zf111 键序检查")

print(u"失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
