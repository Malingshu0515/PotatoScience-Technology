# -*- coding: utf-8 -*-
u"""_zf156_plates.py —— ZF156 ③：把配方里的金属板原料从「自家物品」改成公共标签。

用户原话：「本mod配方里的金属板可以兼容别的mod金属板（板子确实通用 但是咱们的合成配方只认本mod板）」。

证据（`_zf156_recon.txt`）：板子的跨 mod 约定就是 `c:plates/<金属>`，而且
**别人自己就挂好了** —— 沉浸工程 `immersiveengineering:plate_iron` 挂在 `c:plates/iron`，
机械动力 `create:iron_sheet` 也挂在 `c:plates/iron`（1.21.1 里 `{"tag": ...}` 是原版
`Ingredient.Value.MAP_CODEC` 支持的写法，原版配方自己就在用，例如 `minecraft:planks`）。
所以**不需要**往标签里硬写别人的物品 id —— 把原料换成标签，谁挂谁就能用。

只碰原料那一处：`"item": "potato_s_t:xxx_plate"` → `"tag": "c:plates/xxx"`。
⚠ 产物（`"id": "potato_s_t:xxx_plate"`，液压机/F形压板机那 7 份）**一个字节都不动** ——
本 mod 的板还是本 mod 的板，只是"拿别人的板当原料"也认了。

跑法：python build\\zftools\\_zf156_plates.py [--write]
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
RECIPE_DIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")

METALS = ["aluminum", "cobalt", "copper", "iron", "nickel", "silver", "steel"]
PAT = re.compile(u'"item"\\s*:\\s*"potato_s_t:(' + u"|".join(METALS) + u')_plate"')


def main(argv):
    write = u"--write" in argv
    changed = []
    total = 0
    for dirpath, _d, filenames in os.walk(RECIPE_DIR):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            text = io.open(p, encoding="utf-8").read()
            hits = PAT.findall(text)
            if not hits:
                continue
            new = PAT.sub(lambda m: u'"tag": "c:plates/%s"' % m.group(1), text)
            json.loads(new)          # 改完必须是合法 JSON（不然当场炸，别写坏盘）
            rel = os.path.relpath(p, RECIPE_DIR)
            changed.append((rel, len(hits), sorted(set(hits))))
            total += len(hits)
            if write:
                io.open(p, "w", encoding="utf-8", newline="").write(new)
                assert io.open(p, encoding="utf-8").read() == new
    print(u"要改的配方 %d 份 / %d 处：" % (len(changed), total))
    for rel, n, metals in changed:
        print(u"   %-42s ×%d  %s" % (rel, n, u",".join(metals)))
    # 反过来核：改完还剩多少"自家板当原料"
    left = 0
    for dirpath, _d, filenames in os.walk(RECIPE_DIR):
        for fn in filenames:
            if fn.endswith(".json"):
                left += len(PAT.findall(io.open(os.path.join(dirpath, fn), encoding="utf-8").read()))
    print(u"还剩「自家板当原料」%d 处（--write 之后应为 0）" % left)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
