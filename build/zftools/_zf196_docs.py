# -*- coding: utf-8 -*-
u"""_zf196_docs.py —— ZF196 文档落笔（§4.196 + §5 行 + §9 段 + 交接第 50 条 + 英文公告 +
中英双语公告）+ 哈希三处联动 + **两道老门的判据跟平**（`_zf190` 的 B5、`_zf194` 的 A1/A5）。

主题：坍缩模式"看得见地拆" —— 近处优先 + 像爆炸那样的碎裂。
跑法：python build\\zftools\\_zf196_docs.py [--write]
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
V190 = os.path.join(ROOT, "build", "zftools", u"_zf190_verify.py")
V194 = os.path.join(ROOT, "build", "zftools", u"_zf194_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.196 【效果雷】「没有效果」的真凶：游标扫得**太远太慢**——坍缩模式改成近处优先 + 像爆炸那样碎裂（0.14 ZF196）

用户原话：「**没有效果啊 要像爆炸那样的 黑洞旁边的方块明显被破坏**」。

**① 真凶不是"没吸"，是"头 3 秒什么都没吸到"。** 老实现（ZF172 起）用一条**线性游标**扫 81³ 个位置：
从 `(-40,-40,-40)` 那个角开始往后走，每 tick 看 4096 个 ⇒ **要 ~65 tick（3.25 秒）才轮到黑洞身边的东西**。
而坍缩模式默认只活 **80 tick**（8M 装置：召唤 4M + 每 tick 50k）⇒ 玩家看到的就是"放了个黑洞，
它一直在翻远处的地皮，我旁边啥也没变" ✓ 这解释了用户那句"没有效果"。

**② 坍缩模式整个换一套吃法**：不走游标，改成**球内随机取样**（每 tick {@code DEMOLISH_SAMPLES = 2048} 次），
取样半径用 `U(0, R)`（**不是**体积均匀）⇒ 体密度 ∝ 1/r² ⇒ **先啃脚边那一圈、再一圈圈往外扩**；
R 从 3 格起、每 tick +0.08（每秒约 1.6 格），封顶 24 格**且不超过配置的扫描半径**。
落地第一 tick 就见效 —— 这才是"旁边的方块明显被破坏"。

**③ "像爆炸那样"是一个具体的事件号**：拆方块走原版的
`LevelEvent.PARTICLES_DESTROY_BLOCK`（**2001**）—— 客户端收到就放该方块的**碎裂粒子 + 破坏音效**，
原版爆炸拆方块用的就是它。所以"像爆炸"不是加特效，是**用对事件**。⚠ 不掉落物品
（坍缩模式的掉落物本来就会被销毁）。

**④ 两种吃法（ZF194 的教训在这里收尾）**：
  · **露着的**（至少一面贴空气）⇒ 变成下落方块朝奇点飞、到中心清除（ZF194 那套，看得见地飞）；
  · **埋着的**（六面都堵）⇒ **就地拆**。原因是 ZF194 的实测反馈：埋着的方块变成下落方块也**飞不出来**，
    卡在方块里更像"没效果"。
  ⚠ 弹坑一开，原来的"埋着"立刻就变成"露着"了 ⇒ **从外面看不出来**某一块是被拆的还是飞的
  （本条因此加了个诊断计数 `demolishedTotal()`，探针/门才分得开；生产逻辑不依赖它）。

**⑤ ⚠ 天上飞满了也必须继续吃。** `MAX_FLYING = 48` 一占满，旧写法是**跳过**那些露着的方块 ⇒
"盯着脚边的方块却什么都不干"（探针里 48 个残留把上限占满时，S1/S4/Q1 三条一起假红就是这个）。
现在改成：**飞的满了就就地拆**，任何情况下都不空手站着。

**⑥ ⚠ 探针清场口 `clear()` 现在顺手收掉"在飞的下落方块"。** 它们本来就是这次试验造出来的，
而探针里服务端不 tick、它们不会自己走 ⇒ 留着会一直占着 48 的上限，**把下一次试验堵死**
（本轮真踩过：48/48 占满 ⇒ 后面几条全假红）。`Zf194Check` 的 Q5 也因此改了验证方式：
不再拿 `clear()` 当"黑洞没了"，而是**给它一个刚够召唤的小电源、让它自己断电消失**（真实路径）。

**⑦ 跟平的老判据（都是本轮代码真的动了它们）**：`_zf190_verify.py` 的 B5（`Block moved` /
`placeAt(hole, p, moved)` 这套写法没了）、`_zf194_verify.py` 的 A1（`launchFalling` 的调用形态变了）、
A5（坍缩模式已经不走那条带禁采区的游标路了 ⇒ 改成量"一进门就分派给 `collapseEat`"）。
探针侧同样跟平：`Zf190Check` 的 B5 预算 100→500（坍缩模式现在**落地就吃地形**，100 块会被地形吃光）、
`Zf194Check` 的 Q4（去掉"15 格外那块一定被搬走"这条不稳的判据）、Q5（改成断电路径）、
`Zf196Check` 的 S4（半径 r(60)=7.8 还没到 8 格 ⇒ 改 120 tick）。

"""

ROW = u"""| ZF196 | **新建 `zf196_pre`**（**132 份**改前件：1 份将改源码 + `neoforge.mods.toml` + 五份 lang + 4 份文档 + 8 份脚本 + 前几轮五道门与五个探针 + 旧成品与 `.sha1` + **全部常驻门 106 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf196_*` / §4.196 查过没人占（§4.147）） | **0.14：坍缩模式"看得见地拆"（近处优先 + 像爆炸那样碎裂）**（用户原话见 §9）。① **真凶**：老实现那条线性游标要从扫描区一角走 ~65 tick 才轮到身边的东西，而坍缩模式默认只活 80 tick ⇒ 用户看到「没有效果」（§4.196①）。② 坍缩模式改走**球内随机取样**（`U(0,R)`，体密度 ∝ 1/r² ⇒ 先啃脚边、再往外扩），R 从 3 格每秒涨约 1.6 格、封顶 24 且不超过配置扫描半径（§4.196②）。③ 拆方块走原版 **2001** 事件（碎裂粒子 + 音效 = 「像爆炸那样」），不掉落（§4.196③）。④ 露着的飞进奇点（ZF194 那套）、埋着的就地拆（§4.196④）。⑤ **飞的满了也照样就地拆**，不空手站着（§4.196⑤）。⑥ `clear()`（探针清场口）顺手收掉在飞方块 + 新增诊断计数 `demolishedTotal()`（§4.196⑥）。⑦ **探针 `Zf196Check` 5/0**（身边被拆 / 半径随年龄涨 / 两条路都在干活 / 露着的仍飞 / 上限生效）+ 回归 `Zf194Check` 5/0、`Zf192Check` 6/0、`Zf190Check` 16/0、`Zf186Check` 20/0、`Zf188Check` 4/0。⑧ 门 `_zf196_verify.py` **15/0**、反证刀 **8/8**；**跟平**了 `_zf190_verify.py` 的 B5 与 `_zf194_verify.py` 的 A1/A5（§4.196⑦）。⑨ **本轮不动语言键**（五语种仍 691 / lzh 693）。⑩ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.196 |
"""

S9 = u"""### ZF196（0.14）坍缩模式"看得见地拆"：身边一圈圈炸开，方块碎着被吞

你说"没有效果"，我找到了真凶 —— **不是没吸，是头 3 秒没吸到旁边**：

- **以前**：黑洞用一条"游标"从扫描区的一角（离你 40 米远的地下）往后翻，**要 3.25 秒才轮到身边的东西**；
  而坍缩模式默认只活 **4 秒**（8M 装置：召唤 4M + 每 tick 5 万）⇒ 你看到的就是"它一直在翻远处的地皮"。
- **现在**：坍缩模式改成**从脚边一圈圈往外啃**（半径 3 格起步，每秒涨约 1.6 格，最大 24 格，
  也不会超过你配置的扫描半径）—— 放下去**第一 tick 就见效**。
- **"像爆炸那样"是按你说的做的**：拆方块走的是原版爆炸用的那个**方块碎裂事件（2001）**，
  所以是**真的碎裂粒子和破坏音效**，不只是"方块凭空不见"。
- 两种吃法：**露在外面的**（墙上、地面上、树上的）变成下落方块**飞进黑洞中心再清除**；
  **埋在里面的**（六面都堵着）**就地拆掉** —— 因为埋着的变成下落方块也飞不出来，卡在里面更像没效果。

**实测**（真服务端，5/0）：身边 3 格那块 20 tick 内被拆 ✓；同一个洞里 20 格外那块
**早期不动**（半径才 4.6）、跑够 400 tick 就被吃掉（半径封顶 24）✓；一个洞里两种吃法都在干活 ✓；
空气里的方块照旧变成下落方块飞进中心 ✓；上限仍然生效（上限设 30、9³ 石堆里正好被拆 30 块）✓。

⚠ 一句实话：**"好不好看"还是只能你自己进游戏看** —— 我这边只验到"事件发对了、半径会长、
近处优先、上限还在"。放一个试试，觉得太慢/太快说一声，`DEMOLISH_GROWTH_PER_TICK`（现在 0.08）
和 `BLOCKS_PER_TICK`（24）就是那两个旋钮。
"""

HAND50 = u"""50. **ZF196 的账（0.14：坍缩模式"看得见地拆"）**：① 用户原话见档案 §9；**真凶**是原来那条线性游标
    要 ~65 tick 才轮到身边的东西，而默认只活 80 tick ⇒「没有效果」（§4.196①）。② 坍缩模式改走**球内随机取样**
    （`U(0,R)` ⇒ 近处优先），R 从 3 格每秒涨 ~1.6 格、封顶 24 且不超配置扫描半径。③ 拆方块走原版 **2001**
    事件（碎裂粒子 + 音效）= 「像爆炸那样」；不掉落。④ 露着的飞（ZF194）、埋着的就地拆。⑤ ⚠ **飞的满了也照样就地拆**
    （旧写法是"跳过" ⇒ 盯着方块不动手）。⑥ ⚠ `clear()` 顺手收在飞方块（不然 48 上限被上次试验占满，下一次全假红）+
    诊断计数 `demolishedTotal()`。⑦ 探针 `Zf196Check` **5/0**、`Zf194Check` 5/0、`Zf192Check` 6/0、`Zf190Check` 16/0、
    `Zf186Check` 20/0、`Zf188Check` 4/0；门 `_zf196_verify.py` **15/0**、反证刀 **8/8**；**跟平** `_zf190` 的 B5、
    `_zf194` 的 A1/A5 与三个探针（§4.196⑦）。⑧ 本轮**没动语言键**。
"""

BIL_ZH = u"""
- **0.14 追加（ZF196）坍缩模式"看得见地拆"**：以前它用游标从 40 米外的角落往后翻，**要 3 秒多才轮到身边**，
  而默认只活 4 秒 ⇒ 看着像没效果。现在**从脚边一圈圈往外啃**（3 格起步，每秒涨约 1.6 格，最大 24 格），
  **放下去就见效**；拆方块走原版爆炸用的那个**方块碎裂事件**（真的碎裂粒子 + 破坏音效）。
  露在外面的方块**飞进黑洞中心再清除**，埋在里面的**就地拆掉**。
"""

BIL_EN = u"""
- **0.14 follow-up (ZF196) - Collapse mode now visibly tears the area apart:** it used to blunder through a
  40-block-wide scan, taking **over 3 seconds** to reach anything next to you, while the default black hole
  only lives **4 seconds** - which looked like "no effect". It now **eats outward from its own feet**
  (3 blocks and growing ~1.6 blocks per second, up to 24), so you see it act on the very first tick, and
  every block it destroys uses vanilla's **block-destruction event** (the same one explosions use, with real
  break particles and sounds). Blocks exposed to air **fly into the singularity and are erased there**;
  blocks buried inside the ground are **destroyed in place**.
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
    if u"### 4.196 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF196 |" not in doc:
        a2 = u"（class 410；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.194 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF194 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF196（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"50. **ZF196 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND50 + u"\n" + a4, 1)
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

    # ── ① `_zf190_verify.py` 的 B5 跟平：坍缩模式改成"下落下落/就地拆"，码放那条路只剩普通模式 ──
    v190 = read(V190)
    old_b5 = (u'          and u"Block moved = collapse ? state.getBlock() : hole.block;" in hole_c\n'
              u'          and u"placeAt(hole, p, moved)" in hole_c,\n'
              u'          u"B5 「无差别」吸方块（搬的是**原位那一种**），边界 = 空气/流体/不可破坏（基岩那类）")')
    new_b5 = (u'          # 0.14 ZF196 跟平：坍缩模式不再"码放"（露着的飞、埋着的就地拆）⇒\n'
              u'          # 判据改成看**意图**：`eatable` 的边界 + 普通模式只搬副手那一种、码到脚下\n'
              u'          and u"if (!state.is(hole.block)) {" in hole_c\n'
              u'          and u"placeAt(hole, p, hole.block)" in hole_c,\n'
              u'          u"B5 「无差别」的边界 = 空气/流体/不可破坏（基岩那类）；普通模式只搬副手那一种")')
    if old_b5 in v190:
        v190 = v190.replace(old_b5, new_b5, 1)
        print(u"  `_zf190_verify.py`：B5 判据已跟平")
    elif u"placeAt(hole, p, hole.block)" in v190:
        print(u"  `_zf190_verify.py`：B5 已经是新判据，跳过")
    else:
        fails.append(u"_zf190_verify.py：B5 锚点找不到（跟平失败）")
    if write and not fails:
        io.open(V190, "w", encoding="utf-8", newline=u"").write(v190)

    # ── ② `_zf194_verify.py` 的 A1 / A5 跟平 ──
    v194 = read(V194)
    old_a1 = (u'    check(u"if (launchFalling(hole, p, state)) {" in hole_c\n'
              u'          and u"flyingLeft--;" in hole_c\n'
              u'          and u"if (flyingLeft <= 0) {" in hole_c\n'
              u'          and u"level.getEntitiesOfClass(FallingBlockEntity.class, flyBox).size());" in hole_c,')
    new_a1 = (u'    # 0.14 ZF196 跟平：飞这条路的调用形态变了（现在是 `collapseEat` 里的一个分支，\n'
              u'    # 而且"飞的满了就就地拆"）⇒ 判据看**意图**：飞行上限一次算好 + 逐块减。\n'
              u'    check(u"launchFalling(hole, p, state)" in hole_c\n'
              u'          and u"flyingLeft--;" in hole_c\n'
              u'          and u"int flyingLeft = Math.max(0, MAX_FLYING" in hole_c\n'
              u'          and u"level.getEntitiesOfClass(FallingBlockEntity.class, flyBox).size());" in hole_c,')
    old_a5 = (u'    check(u"if (!collapse && Math.abs(dx) <= PILE_GUARD" in hole_c,\n'
              u'          u"A5 坍缩模式**不设禁采区**（它没有「码放」这一步，而且连脚边那圈也吸才看得出它在吃周围）")')
    new_a5 = (u'    # 0.14 ZF196 跟平：坍缩模式已经**不走那条带禁采区的游标路**了 ⇒ 改成量"一进门就分派"：\n'
              u'    # 它压根不经过那条扫，禁采区自然管不到它。\n'
              u'    check(u"if (hole.mode == GravityDeviceItem.MODE_COLLAPSE) {" in hole_c\n'
              u'          and u"collapseEat(hole);" in hole_c\n'
              u'          and u"if (Math.abs(dx) <= PILE_GUARD" in hole_c,\n'
              u'          u"A5 坍缩模式**不走**那条带禁采区的游标路（一进门就分派给 collapseEat）")')
    for old, new, tag in ((old_a1, new_a1, u"A1"), (old_a5, new_a5, u"A5")):
        if old in v194:
            v194 = v194.replace(old, new, 1)
            print(u"  `_zf194_verify.py`：%s 判据已跟平" % tag)
        elif new.split(u"\n")[-1] in v194:
            print(u"  `_zf194_verify.py`：%s 已经是新判据，跳过" % tag)
        else:
            fails.append(u"_zf194_verify.py：%s 锚点找不到（跟平失败）" % tag)
    if write and not fails:
        io.open(V194, "w", encoding="utf-8", newline=u"").write(v194)

    ann = read(ANN)
    if u"## New in 0.14 ZF196" not in ann:
        a5 = u"## New in 0.14 ZF194 - You can now watch Collapse mode eat"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF194 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF196 - Collapse mode now visibly tears the area apart\n\n"
                     u"- **Why it looked like nothing happened:** the black hole walked a linear cursor across\n"
                     u"  its whole 40-block scan volume, starting at a far corner, so it needed **about 3.25\n"
                     u"  seconds** before it touched anything next to you - while a default device only keeps\n"
                     u"  the black hole alive for **4 seconds**. It was not idle; it was rummaging far away.\n"
                     u"- The Collapse mode no longer uses that cursor. It now **eats outward from its own feet**:\n"
                     u"  random sampling in a ball whose radius starts at 3 blocks and grows about 1.6 blocks\n"
                     u"  per second (capped at 24, and never above your configured scan radius).\n"
                     u"- Every destroyed block uses vanilla's **block-destruction event (2001)** - the same one\n"
                     u"  explosions use - so you get real break particles and break sounds, not silent removal.\n"
                     u"- **Exposed** blocks (touching air) turn into falling blocks, fly into the singularity and\n"
                     u"  are erased there; **buried** blocks are destroyed in place, because a buried falling\n"
                     u"  block cannot fly anywhere and only looks like nothing is happening.\n"
                     u"- If 48 blocks are already in flight the black hole now **destroys exposed blocks in\n"
                     u"  place instead of skipping them** - it never just stares at a block.\n"
                     u"- Measured on a real server (5 checks, all green): a block 3 blocks away is destroyed\n"
                     u"  within 20 ticks; in the same hole a block 20 blocks away is untouched early on\n"
                     u"  (radius 4.6) and eaten after 400 ticks (radius capped at 24); both eating paths run;\n"
                     u"  blocks in the air still fly in; and the `max_blocks` cap still holds (30).\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加（ZF196）" not in bil:
        az2 = u"  还在飞的方块会照常落地变回方块 —— **不凭空丢东西**。\n"
        ae2 = u"  destroyed by accident.\n"
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
