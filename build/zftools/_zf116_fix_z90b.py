# -*- coding: utf-8 -*-
u"""_zf116_fix_z90b.py —— 把 `_zf90_verify.py` 那条"板正好三张"收窄到 `*_plate.png`

原写法：`left = sorted(n for n in os.listdir(TEXI) if u"plate" in n)`
再断言 `left == [copper_plate, iron_plate, steel_plate]`。

**问题**：这是**子串**匹配 ⇒ `star_steel_chestplate.png`（"chestplate" 里含 "plate"）
被当成第四张板子，ZF116 一上线这条就红。但它**不是**这张门要保护的东西 ——
`plate.png` 是**通用板**（ZF90 删掉的那张），这条门的意图是
「通用板没了、只剩三张专用板」，而胸甲（chestplate）是原版就有的命名，本来就不该被数进来。

**改法**：收窄成 `n.endswith("_plate.png") or n == "plate.png"` ——
`copper_plate` / `iron_plate` / `steel_plate` 仍是三张，`plate.png` 若复活照样被抓
（"删除 = 剩下的是空的"那条断言仍在），而 `chestplate` 不再误伤。
**这不是放宽断言**：对这张门真正关心的东西（通用板 / 三张专用板）判据一条没少。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf90_verify.py"

raw = io.open(P, encoding="utf-8").read()
orig = raw
old = u'left = sorted(n for n in os.listdir(TEXI) if u"plate" in n)'
new = (u'# ⚠ 这里原来是子串匹配 `u"plate" in n` —— 会把 `star_steel_chestplate.png`\n'
       u'    #   （"chestplate" 含 "plate"）当成第四张板子（ZF116 一上线就红）。\n'
       u'    #   收窄成"以 _plate.png 结尾 或 正好叫 plate.png"：通用板复活照样抓，胸甲不误伤。\n'
       u'    left = sorted(n for n in os.listdir(TEXI)\n'
       u'                  if n.endswith(u"_plate.png") or n == u"plate.png")')

if new in raw:
    print(u"  [幂等] 已收窄过")
elif raw.count(old) == 1:
    raw = raw.replace(old, new)
    io.open(P, "w", encoding="utf-8", newline="\n").write(raw)
    print(u"  [OK] 已把「板正好三张」的过滤器收窄到 *_plate.png")
else:
    print(u"  !! 锚点出现 %d 次，停手" % raw.count(old))
    sys.exit(1)

back = io.open(P, encoding="utf-8").read()
print(u"\n回读断言：")
print(u"  [%s] 新过滤器在" % (u"OK" if u'n.endswith(u"_plate.png")' in back else u"!!"))
print(u"  [%s] 旧的子串过滤器已不在" % (u"OK" if old not in back else u"!!"))
print(u"  [%s] 原有的三张断言与 plate.png 删除断言都还在"
      % (u"OK" if (u'[u"copper_plate.png", u"iron_plate.png", u"steel_plate.png"]' in back
                   and u'check(u"textures/item/plate.png 已不存在"' in back) else u"!!"))
