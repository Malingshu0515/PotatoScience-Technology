# -*- coding: utf-8 -*-
u"""_zf180_docs.py —— ZF180 文档落笔（§4.180 + §5 行 + §9 段 + 交接第 42 条 + 英文公告）+ 哈希跟平。

主题：修「振金/星璨钢装备无法附魔」（原版附魔台 / 铁砧 / 附魔灌注台都不行）。

跑法：python build\\zftools\\_zf180_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

S4 = u"""### 4.180 【数据包雷】1.21 的附魔看 `supported_items`，而原版 `enchantable/*` 全是按**类型标签**定义的（0.13 ZF180 → 用户按 0.14 报的）

用户实测原话：「**附魔灌注台以及原版附魔台都无法给振金/星璨钢装备附魔 铁砧也不可以！**」

三个地方一起失效，说明问题不在那三台机器里，而在**装备自己**。1.21 的判据是：
一条附魔能不能上到某件装备，看这条附魔的 **`supported_items`**（数据包字段）；
而原版 `data/minecraft/tags/item/enchantable/*` **19 个标签全是按"装备类型"标签定义的**：

| 原版 `enchantable/*` | 它的内容 |
|---|---|
| `head_armor` / `chest_armor` / `leg_armor` / `foot_armor` | `#minecraft:head_armor` 等**同名类型标签** |
| `armor` | 上面四个 |
| `sword` | `#minecraft:swords` |
| `mining` / `mining_loot` | `#minecraft:axes` + `#minecraft:pickaxes` + `#minecraft:shovels` + `#minecraft:hoes` |
| `durability` | 上面全部 + 弓/弩/三叉戟/打火石/剪刀… |

⇒ **模组装备只要没挂进那些"类型"标签，就没有任何一条附魔支持它**：附魔台算不出可附魔项（什么都不给）、
铁砧插不上附魔书、别的 mod 的附魔灌注台同理。本工程此前**只**挂了两个标签、而且只写了钛合金那一件
（`swords` → 只有 `titanium_alloy_sword`；`pickaxes` → 只有 `titanium_alloy_pickaxe`），
**振金/星璨钢的四件套护甲一件都没挂**、剑/镐/斧/锹/锄也几乎全漏 —— 这就是"铁砧也不行"的直接原因。

**修法**（纯数据，`build\\zftools\\_zf180_tags.py`）：把 20 件装备挂进 9 个类型标签 ——
四个护甲位 × 三套材质，`swords` 补星璨钢剑与振金剑，`pickaxes` 补星璨钢镐，并新建
`axes`/`shovels`/`hoes`。**只加我们自己的 id，一个原版条目都不动**（门里有这条判据）。

**取证**（真服务端 `Zf180Check`，5/0）：逐件断言 `stack.isEnchantable()`、附魔权重 > 0、
以及**具体附魔的 `supported_items` 是否命中**（护甲→保护、剑/斧→锋利、工具→效率、全体→耐久/经验修补），
外加 3 条负对照（星璨钢锭不被"保护"支持、振金头盔不被"效率"支持、泥土不被"锋利"支持）。
这三样正是附魔台/铁砧/灌注台真正查的东西 —— 比"挂了标签应该就好了"硬。

"""

ROW = u"""| ZF180 | **无新备份根**（纯数据：9 个 `minecraft:tags/item/*` 标签 + 门/探针脚本 + 文档；⚠ 轮号 `_zf180_*` 开工前查过没人占（§4.147）） | **0.13（按用户口径的 0.14 内容）：修「振金/星璨钢装备无法附魔」**（用户原话见 §9）。① **病根**（§4.180）：1.21 看附魔自己的 `supported_items`，而原版 `enchantable/*` 全按**装备类型标签**定义；我们只挂了 `swords`（仅钛合金剑）与 `pickaxes`（仅钛合金镐）⇒ 振金/星璨钢护甲与多数工具**没有任何附魔支持**。② **修法**：`_zf180_tags.py` 把 **20 件装备**挂进 **9 个**类型标签（四个护甲位 × 三套材质 + `swords`/`pickaxes` 补齐 + 新建 `axes`/`shovels`/`hoes`），**只加自己的 id**。③ **真服务端探针 `Zf180Check` 5/0**：逐件 `isEnchantable` + 权重 > 0 + **目标附魔 `supported_items` 命中** + 3 条负对照。④ 门 `_zf180_verify.py` **6/0**。⑤ **重打成品**：`release\\PotatoST-0.13.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.180 |
"""

S9 = u"""### ZF180（0.14 内容）修「振金/星璨钢装备无法附魔」—— **附魔台 / 铁砧 / 灌注台应当都能用了**

你报的原话：「**附魔灌注台以及原版附魔台都无法给振金/星璨钢装备附魔 铁砧也不可以！**」

**病根不在那三台机器上，在装备自己**：1.21 里"这条附魔能不能上到这件装备"看的是**附魔自己的
`supported_items`**；而原版的 `enchantable/*` 标签（19 个）**全是按原版"装备类型"标签定义的** ——
`enchantable/head_armor` ＝ `#minecraft:head_armor`、`enchantable/sword` ＝ `#minecraft:swords`、
`enchantable/mining` ＝ `#minecraft:axes` + `#minecraft:pickaxes` + `#minecraft:shovels` + `#minecraft:hoes`…

我们此前**只**挂了两个标签并且只写了钛合金那一件（`swords` 里只有 `titanium_alloy_sword`、
`pickaxes` 里只有 `titanium_alloy_pickaxe`）—— **振金/星璨钢的四件套护甲一件都没挂**，
剑/镐/斧/锹/锄也几乎全漏。所以三处一起失效：附魔台算不出可附魔项、铁砧插不上书、别的 mod 的灌注台同理。

**现在**：20 件装备全部挂进正确的类型标签 —— 四个护甲位 × 钛合金/星璨钢/振金，
`swords` 补上星璨钢剑与振金剑，`pickaxes` 补上星璨钢镐，并新建 `axes`/`shovels`/`hoes`。
**只加我们自己的 id，原版条目一个没动**（门里有这条判据）。

**取证（真服务端，5/0）**：逐件断言 `isEnchantable()`、附魔权重 > 0、以及**具体附魔的 `supported_items`
是否命中**（护甲→保护、剑/斧→锋利、工具→效率、全体→耐久/经验修补）；负对照：星璨钢锭不被"保护"支持、
振金头盔不被"效率"支持、泥土不被"锋利"支持。这三样正是附魔台/铁砧真正查的东西。

**要你实测**：拿振金/星璨钢的护甲与剑/镐/斧去附魔台（应当能出附魔）、拿附魔书去铁砧（应当能插上）、
再用你那台附魔灌注台试一次。
"""

HAND42 = u"""42. **ZF180 的账（修「振金/星璨钢装备无法附魔」）**：① 用户原话与三个现象见档案 §9；**病根是数据包**（§4.180）：
    1.21 看附魔自己的 `supported_items`，原版 `enchantable/*` 按**装备类型标签**定义 ⇒ 我们只挂了
    `swords`（仅钛合金剑）/`pickaxes`（仅钛合金镐）⇒ 振金·星璨钢护甲与多数工具没有任何附魔支持。
    ② 修法：`build\\zftools\\_zf180_tags.py` 把 **20 件装备**挂进 **9 个** `minecraft:tags/item/*`
    （四护甲位 × 三材质 + `swords`/`pickaxes` 补齐 + 新建 `axes`/`shovels`/`hoes`），**只加自己的 id**。
    ③ 取证：真服务端 `Zf180Check` **5/0**（逐件 `isEnchantable` + 权重 > 0 + **目标附魔 `supported_items`
    命中** + 3 条负对照）；门 `_zf180_verify.py` **6/0**。④ ⚠ 版本：用户按 **0.14** 报的，但仓库
    `gradle.properties` 此刻仍是 `0.13` —— 抬版本要连带跟平三份钉 `mod_version` 的老门（ZF147 先例），
    等用户/另一条线明确后再动。⑤ 教训：模组加**任何**能被附魔的装备（护甲/工具/武器），
    都必须同时挂对应**类型标签**，否则"看起来数据都对、附魔台就是不给"。
"""


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(JAR):
        print(u"!! 成品不在")
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    tag_in_jar = [n for n in names if n.startswith(u"data/minecraft/tags/item/")]
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d / jar 里 minecraft:tags/item %d 份"
          % (size, h, cls, recipes, keys_zh, keys_lzh, len(tag_in_jar)))
    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    m = re.search(u"\\*\\*(\\d+) classes, 43 advancements", read(ANN))
    old_cls = m.group(1) if m else u""
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        if old_cls:
            text = re.sub(u"class " + old_cls + u"；§4\\.159", u"class %d；§4.159" % cls, text)
        text = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), text)
        text = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        text = re.sub(u"\\((\\d+) keys each\\)", u"(%d keys each)" % keys_zh, text)
        text = re.sub(u"plus Literary Chinese with (\\d+)\\.",
                      u"plus Literary Chinese with %d." % keys_lzh, text)
        return text

    def subst(text):
        return (text.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h)
                .replace(u"{cls}", str(cls)))

    doc = read(DOC)
    if u"### 4.180 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF180 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.178 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF178 行尾锚点 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + subst(ROW) + u"\n", 1)
    if u"### ZF180（0.14 内容）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"42. **ZF180 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND42 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = read(V149)
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, vn, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == read(V149):
        fails.append(u"_zf149_verify.py：一个靶子都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF180" not in ann:
        a5 = u"## New in 0.13 ZF178 - Magnet block and raw ore blocks"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF178 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF180 - Vibranium and Star Steel gear can be enchanted again\n\n"
                     u"- **Fixed: vibranium / star steel (and titanium) armour, swords and tools could not\n"
                     u"  be enchanted** - not by the vanilla enchanting table, not with an anvil and not by\n"
                     u"  third-party enchanting blocks.\n"
                     u"- The cause was on the gear side, not in those blocks: in 1.21 an enchantment only\n"
                     u"  applies to items listed in its `supported_items`, and vanilla's `enchantable/*`\n"
                     u"  tags are all defined from the **vanilla equipment-type tags**\n"
                     u"  (`#minecraft:head_armor`, `#minecraft:swords`, `#minecraft:axes`, ...). Our gear\n"
                     u"  was in almost none of them.\n"
                     u"- **All 20 pieces are now tagged** (four armour slots x three materials, plus\n"
                     u"  sword/pickaxe/axe/shovel/hoe), adding only our own ids - no vanilla entry was\n"
                     u"  touched.\n"
                     u"- Verified on a real server, per item: `isEnchantable()`, a non-zero enchantment\n"
                     u"  value, and an actual `supported_items` hit for the enchantments that belong on it\n"
                     u"  (protection / sharpness / efficiency / unbreaking / mending), plus three negative\n"
                     u"  controls. 5/0.\n"
                     u"- **Download:** `release/PotatoST-0.13.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
