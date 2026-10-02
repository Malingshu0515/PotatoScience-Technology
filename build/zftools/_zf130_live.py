# -*- coding: utf-8 -*-
u"""_zf117_live.py —— 把活体数字从 15 收口到 13

## 为什么是 13（三方对账，不是拍脑袋）

| 来源 | 值 |
|---|---|
| ZF116 我留给盘上的 | **9** |
| 另一条线这轮新增 `vibranium_*` 四件盔甲（借原版铁套） | 9 + 4 = **13** |
| 我 ZF117 把 `silver_wire` / `silver_wire_spool` 改成自己的图 | 13 − 2 = **11**？|

⚠ 等等 —— 上面第三行要小心：**「借原版」这一档数的是"模型引用了原版贴图"**。
银线两件原来借 `iron_nugget` / `iron_ingot`，改掉之后确实各减 1。
但**权威是第 8 道门 `TextureCheck.py` 现数的结果**，不是我这套推算：

    $ python build/zftools/TextureCheck.py
    ... 待画 = 13

它数的就是"还在借原版贴图的模型"，清单里**没有** `silver_wire` / `silver_wire_spool`
（改成功了），也没有 `star_steel_*`（ZF110/116 改掉了），
有的是 `titanium_alloy_*` 4 件 + `vibranium_*` 4 件 + `creative_cable` / `lithium_concentrate` /
`test_fluid_tank` ×2 + `block/test_fluid_tank`。

⇒ **13 才是盘上事实**；门里与公告里那个 15 是**改早了**（另一条线把自己那 4 件加上去时，
我这两件还没改完）。本脚本把三处一起收到 13，并用 `TextureCheck` 的输出**当场互核**。
"""
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
NEW = 13
OLD = 15
fails = []


def patch(path, old, new, label, expect=1):
    t = io.open(path, encoding="utf-8").read()
    n = t.count(old)
    if n != expect:
        fails.append(u"%s：锚点 %d 次（期望 %d）" % (label, n, expect))
        print(u"    !! %s 锚点 %d 次，停手" % (label, n))
        return False
    io.open(path, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
    b = io.open(path, encoding="utf-8").read()
    if new not in b:
        fails.append(u"%s 回读失败" % label)
        return False
    print(u"    [OK] %s" % label)
    return True


print(u"== ① 先问第 8 道门：盘上到底几个 ==")
r = subprocess.run([sys.executable, os.path.join(TOOLS, "TextureCheck.py")],
                   capture_output=True, cwd=TOOLS)
out = r.stdout.decode("utf-8", "replace")
m = re.search(r"待画\s*=\s*(\d+)", out)
truth = int(m.group(1)) if m else -1
print(u"    TextureCheck 报：待画 = %d" % truth)
if truth != NEW:
    print(u"    !! 与预期 %d 不符 —— 盘上又变了，停手（不硬改成 %d）" % (NEW, NEW))
    sys.exit(1)
print(u"    [OK] 与预期 %d 一致" % NEW)

print(u"\n== ② 三处一起改 ==")
ann = os.path.join(DOCS, "UpdateAnnouncement_EN.md")
t = io.open(ann, encoding="utf-8").read()
if u"%d models still do this" % NEW in t:
    print(u"    [幂等] 公告已是 %d" % NEW)
else:
    patch(ann, u"%d models still do this" % OLD, u"%d models still do this" % NEW,
          u"公告 %d -> %d" % (OLD, NEW))

z71 = os.path.join(TOOLS, "_zf71_verify.py")
t = io.open(z71, encoding="utf-8").read()
if u"n_draw == %d" % NEW in t and u'u"%d models still do this"' % NEW in t:
    print(u"    [幂等] _zf71 已是 %d" % NEW)
else:
    patch(z71, u"n_draw == %d" % OLD, u"n_draw == %d" % NEW, u"_zf71 n_draw")
    patch(z71, u'u"%d models still do this"' % OLD, u'u"%d models still do this"' % NEW,
          u"_zf71 文案")
    patch(z71, u"（公告写 %d）" % OLD, u"（公告写 %d）" % NEW, u"_zf71 中文标签")

z90 = os.path.join(TOOLS, "_zf90_verify.py")
t = io.open(z90, encoding="utf-8").read()
if u'u"英文公告已改成 %d models still do this"' % NEW in t:
    print(u"    [幂等] _zf90 已是 %d" % NEW)
else:
    patch(z90, u'u"英文公告已改成 %d models still do this"' % OLD,
          u'u"英文公告已改成 %d models still do this"' % NEW, u"_zf90 公告标签")
    patch(z90, u'u"%d models still do this" in ann' % OLD,
          u'u"%d models still do this" in ann' % NEW, u"_zf90 公告断言")
    patch(z90, u'u"`_zf71_verify.py` 的期望值同步成 %d"' % OLD,
          u'u"`_zf71_verify.py` 的期望值同步成 %d"' % NEW, u"_zf90 z71 标签")
    patch(z90, u'u"n_draw == %d" in z71' % OLD,
          u'u"n_draw == %d" in z71' % NEW, u"_zf90 z71 断言")
    # 旧数字黑名单 / 标签里补上 15
    t = io.open(z90, encoding="utf-8").read()
    mm = re.search(r"for n in \((5, 6, 7[^)]*)\)", t)
    if mm and u"15" not in mm.group(1):
        patch(z90, u"for n in (%s)" % mm.group(1),
              u"for n in (%s, %d)" % (mm.group(1), OLD), u"_zf90 黑名单补 %d" % OLD)
    mm = re.search(u"u\"英文公告里不再写 ([0-9/]+) models\"", t)
    if mm and u"15" not in mm.group(1):
        patch(z90, u"u\"英文公告里不再写 %s models\"" % mm.group(1),
              u"u\"英文公告里不再写 %s/%d models\"" % (mm.group(1), OLD),
              u"_zf90 标签补 %d" % OLD)

print(u"\n== ③ 复跑两张门，看活体数字那条 ==")
for g, pat in (("_zf71_verify.py", u"借原版"), ("_zf90_verify.py", u"models still do this")):
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)],
                        capture_output=True, cwd=TOOLS)
    o = rr.stdout.decode("utf-8", "replace")
    hit = [ln.strip() for ln in o.splitlines() if pat in ln]
    print(u"    %s：%s" % (g, u" | ".join(hit) if hit else u"（没找到那行）"))

print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
