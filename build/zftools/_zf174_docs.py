# -*- coding: utf-8 -*-
u"""_zf174_docs.py —— ZF174 文档落笔（§4.174 + §5 行 + §9 段 + 交接第 39 条 + 英文公告），
并把哈希/体积/class/配方/键数跟到刚打出来的那份 jar。

⚠ 轮号：`_zf170_*`/`_zf171_*`/`_zf172_*` 都已被别的线占用（他们的手册 4165 / 前置 / 另一件事），
本轮的编号取 **ZF174**（§4.147 轮号检查）。

跑法：python build\\zftools\\_zf174_docs.py [--write]
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

S4 = u"""### 4.174 【交互雷】机器"没吃下"这次交互时返回 `PASS` ⇒ 原版接着跑 `BucketItem#useOn`，**把桶里的流体倒进世界**（0.13 ZF174）

用户实测原话：「**shift+右键会把流体倒出来 而不是倒进版样**」——截图里手里是一铁桶汽油，
屏幕角落还写着「铁桶: 倒空」。病根不在倒的方向（潜行本来就是"倒进输出罐 = 设样板"），
而在**失败那条分支的返回值**：

```java
if (pour.moved() <= 0) { ...提示...; return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION; }
```

`PASS_TO_DEFAULT_BLOCK_INTERACTION` 的意思是"这一下我不管，交给后面" —— 而"后面"正是原版的
`BucketItem#useOn`：**它会把桶里的流体倒进世界**（对着方块倒就是放一个源方块）。
于是"样板被别的流体占着 / 罐收不下"这种**本该只是被拒绝**的情况，变成了**玩家凭空丢一桶流体**。

**正解**：手里是流体容器（我们的气罐/油桶、任何挂 NeoForge 物品流体能力的容器，**含空桶**）时，
机器**必须吃下**这次交互（`sidedSuccess(false)`）；只有手里不是流体容器（扳手、方块、食物…）才返回 PASS
—— 否则会挡住别的 mod 的正常交互。判据落在 `FluidConverterBlockEntity.isFluidContainer(...)`。

**教训**：凡是覆盖 `useItemOn` 的机器，**"我不处理"和"我处理了但什么都没发生"是两件事** ——
前者会把交互让给原版（桶倒世界、打火石点火、骨粉催熟），后者才是"这次没成，但别乱动"。
探针 `Zf174Check`（真 `FakePlayer` + 真 `BlockHitResult` 调 `BlockState#useItemOn`）验的就是
"结果到底吃没吃下"，`_zf168_verify.py` 的 F 段与反证刀 K7 钉住这条。

"""

ROW = u"""| ZF174 | **无新备份根**（本轮只改 `FluidConverterBlock` / `FluidConverterBlockEntity` 两份 java + 门/探针脚本 + 三份文档；改前件由 `git show HEAD:` 取，与 ZF164/ZF168 同例。⚠ 开工前查过轮号：`_zf170_*` / `_zf171_*` / `_zf172_*` **都已被别的线占用** ⇒ 本轮取 **ZF174**（§4.147）） | **0.13：修「shift+右键会把流体倒出来」**（用户原话见 §9）。① **病根**（§4.174）：失败分支返回 `PASS_TO_DEFAULT_BLOCK_INTERACTION` ⇒ 原版接着跑 `BucketItem#useOn`，**把桶里的流体倒进世界**（玩家凭空丢一桶）。② **正解**：手里是流体容器（**含空桶**）时必须**吃下**交互（`sidedSuccess(false)`），手里不是流体容器才 PASS（不挡别的 mod）；判据收在 `FluidConverterBlockEntity.isFluidContainer(...)`。③ **block 级探针 `Zf174Check` 9/0**：真 `FakePlayer` + 真 `BlockHitResult` 调 `BlockState#useItemOn` —— 满桶岩浆对着"水样板"潜行右键 ⇒ **交互被吃下**、样板/输入罐/手里的桶**全都没动**；负对照（钻石 ⇒ **不**吃下）；并复验 ZF168 那条"空桶右键把样板装走"（C 段）与不潜行方向（D 段）。④ 门 `_zf168_verify.py` 加 F 段 ⇒ **24/0**；反证刀加到 **7/7**（K7 砍的就是这一行）。 | 见 §9 ｜ 见 §4.174 |
"""

S9 = u"""### ZF174（0.13）修「shift+右键会把流体倒出来」—— **不会再洒进世界里了**

你报的原话（还带截图）：「**shift+右键会把流体倒出来 而不是倒进版样**」，截图里手里是一铁桶汽油、
屏幕角落写着「铁桶: 倒空」。查清了：**不是倒的方向错了**（潜行本来就是"倒进输出罐 = 设样板"），
而是**机器拒绝的那一下把交互让给了原版**：

- 机器这次没收下（比如样板罐里已经是**另一种**流体、或者罐收不下）时代码返回
  `PASS_TO_DEFAULT_BLOCK_INTERACTION` —— 这个返回值的含义是"这一下我不管，交给后面"；
- "后面"就是原版的**桶**：它会把桶里的流体**倒进世界**（对着方块倒就是放一个源方块）。
- 于是"本该只是被拒绝"的情况变成了"**玩家凭空丢一桶流体**"。

**现在**：手里是流体容器（空桶 / 满桶 / 我们的气罐油桶 / 别的 mod 的容器）时，机器**一定吃下**这次交互
—— 原版桶再没有机会；手里不是流体容器（扳手、方块、食物…）时才让给原版，免得挡住别的 mod。
该给的那句提示照旧：「输出罐里已经是别的流体（X）—— 手拿空容器右键机器就能把样板装走，然后再倒新的」。

**实测证据（真服务端，block 级）**：满桶岩浆对着"水样板"潜行右键 ⇒ **交互被吃下**（`consumesAction()`）、
水样板 1000 mB 一分不动、**手里的岩浆桶还在**、输入罐也没动；负对照：手里是**钻石**时**不**吃下；
同一份探针里复验了"空桶右键把样板装走"那条路（手里变水桶）—— **9/0 全绿**。

**要你实测**：拿一桶跟样板**不一样**的流体对着转化器潜行右键 —— 应该**什么都不洒**，
只在聊天栏看到那句提示；拿空桶右键仍然能把样板装走。
"""

HAND39 = u"""39. **ZF174 的账（0.13：修「shift+右键会把流体倒出来」）**：① 用户原话与截图见档案 §9；病根是
    **交互返回值**（§4.174）：失败分支返回 `PASS` ⇒ 原版 `BucketItem#useOn` 把桶里的流体**倒进世界**。
    ② 正解：手里是流体容器（**含空桶**）就**吃下**这次交互（`sidedSuccess(false)`），不是流体容器才 PASS；
    判据 = `FluidConverterBlockEntity.isFluidContainer(...)`。③ 探针 `Zf174Check` **9/0**
    （真 `FakePlayer` + 真 `BlockHitResult` 调 `BlockState#useItemOn`，验的就是"吃没吃下"）；
    门 `_zf168_verify.py` 加 F 段（**24/0**），反证刀 **7/7**。④ ⚠ 通用教训：覆盖 `useItemOn` 的机器，
    "我不处理"与"我处理了但什么都没发生"是两件事 —— 前者会把交互让给原版（桶倒世界、打火石点火、
    骨粉催熟），后者才是"这次没成，但别乱动"。⑤ **轮号**：`_zf170_/171_/172_` 已被别的线占用，本轮 ZF174。
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
    m = re.search(u'WANT_SHA = u"([0-9a-f]{40})"', v149)
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
    if u"### 4.174 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF174 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.173 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF168 行尾锚点 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW + u"\n", 1)
    if u"### ZF174（0.13）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"39. **ZF174 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND39 + u"\n" + a4, 1)
    hand = hand.replace(u"**ZF168 转换器样板可换（新）**",
                        u"**ZF168 转换器样板可换** / **ZF174 拒绝时不再洒流体（新）**")
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = read(V149)
    vn = re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, vn, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == read(V149):
        fails.append(u"_zf149_verify.py：一个靶子都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF174" not in ann:
        a5 = u"## New in 0.13 ZF168 - The Fluid Converter's output tank can now be changed"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF168 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF174 - No more spilling fluid into the world\n\n"
                     u"- **Fixed: sneak-right-clicking the Fluid Converter with a bucket no longer pours\n"
                     u"  the fluid out onto the ground.** When the machine refused the fluid (for example\n"
                     u"  because the sample tank already holds a different one), it handed the interaction\n"
                     u"  back to vanilla - and vanilla's bucket emptied itself into the world.\n"
                     u"- **Now the machine consumes that interaction whenever you are holding a fluid\n"
                     u"  container** (empty bucket, full bucket, our gas tank / oil drum, another mod's\n"
                     u"  container). Nothing is spilled; you just get the line telling you to take the old\n"
                     u"  sample out with an empty container first. Non-container items behave as before.\n"
                     u"- Verified on a real server at the block-interaction level (fake player + real block\n"
                     u"  hit result calling `BlockState#useItemOn`): interaction consumed, sample untouched,\n"
                     u"  lava bucket still full - plus a negative control (diamond is not consumed) and a\n"
                     u"  re-check of the ZF168 \"empty container takes the sample out\" path. 9/0.\n"
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
