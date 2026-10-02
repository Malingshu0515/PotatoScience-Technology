# -*- coding: utf-8 -*-
u"""_zf178_docs.py —— ZF178 文档落笔（§4.178 + §5 行 + §9 段 + 交接第 41 条 + 英文公告）+ 哈希跟平。

主题：磁铁块 + 6 个粗矿块（9 ↔ 1 双向配方，贴图自己画）。

跑法：python build\\zftools\\_zf178_docs.py [--write]
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

S4 = u"""### 4.178 【取证雷 + 语法雷】生成器的"id 存在性"检查只认方法名含 `register` 的调用；列表推导式不能混在列表字面量里（0.13 ZF178）

本轮加 7 个方块 + 14 条配方，撞了两个**和游戏逻辑无关**的坑，都是"工具/语法"层面的：

**① 取证范围太窄 ⇒ 14 条假 FAIL。** `_zf45_recipes.py` 的"配方产物/原料 id 存在性"检查靠扫
`ModItems/ModBlocks/ModArmorItems/PotatoSTOres` 里**方法名含 register** 的调用收集 id。
可 `PotatoSTOres` 的真正注册入口是三个**私有工厂** `ore(name, …)` / `raw(name)` / `rawBlock(name)`
（工厂内部 `ORES.register(name, …)` 传的是**变量**，那条正则一条也匹配不到）⇒ 新加的 6 个粗矿块
与既有的 `raw_*` 全被判成"没注册"。修法：把三个工厂名加进取证范围（与 §4.71/§4.76 那条
「**取证范围本身就是判据的一部分**」同一个道理）。

**② `SHAPELESS` 列表不能直接塞元素。** 那张表的第一个元素是**列表推导式**，而推导式必须做列表里
唯一的元素；在前面插 `dict(...)` 会得到 `SyntaxError: did you forget parentheses around the
comprehension target?`。修法：新增的 7 条 1→9 写成 `SHAPELESS += [...]`（紧跟在原列表之后）。

**③ 另外两条小雷**：给 JSON 模板套 `str.format()` 会因模板里的花括号直接 `KeyError`（用 `%s`）；
本机 PATH 上的 Python **没有 Pillow**（画贴图要用工程自带的那个 Python）。

"""
ROW = u"""| ZF178 | **无新备份根**（只改 3 份 java + 5 份 lang + 新增 7 贴图/21 模型/7 loot table/14 配方 + 生成器表 + 门脚本；改前件用 `git show HEAD:`，与 ZF164/ZF168/ZF174 同例。⚠ 轮号 `_zf178_*` 开工前查过没人占（§4.147）） | **0.13：磁铁块 + 6 个粗矿块（9 ↔ 1 双向）**（用户原话见 §9）。① **磁铁块**：`magnet_block`，属性照装饰金属块（5.0/6.0 + 金属音 + 必须用对工具），9 磁铁 ↔ 1 块双向。② **6 个粗矿块**：`raw_{aluminum,cobalt,nickel,silver,tungsten,uranium}_block`，走 `PotatoSTOres.rawBlock()` 工厂注册（块物品自动进 `ALL_ORE_ITEMS` ⇒ 自动上创造页），属性照**原版粗矿块**（5.0/6.0 + 石音 + 必须用对工具）；**按用户要求不做锂/锰/钛/振金的块**（门里逐条断言"没有"）。③ **贴图自己画**（用户原话「可以自己画吧」）：7 张 16×16 RGBA，`_zf178_draw.py` 确定性生成 —— **石头底 + 7~9 坨矿斑**，矿斑配色**从对应 `textures\\item\\raw_<metal>.png` 采样**（暗 20% / 中 50% / 亮 85% 三色），磁铁块 = 铁灰底 + 红色磁极斑（取自 `magnet.png`）。④ **14 条配方**（7 条 3×3 的 9→1 + 7 条 shapeless 的 1→9）走生成器表 ⇒ 盘上 **98 → 112 份**，`--write` 重出**只多这 14 份**。⑤ 7 份 loot table、2 个方块 tag（`mineable/pickaxe` + `needs_stone_tool` 各 +7）、7 个语言键 ×5（**621 → 628**，lzh 623 → 630）。⑥ **常驻门 `_zf178_verify.py` 18/0**、**反证刀 7/7**。⑦ **重打成品**：`release\\PotatoST-0.13.jar` = **%s 字节 / sha1 `%s`**（class %s；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.178 |
"""

S9 = u"""### ZF178（0.13）磁铁块 + 6 个粗矿块（9 ↔ 1 双向）—— **贴图是自己画的**

你交代的三件事都做了：

**① 磁铁块**：`magnet_block`。**9 个磁铁 → 1 块**（3×3 合成），**1 块 → 9 个磁铁**（无序配方）。
属性照装饰金属块那套（5.0/6.0 硬度 + 金属音 + 必须用对工具）。

**② 粗矿块（6 个）**：粗铝块 / 粗钴块 / 粗镍块 / 粗银块 / 粗钨块 / 粗铀块 —— 各 **9 粗矿 ↔ 1 块**。
属性照**原版粗矿块**：5.0/6.0 硬度、石音、"必须用对工具才掉东西"；`mineable/pickaxe` 与 `needs_stone_tool`
两个 tag 都加了（这两件事少写一个就会出现"木镐能挖但什么都不掉"或"石镐挖了不掉"）。
**锂 / 锰 / 钛 / 振金按你说的不做块** —— 门里专门有一条逐项断言"这几样没有块"。

**③ 贴图（7 张，我自己画的）**：`_zf178_draw.py` 确定性生成，16×16 RGBA：
**石头底**（16×16 灰石子噪点 + 几处 2×2 深浅颗粒）+ **7~9 坨矿斑**（不规则团块、心部亮边部暗、
左下压一像素深描边）。矿斑颜色是**从对应的 `textures\item\raw_<metal>.png` 里采样出来的**
（不透明像素按亮度取暗 20% / 中 50% / 亮 85% 三色）—— 所以方块上的料和物品是**同一块料**。
磁铁块另画：铁灰底 + 红色磁极斑（红取自 `magnet.png`）。出图后我逐张看过，不是纯色噪声块。

**④ 验收**：常驻门 `_zf178_verify.py` **18/0**（注册 / 14 条配方逐份核内容 / 7 张贴图 16×16·8 位·RGBA /
21 份模型 / 7 份 loot table / 2 个 tag / 7 个语言键 ×5 / 生成器表 0 失败 / 锂锰钛振金无块）；
反证刀 **7/7**（砍注册、砍配方数量、改产物 id、改贴图名、删 tag 项、删语言键、改掉落物 —— 每一刀都当场变红）。

**⑤ 要你实测**：创造页里应出现 7 个新方块；9 个磁铁合 1 块、1 块分解 9 个；粗矿同理。
贴图不满意就说一声，脚本里改配色/坨数都是一处的事。
"""

HAND41 = u"""41. **ZF178 的账（0.13：磁铁块 + 6 个粗矿块，贴图自己画）**：① 用户原话见档案 §9；**锂/锰/钛/振金不做块**
    （门里逐条断言"没有"）。② 磁铁块在 `ModBlocks`（装饰金属块属性）；6 个粗矿块走新写的
    `PotatoSTOres.rawBlock()` 工厂 —— 块物品自动进 `ALL_ORE_ITEMS` ⇒ **自动上创造页**。
    ③ 贴图 7 张由 `build\\zftools\\_zf178_draw.py` **确定性生成**（石头底 + 矿斑，配色从 `raw_<metal>.png` 采样；
    磁铁块 = 铁灰底 + 红磁极斑），出图后**逐张肉眼验过**。④ 14 条配方（7×3×3 的 9→1 + 7×shapeless 的 1→9）
    走生成器表 ⇒ 盘上 98 → 112；7 份 loot table、2 个 tag 各 +7、7 个键 ×5（621→628 / lzh 623→630）。
    ⑤ **两条工具/语法雷记进 §4.178**：生成器的 id 取证只认"方法名含 register"（工厂 `ore/raw/rawBlock` 漏掉 ⇒
    14 条假 FAIL）；`SHAPELESS` 列表第一个元素是推导式 ⇒ 新元素只能 `SHAPELESS += [...]`。
    ⑥ 门 `_zf178_verify.py` **18/0**、反证刀 **7/7**。⑦ 画贴图要用**工程自带的 Python**（PATH 上那个没 Pillow）。
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
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d" % (size, h, cls, recipes, keys_zh, keys_lzh))
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

    doc = read(DOC)
    if u"### 4.178 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF178 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.176 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF176 行尾锚点 %d 次" % doc.count(a2))
        else:
            # ⚠ 不能用 `%`/`.format()` 套 ROW —— 正文里既有 `{a,b,c}` 又有裸 `%`（本轮两次翻车：
            #   KeyError: 'aluminum,cobalt,...' / ValueError: unsupported format character）。
            row_text = (ROW.replace(u"{size}", u"{:,}".format(size))
                        .replace(u"{sha}", h).replace(u"{cls}", str(cls)))
            doc = doc.replace(a2, a2 + row_text + u"\n", 1)
    if u"### ZF178（0.13）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"41. **ZF178 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND41 + u"\n" + a4, 1)
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
    if u"## New in 0.13 ZF178" not in ann:
        a5 = u"## New in 0.13 ZF176 - Feed the sample with a pipe"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF176 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF178 - Magnet block and raw ore blocks\n\n"
                     u"- **New: the Magnet Block.** 9 magnets <-> 1 block, in both directions.\n"
                     u"- **New: six raw ore blocks** - raw aluminum, cobalt, nickel, silver, tungsten and\n"
                     u"  uranium (9 raw ore <-> 1 block, both directions). Lithium, manganese, titanium\n"
                     u"  and vibranium deliberately get no block.\n"
                     u"- They are proper ore-style blocks: same hardness/sound/tool rules as vanilla's raw\n"
                     u"  ore blocks, registered in the pickaxe and stone-tool block tags, with their own\n"
                     u"  loot tables, and they show up in the creative tab.\n"
                     u"- **All seven textures were drawn for this update** (16x16): a stone base with the\n"
                     u"  metal's specks, their colours sampled straight from our own raw ore items, so the\n"
                     u"  block and the item look like the same material; the magnet block is dark iron with\n"
                     u"  red pole specks.\n"
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
