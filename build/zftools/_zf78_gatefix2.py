# -*- coding: utf-8 -*-
u"""_zf78_gatefix2.py —— 公告与 ZF71 那条活体核对（流体数 / 语言键数）跟着本轮内容更新

ZF75 有过一次同样的修法（`_zf75_gatefix.py`：公告 218 → 219 键 + 校验期望值一起改）——
公告是**活体**的：里面每个数都必须等于当前代码/资源算出来的值，否则它就是骗人的。

本轮：
  ① 公告 §5「Fluids」一行：加上 4 种分馏产物；
  ② 公告那行 `c:` 标签清单：加上 4 张新标签；
  ③ 公告 §8 的 `219 keys each` → `241 keys each`；
  ④ `_zf71_verify.py`：`fl == 4` → `fl == 8`、`{219}` → `{241}`、"219 keys each" → "241 keys each"；
  ⑤ 「尚未完成」那节的**可证伪断言**扩到本轮两个新方块（公告把它们列进 creative-only 了）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
VER = os.path.join(ROOT, "build", "zftools", "_zf71_verify.py")
fails = []


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    print(u"== ① 公告：流体清单 ==")
    patch(ANN,
          u"- **Fluids:** oxygen, hydrogen, chlorine, plus **crude oil** (new in 0.11, see below).",
          u"- **Fluids:** oxygen, hydrogen, chlorine, **crude oil** (new in 0.11) and the four\n"
          u"  distillation products — **diesel, naphtha, gasoline and LPG** (new in 0.11).",
          u"公告 §5 流体清单")

    print(u"== ② 公告：c: 标签清单 ==")
    patch(ANN,
          u"Crude oil and the three process gases carry the common `c:` fluid tags\n"
          u"(`c:crude_oil`, `c:gaseous`, plus `c:oxygen` / `c:hydrogen` / `c:chlorine`), so other mods'",
          u"Crude oil, the three process gases and the four distillation products carry the common `c:` fluid\n"
          u"tags (`c:crude_oil`, `c:gaseous`, `c:oxygen` / `c:hydrogen` / `c:chlorine` and\n"
          u"`c:diesel` / `c:naphtha` / `c:gasoline` / `c:lpg`), so other mods'",
          u"公告 c: 标签清单")

    print(u"== ③ 公告：语言键数 ==")
    patch(ANN, u"(219 keys each)", u"(241 keys each)", u"公告 219 → 241 键")

    print(u"== ④ 校验脚本：活体计数 ==")
    patch(VER,
          u'    check(fl == 4 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)',
          u'    check(fl == 8 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)',
          u"_zf71 流体数 4 → 8")
    patch(VER,
          u'    check(len(keys) == 4 and set(keys.values()) == {219} and u"219 keys each" in doc,',
          u'    check(len(keys) == 4 and set(keys.values()) == {241} and u"241 keys each" in doc,',
          u"_zf71 语言键 219 → 241")

    print(u"== ⑤ 可证伪断言扩到本轮两个新方块 ==")
    patch(VER,
          u'''    for bid in ("potato_s_t:alloy_smelter", "potato_s_t:lithium_battery",
                "potato_s_t:advanced_metal_block", "potato_s_t:stable_metal_block"):''',
          u'''    for bid in ("potato_s_t:alloy_smelter", "potato_s_t:lithium_battery",
                "potato_s_t:advanced_metal_block", "potato_s_t:stable_metal_block",
                "potato_s_t:distillation_controller", "potato_s_t:distillation_operator"):''',
          u"_zf71 known-gaps 6 个方块")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
