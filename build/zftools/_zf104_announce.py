# -*- coding: utf-8 -*-
r"""_zf104_announce.py —— ZF104 更新 docs/UpdateAnnouncement_EN.md（英文公告）

两处：
  ① §6 Tools and gear 加"两套盔甲 + 星璨钢锭"一节
  ② §8 的键数 335 → 349；§9 的"借原版贴图 5 个" → 13 个
锚点唯一性先查后改（§4.6）。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
fails = []

ARMOR_ANCHOR = u"| **Wrench** | Shift + right-click to disassemble multiblocks |\n"
ARMOR_NEW = u"""| **Wrench** | Shift + right-click to disassemble multiblocks |

### Two new armour sets (new in 0.11 ZF104)

Both sets are crafted nowhere yet — **they are creative-only for now** (ask and recipes can be added).
Inventory icons currently borrow the vanilla **iron** armour sprites, as requested; the worn models
do too, so they look like iron until real art arrives.

| Piece | Titanium Alloy — durability / armour | Star Steel — durability / armour / toughness |
|---|---|---|
| Helmet | 2,801 / **+2.5** | 2,012 / **+5.5** / +0.5 |
| Chestplate | 4,096 / +8 | 3,876 / **+9.5** / **+1** |
| Leggings | 3,412 / +6 | 2,790 / **+7.5** / +0.5 |
| Boots | 2,048 / **+4.5** | 1,754 / **+5.5** / +0.5 |

- **Titanium Alloy set**: enchantability **25** (higher than gold's 22), repaired with
  **Lightweight Titanium Alloy**. The half-point armour values are real — they are written as
  `double` attribute modifiers, not the vanilla integer armour table.
- **Star Steel set**: enchantability **20**, repaired with the new **Star Steel Ingot**
  (no recipe yet — it exists only as a repair material for now).
- **Per piece (no full set needed):** at night you get **Resistance I** — wearing all four is still
  only Resistance I, it does **not** stack — and your armour **does not lose durability at night**.
  During the day (and in the End/Nether) durability is consumed normally.
- **Full set, Overworld, night:** Strength I, Resistance II, plus **10 s of Absorption III every 45 s**.
- **Full set, The End:** Regeneration I, Resistance III, Strength II, plus
  **12 s of Absorption VI every 15 s**.
- **Full set, void damage:** you are teleported to the nearest solid block within **20 × 20 blocks,
  any height** (the search runs from world bottom to world top). If there is truly no block,
  you **swap places with the nearest mob** instead. Both outcomes are reported on the action bar.
"""
LANG_ANCHOR = u"- **4 languages:** English, 中文, 日本語, Русский (335 keys each)\n"
LANG_NEW = u"- **4 languages:** English, 中文, 日本語, Русский (349 keys each)\n"
TEX_ANCHOR = u"- **Some textures are placeholders** borrowed from vanilla (5 models still do this); on top of"
TEX_NEW = (u"- **Some textures are placeholders** borrowed from vanilla (13 models still do this — the count\n"
           u"  went up because the eight new armour pieces borrow the vanilla iron armour sprites); on top of")


def patch(path, old, new, label, expect=1):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        fails.append(u"%s：锚点命中 %d 次（应为 %d）" % (label, hits, expect))
        print(u"  [FAIL] %s" % label)
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    patch(DOC, ARMOR_ANCHOR, ARMOR_NEW, u"§6 加两套盔甲一节")
    patch(DOC, LANG_ANCHOR, LANG_NEW, u"§8 键数 335 → 349")
    patch(DOC, TEX_ANCHOR, TEX_NEW, u"§9 借原版贴图 5 → 13")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
