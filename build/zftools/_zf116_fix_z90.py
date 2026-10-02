# -*- coding: utf-8 -*-
u"""_zf116_fix_z90.py —— 补上 `_zf90_verify.py` 剩下的两处（并发环境：正则按实质替换）

上一版用整段字面量去匹配，**只差一个缩进空格**就打不上（脚本正确地报了"锚点 0 次"并停手）。
这里改成按「代码实质」替换 —— 只认 `for n in (...)` 那个元组和那句中文标签，
不依赖换行与缩进。改完立刻回读断言。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf90_verify.py"

raw = io.open(P, encoding="utf-8").read()
orig = raw
notes = []

# ① 旧数字黑名单：(5, 6, 7, 13) -> (5, 6, 7, 13, 12)
m = re.search(r"for n in \(5, 6, 7, 13\)", raw)
if m:
    raw = raw[:m.start()] + "for n in (5, 6, 7, 13, 12)" + raw[m.end():]
    notes.append(u"黑名单 (5,6,7,13) -> (5,6,7,13,12)")
else:
    if "for n in (5, 6, 7, 13, 12)" in raw:
        notes.append(u"黑名单已是 (5,6,7,13,12)（幂等）")
    else:
        notes.append(u"!! 找不到黑名单元组，未改")

# ② 那句中文标签 5/6/7/13 -> 5/6/7/13/12
m = re.search(u"u\"英文公告里不再写 5/6/7/13 models\"", raw)
if m:
    raw = raw[:m.start()] + u"u\"英文公告里不再写 5/6/7/13/12 models\"" + raw[m.end():]
    notes.append(u"标签 -> 5/6/7/13/12")
elif u"u\"英文公告里不再写 5/6/7/13/12 models\"" in raw:
    notes.append(u"标签已是 5/6/7/13/12（幂等）")
else:
    notes.append(u"!! 找不到中文标签，未改")

# ③ 贴图清单表头那条注释与断言：12 -> 9
m = re.search(r"# ZF110 重跑过 `TextureCheck\.py --plan` ⇒ 表头跟着活体数字走（现在 12 个）", raw)
if m:
    raw = raw[:m.start()] + u"# ZF110/ZF116 重跑过 `TextureCheck.py --plan` ⇒ 表头跟着活体数字走（现在 9 个）" + raw[m.end():]
    notes.append(u"注释 12 -> 9")
m = re.search(u"check\\(u\"贴图清单的待画表头已变 12 个\", u\"## 待画（12 个\" in listing\\)", raw)
if m:
    raw = raw[:m.start()] + u"check(u\"贴图清单的待画表头已变 9 个\", u\"## 待画（9 个\" in listing)" + raw[m.end():]
    notes.append(u"表头断言 12 -> 9")
else:
    notes.append(u"!! 表头断言未改（可能已是 9 或文本变了）")

# ④ 把 ZF116 这轮记进注释
m = re.search(u"#   \\*\\*ZF110\\*\\* 星璨钢头盔拿到自己的背包图标 ⇒ \\*\\*13 → 12\\*\\*（这三处一起改）\n", raw)
if m:
    raw = raw[:m.end()] + u"    #   **ZF116** 胸甲/护腿/靴子三件也拿到自己的图 ⇒ **12 → 9**（同样三处一起改）\n" + raw[m.end():]
    notes.append(u"补 ZF116 注释")

if raw != orig:
    io.open(P, "w", encoding="utf-8", newline="\n").write(raw)

back = io.open(P, encoding="utf-8").read()
print(u"改动：")
for n in notes:
    print(u"  - " + n)
print(u"\n回读断言：")
print(u"  [%s] 黑名单含 12" % (u"OK" if "for n in (5, 6, 7, 13, 12)" in back else u"!!"))
print(u"  [%s] 表头断言 = 9" % (u"OK" if u"## 待画（9 个" in back else u"!!"))
print(u"  [%s] 不再出现「已变 12 个」" % (u"OK" if u"已变 12 个" not in back else u"!!"))
print(u"  [%s] 文件有变化" % (u"OK" if raw != orig else u"（无变化）"))
