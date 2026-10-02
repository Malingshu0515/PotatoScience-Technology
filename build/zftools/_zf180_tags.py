# -*- coding: utf-8 -*-
u"""_zf180_tags.py —— ZF180（0.14）：把振金/星璨钢/钛合金装备挂进**原版装备类型标签**。

**病根**（用户 0.14 实测：「附魔灌注台以及原版附魔台都无法给振金/星璨钢装备附魔 铁砧也不可以！」）：

1.21 的附魔能不能上到某件装备上，看的是**附魔自己的 `supported_items`**（数据包里的字段），而原版的
`data/minecraft/tags/item/enchantable/*` **全是按原版"装备类型"标签定义的**，例如：

| 原版 enchantable/* | 内容 |
|---|---|
| `enchantable/head_armor` | `#minecraft:head_armor` |
| `enchantable/chest_armor` / `leg_armor` / `foot_armor` | 同名类型标签 |
| `enchantable/armor` | 上面四个 |
| `enchantable/sword` | `#minecraft:swords` |
| `enchantable/mining` / `mining_loot` | `#minecraft:axes` + `#minecraft:pickaxes` + `#minecraft:shovels` + `#minecraft:hoes` |
| `enchantable/durability` | 上面全部 + 弓/弩/三叉戟/打火石/剪刀… |

⇒ **模组装备只要没挂进这些"类型"标签，就没有任何一条附魔支持它**：附魔台算不出可附魔项（什么都不给）、
铁砧插不上附魔书、别的 mod 的附魔灌注台同理。本工程此前**只**挂了
`minecraft:swords`（仅钛合金剑）与 `minecraft:pickaxes`（仅钛合金镐）—— 振金/星璨钢的**四件套护甲
与剑/镐/斧/锹/锄一件都没挂**，所以它们"铁砧也不行"。

跑法：python build\\zftools\\_zf180_tags.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
TAGS = os.path.join(ROOT, r"src\main\resources\data\minecraft\tags\item")

ARMOR = [u"titanium_alloy", u"star_steel", u"vibranium"]
PIECES = [(u"head_armor", u"helmet"), (u"chest_armor", u"chestplate"),
          (u"leg_armor", u"leggings"), (u"foot_armor", u"boots")]
TOOLS = [(u"swords", u"sword"), (u"pickaxes", u"pickaxe"), (u"axes", u"axe"),
         (u"shovels", u"shovel"), (u"hoes", u"hoe")]

# 0.14 已有的：swords 里只有钛合金剑、pickaxes 里只有钛合金镐（振金/星璨钢漏了）；护甲四类一个都没建
PLAN = {}
for tag, piece in PIECES:
    PLAN[tag] = [u"potato_s_t:%s_%s" % (m, piece) for m in ARMOR]
for tag, tool in TOOLS:
    ids = [u"potato_s_t:star_steel_%s" % tool]
    if tag in (u"swords", u"pickaxes"):
        ids += [u"potato_s_t:titanium_alloy_%s" % tool]
    if tag == u"swords":
        ids += [u"potato_s_t:vibranium_sword"]
    PLAN[tag] = ids


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    for tag, ids in sorted(PLAN.items()):
        p = os.path.join(TAGS, tag + u".json")
        if os.path.isfile(p):
            obj = json.loads(read(p))
            cur = list(obj.get(u"values", []))
            add = [i for i in ids if i not in cur]
            if not add:
                notes.append(u"%s.json：（已齐，%d 项）" % (tag, len(cur)))
                continue
            obj[u"values"] = cur + add
        else:
            obj = {u"replace": False, u"values": ids}
            add = list(ids)
        text = json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"
        back = json.loads(text)
        if back[u"values"][:len(ids)] != ids and not os.path.isfile(p):
            fails.append(u"%s：内容不对" % tag)
            continue
        notes.append(u"%s.json：+%d 项（共 %d 项）" % (tag, len(add), len(back[u"values"])))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
