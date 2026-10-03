# -*- coding: utf-8 -*-
u"""_zf194_docs.py —— ZF194 文档落笔（§4.194 + §5 行 + §9 段 + 交接第 49 条 + 英文公告 +
中英双语公告）+ 哈希三处联动。

主题：坍缩模式的方块改成**下落方块飞向奇点、到中心清除**。
跑法：python build\\zftools\\_zf194_docs.py [--write]
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
BIL = os.path.join(ROOT, "docs", u"0.13_0.14更新公告与介绍_中英.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.194 【视觉雷】「看不出来在吸方块」—— 方块要**变成下落方块飞进中心再清除**（0.14 ZF194）

用户原话：「**看不出来坍缩模式在吸取周围方块（做成把方块变成下落形式的 吸取到黑洞中心位置再清除）**」。

**① 病根**：坍缩模式（ZF190）虽然「无差别吸」，但走的是和普通模式**同一条**「先 `placeAt` 码到脚下、
再 `removeBlock`」的路子 ⇒ 玩家视角里方块是**瞬间消失**、脚下莫名多出一堆，**看不见"被吸"的过程**。
修法：方块换成 `FallingBlockEntity` —— 起飞 → 每 tick 朝奇点校正速度 → 进 `CLEAR_RADIUS`（2.5 格）**清除**。

**② 那段代码本来就是现成的，而且一直是死代码。** `launchFalling` 是 0.14 ZF170 写下的
（当时名义上是给模式 1「引力牵引」用的），但**从来没有被调用过** —— 模式 1 实际走的也是码放。
本轮把它**接给坍缩模式**并按「到中心清除」改写。教训记一笔：**写下来没接上的代码 = 迟早要重新发现一遍**。

**③ 性能：天上飞的数量有硬上限，但别在循环里查。** `MAX_FLYING = 48` 是防实体爆炸的老上限；
旧写法（`launchFalling` 内部自己查一次实体）会在 `pullBlocks` 的循环里**每块查一次** ⇒
一 tick 最多 24 次实体查询。现在**一次查好**（`flyingLeft`）再逐块减。

**④ ⚠ 重力不能关。** `setNoGravity(true)` 会让这些方块在黑洞半路消失（断电 / 操作者走人 / 2 分钟炸掉）
之后**永远朝一个方向飞下去**。所以只给"吸"的那一份速度、重力照旧 ⇒ 黑洞没了它们会**正常落地变回方块**。
探针 Q5 专门钉住"断电之后不再清除"。

**⑤ 「无差别」这次才是真无差别。** 坍缩模式**不再设禁采区**（`PILE_GUARD`）：它没有"码放"这一步，
禁采区的理由（别把自己刚码的又吸一遍）对它不存在；而且**连脚边那一圈也吸**，才看得出它真的在吃周围。

**⑥ ⚠ 探针的"预算"与"别人的残留"也会骗人（Q4 连红两次，都不是被测代码的错）：**
  · 洞开在「出生点坐标 y + 40/60」上，而出生点在山坡上 ⇒ 扫描范围（±40）**够到了地表**，
    黑洞先把 100 块（`max_blocks`）地形搬光，我摆的那块**永远轮不到** ⇒ 洞必须开在「**地表高度 + 60**」
    （`level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z)`）；
  · 「一个下落方块都没有」这个判据被**别的探针留下的在飞方块**污染 ⇒ 改成「**这次没有新增**」（前后计数比）。
  与 §4.192④ 同一条教训：**假红先看诊断、先想环境**。

**⑦ ⚠ 收尾顺序（本轮踩了一分钟）**：探针类**挂载期间**跑常驻门会假红 ——
`_zf188_verify.py` 的「『configured』不许出现在非客户端代码里」会把挂着的 `Zf188Check.java` 当成正式源码。
⇒ **先卸探针、再跑门**。

"""

ROW = u"""| ZF194 | **新建 `zf194_pre`**（**130 份**改前件：1 份将改源码 + `neoforge.mods.toml` + 五份 lang + 4 份文档 + 8 份脚本 + 前几轮四道门与四个探针 + 旧成品与 `.sha1` + **全部常驻门 105 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf194_*` / §4.194 查过没人占（§4.147）） | **0.14：坍缩模式的方块改成「下落方块飞向奇点、到中心清除」**（用户原话见 §9）。① 坍缩分支不再码放，改走 `launchFalling`（复活 ZF170 写下却**从未接上**的死代码，§4.194②）。② 新增 `consumeFalling`：每 tick 把下落方块继续拉向中心，进 `CLEAR_RADIUS = 2.5` 格就 `discard()` 清除（不留方块、不掉物品，§4.194①）。③ 天上飞的数量改成**一次查好**（`flyingLeft`），不再逐块查实体（§4.194③）。④ **不禁用重力**：黑洞半路没了，在飞的方块照常落地变回方块（探针 Q5 钉住，§4.194④）。⑤ 坍缩模式**取消禁采区**（脚边那一圈也吸，§4.194⑤）。⑥ **探针 `Zf194Check` 5/0**（变下落方块 / 速度正对中心 1.000 / 到中心清除 / 反面自证普通模式仍码放 / 断电后不清除）+ 回归 `Zf192Check` 6/0、`Zf190Check` 16/0、`Zf186Check` 20/0、`Zf188Check` 4/0。⑦ 门 `_zf194_verify.py` **14/0**、反证刀 **8/8**；**没有改任何老判据**（四道老门仍全绿）。⑧ **本轮不动语言键**（五语种仍 691 / lzh 693）。⑨ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.194 |
"""

S9 = u"""### ZF194（0.14）坍缩模式现在**看得见**了：方块变成下落方块飞进中心再清除

按你说的做了：

- **以前**：方块"啪"一下没了、脚下莫名多一堆 —— 完全看不出来它在吸（你报的就是这个）。
- **现在**：周围的方块会**变成下落方块朝黑洞飞**，一路被吸着加速，进到中心 **2.5 格以内直接被清除**
  （不掉落、不落地、不留痕迹），到中心还会冒一记闷响似的黑雾。
- 顺带把「无差别」做实了：**连脚边那一圈也吸**（以前留了 12 格"禁采区"不吸）。

**实测**（真服务端，5/0）：原位清空 + 场上确实出现下落方块 ✓；它的速度方向**正对黑洞中心**
（方向余弦 **1.000**）✓；挪到中心那一 tick 就被清除（中心还是空气、没有掉落物）✓；
**反面自证**：普通模式仍然是"码到脚下"、全程没有下落方块 ✓；
**黑洞断电消失之后，还在飞的方块不会被清除** —— 它们会照常落地变回方块，**不凭空丢东西** ✓。

⚠ 一句丑话：探针只能验"方向对、到中心会清、断电不清"，**"好不好看"只能你自己进游戏看**
（这次改动就是冲着眼睛去的，去放一个试试）。
"""

HAND49 = u"""49. **ZF194 的账（0.14：坍缩模式改成"下落方块飞向中心再清除"）**：① 用户原话见档案 §9；病根与五条设计决定见 §4.194。
    ② **复活了一段死代码**：`launchFalling` 是 ZF170 写下、**从未被调用**的（模式 1 名义上用它，实际走码放）
    —— 教训：写下来没接上的代码迟早要重新发现一遍。③ ⚠ **重力不能关**（`setNoGravity` 会让断电后的方块永远飞）。
    ④ ⚠ **天上飞的数量一次查好**（`flyingLeft`），别在 `pullBlocks` 循环里逐块查实体。
    ⑤ 坍缩模式**取消禁采区**（脚边也吸）。⑥ **探针 Q4 连红两次都是环境**：洞开在"出生点 y + 40/60"上、
    而出生点在山坡 ⇒ 扫描够到地表、100 块预算被地形吃光；判据又被别的探针留下的在飞方块污染
    ⇒ 改成"洞开在地表 + 60" + "这次没有新增下落方块"。⑦ ⚠ **先卸探针再跑门**（挂着的 `Zf188Check.java`
    会让 `_zf188_verify.py` 的「configured 不许出现在非客户端代码」假红）。⑧ 探针 `Zf194Check` **5/0**、
    四道老门全绿、本轮**没改任何老判据**、**没动语言键**；门 `_zf194_verify.py` **14/0**、反证刀 **8/8**。
"""

BIL_ZH = u"""
- **0.14 追加（ZF194）坍缩模式"看得见"了**：周围的方块会**变成下落方块朝黑洞飞**，进到中心 2.5 格就
  **直接清除**（不掉落、不落地）；顺带**连脚边那一圈也吸**（取消旧禁采区）。黑洞断电消失时，
  还在飞的方块会照常落地变回方块 —— **不凭空丢东西**。
"""

BIL_EN = u"""
- **0.14 follow-up (ZF194) - you can now watch Collapse mode eat:** nearby blocks turn into **falling
  blocks that fly into the black hole** and are **erased** inside 2.5 blocks of the centre (no drops, no
  landing). The old 12-block "no-eat" ring around the hole is gone too, so it really does eat everything.
  If the black hole loses power mid-flight the blocks simply land and turn back into blocks - nothing is
  destroyed by accident.
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
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    z.close()
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d" % (size, h, cls, recipes, adv))

    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        text = re.sub(u"\\*\\*\\d+ classes, \\d+ advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, %d advancements, %d recipes**" % (cls, adv, recipes), text)
        return text

    doc = read(DOC)
    if u"### 4.194 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF194 |" not in doc:
        a2 = u"（class 410；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.192 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF192 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF194（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"49. **ZF194 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND49 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    if vn == v149:
        if (u'WANT_SHA = u"%s"' % h) in v149:
            print(u"  （_zf149_verify.py 的靶子已经就是这份成品，跳过）")
        else:
            fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.14 ZF194" not in ann:
        a5 = u"## New in 0.14 ZF192 - Collapse mode can be fired with an empty offhand"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF192 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF194 - You can now watch Collapse mode eat\n\n"
                     u"- The old behaviour was invisible: blocks simply vanished and a pile appeared under the\n"
                     u"  black hole. Now the blocks around it **turn into falling blocks and fly into the\n"
                     u"  singularity**, and they are **erased** once they get within 2.5 blocks of the centre\n"
                     u"  (no drops, no landing, just a puff of ink and a flash).\n"
                     u"- The old 12-block \"do not eat\" ring around the hole is **gone for this mode**, so it\n"
                     u"  really does eat everything around it, including the blocks right next to it.\n"
                     u"- Safety: gravity is deliberately left ON. If the black hole disappears mid-flight\n"
                     u"  (power cut, the owner leaving, the 2-minute fuse) the flying blocks simply land and\n"
                     u"  turn back into blocks - nothing is destroyed by accident.\n"
                     u"- At most 48 blocks fly at once (unchanged cap), and the count is now fetched once per\n"
                     u"  tick instead of once per block.\n"
                     u"- Measured on a real server (5 checks, all green): the source position becomes air and\n"
                     u"  a falling block appears; its velocity points straight at the centre (direction\n"
                     u"  cosine 1.000); moving it to the centre clears it and leaves no block or drop behind;\n"
                     u"  the two normal modes still place blocks instead (no falling block involved); and\n"
                     u"  after the black hole is gone the blocks in flight are no longer cleared.\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加（ZF194）" not in bil:
        az2 = u"  空手时动作栏那句改成「它开始吸取周围的一切了」（为此加了 1 个语言键，五语种都有）。\n"
        ae2 = u"  five languages).\n"
        if bil.count(az2) != 1 or bil.count(ae2) != 1:
            fails.append(u"双语公告锚点 zh=%d en=%d" % (bil.count(az2), bil.count(ae2)))
        else:
            bil = bil.replace(az2, az2 + BIL_ZH, 1)
            bil = bil.replace(ae2, ae2 + BIL_EN, 1)
    bil = refresh(bil)
    if write and not fails:
        io.open(BIL, "w", encoding="utf-8", newline=u"").write(bil)

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
