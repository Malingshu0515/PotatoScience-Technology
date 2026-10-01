# -*- coding: utf-8 -*-
u"""_zf160_apply.py —— ZF160 落地（幂等，默认 dry-run）：银矿调大、铝的权重调小。

用户原话：「银矿矿脉可以稍微调大一点 大概和铜差不多（或者生成权重大一点也可以）
然后铝的权重调小1~2」。

取证（`_zf160_recon.txt`）：本模组 9 种矿里**银是最小的**（size 3，铝 11、锰 12、铀 10…），
原版铜是 **小脉 size 10 / 每区块 16 次**（外加一条 size 20 的大脉）。所以：

  ① 银 `ore_silver.json` 的 `size`：**3 → 10** —— 直接对齐原版**铜小脉**的 size（用户给的锚点）。
  ② 银 `ore_silver_placed.json` 的 `count`：**9 → 12** —— 用户说"或者生成权重大一点也可以"，
     顺手把权重也提一档；仍**低于**铜的 16，留给"银比铜稀"这条常识。
  ③ 铝 `ore_aluminum_placed.json` 的 `count`：**12 → 10**（用户说"调小1~2"，取 2）。

跑法：python build\\zftools\\_zf160_apply.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
WG = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\worldgen")
SILVER_CFG = os.path.join(WG, "configured_feature", u"ore_silver.json")
SILVER_PLC = os.path.join(WG, "placed_feature", u"ore_silver_placed.json")
ALUM_PLC = os.path.join(WG, "placed_feature", u"ore_aluminum_placed.json")

EDITS = [
    (SILVER_CFG, u'"size": 3', u'"size": 10', u"银：矿脉 size 3 → 10（对齐原版铜小脉）"),
    (SILVER_PLC, u'{ "type": "minecraft:count", "count": 9 }',
     u'{ "type": "minecraft:count", "count": 12 }', u"银：每区块次数 9 → 12"),
    (ALUM_PLC, u'{ "type": "minecraft:count", "count": 12 }',
     u'{ "type": "minecraft:count", "count": 10 }', u"铝：每区块次数 12 → 10"),
]


def main(argv):
    write = u"--write" in argv
    fails = []
    plan = []
    for path, old, new, label in EDITS:
        text = io.open(path, encoding="utf-8", newline=u"").read()
        if new in text and old not in text:
            print(u"  [跳过] %s（已经是新的，幂等）" % label)
            continue
        n = text.count(old)
        if n != 1:
            fails.append(u"%s：锚点命中 %d 次（应为 1）→ %s" % (label, n, old))
            continue
        text2 = text.replace(old, new, 1)
        json.loads(text2)                     # 改完必须还是合法 JSON
        plan.append((path, text2, label))
        print(u"  [改] %s" % label)
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not plan:
        print(u"（三处都已经是新的，无事可做）")
        return 0
    if not write:
        print(u"（没加 --write：只算不写）")
        return 0
    for path, text2, label in plan:
        io.open(path, u"w", encoding="utf-8", newline=u"").write(text2)
        assert io.open(path, encoding="utf-8", newline=u"").read() == text2
        print(u"  已写 %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
