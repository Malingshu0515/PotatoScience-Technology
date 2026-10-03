# -*- coding: utf-8 -*-
u"""_zf192_docs.py —— ZF192 文档落笔（§4.192 + §5 行 + §9 段 + 交接第 48 条 + 英文公告 +
中英双语公告）+ 哈希三处联动 + **三道老门的判据跟平**。

主题：坍缩模式**空手也能放**（+ 探针判据的环境坑）。
跑法：python build\\zftools\\_zf192_docs.py [--write]
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
V188 = os.path.join(ROOT, "build", "zftools", u"_zf188_verify.py")
V190 = os.path.join(ROOT, "build", "zftools", u"_zf190_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.192 【空手雷】「空手也能放」要放行三处，而且 AIR 哨兵不能让存档把它丢掉（0.14 ZF192）

用户原话：「**坍缩模式空手也能放**」。

**① 「要不要副手方块」是一道三处的门。** `use()`（开始蓄力）、`onUseTick()`（蓄力途中）、
`fire()`（松手开火）各有一处 `offhandBlock(player) == null`。只放行 `use()` 的话，
蓄力的第一 tick 就会被 `onUseTick` 取消（动作栏还会说"副手方块消失，蓄力中断"）；
只放行两处的话开火那一关仍然拦着。门 A1 三处一起钉，探针 P1/P4 分别量"放得出来"与"蓄力不被打断"。

**② 种子方块用 `Blocks.AIR` 当哨兵，但存档那条路必须跟着改。** 坍缩模式吸什么完全由
`eatable(state)` 决定，`Hole.block` 对它**没有作用**（只有"码放"用得上，而坍缩模式放的是
**原位那一种**方块）⇒ 空手时把 `Hole.block` 记成 AIR 就够。⚠ 但 `loadFrom` 原来是
「block == AIR ⇒ 这个黑洞作废（那个模组被卸了）」，现在必须**只对非坍缩模式**成立，
否则"空手放的洞"一读档就没了。探针 P6 就钉这个：存两条 AIR 洞（一条坍缩、一条普通）⇒ 读回来只剩坍缩那个。

**③ 话也得改一句。** 开火那句是 `message.potato_s_t.gravity.fired`（「它开始吸取 %s 了」），
%s 填副手方块的名字 —— 空手时没有方块可填。上一轮用户说「语言键都不需要改和加（除了显示模式的）」，
但这一轮是**新功能**：硬填"空气/石头"会当场说错"它在吸什么" ⇒ 加**一个**键
`...gravity.fired.everything`（「黑洞成形：它开始吸取周围的一切了」，五语种 691 / lzh 693）。
**这是替用户做的决定，写在这里不藏着**：不想加键的话，把那句改成复用模式名、或者干脆不发消息，都是几行的事。

**④ ⚠⚠ 探针判据的"环境坑"（本轮花时间最多的地方，值得写下来）。**
探针跑在 `ServerStartedEvent` 里，**服务端一 tick 都还没跑**。此时：

  · `isLoaded(pos)` 为真**不代表**那个区块的**实体表**是加载的：`addFreshEntity` 会返回 **true**，
    可实体还挂在 pending 里 —— `getEntitiesOfClass` / `level.getEntities().get(id)` **都看不到它**。
    实测诊断行：「老牛在实体表 false、新牛在实体表 true」「老洞可见生物 0」
    ⇒ 黑洞拉不动、也打不到，B9/B10 假红。（而这两条在**上一轮**是绿的 —— 同一份代码，
    只是那块区块这次的加载状态不同 ⇒ **这种判据本身不稳定**。）
  · 所以两条修法：**凡是要"看到实体"的判据，洞/牛必须放在出生点区块里**（那几块是 START 票，
    实体表一定加载着）；**"两个状态对比"的判据用同一个洞量两次**（先新鲜、跑 600 tick 再量），
    别用"一老一新两个洞"（那要求两块区块都可用，稳定性减半）。
  · `setChunkForced` **救不了**：挂票只是登记，区块状态要等区块源 tick 才会重算 —— 探针里没有 tick。
  `Zf190Check` 按这两条重写后重跑：**16/0**（B7 掉落物销毁也一并挪进了出生点区块）。

**⑤ 语言键只加一个。** 见 ③；其余一个字没动（五份键集合依旧一致）。

"""

ROW = u"""| ZF192 | **新建 `zf192_pre`**（**127 份**改前件：2 份将改源码 + `neoforge.mods.toml` + 五份 lang + 4 份文档 + 6 份脚本 + 前几轮三道门与四个探针 + 旧成品与 `.sha1` + **全部常驻门 104 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf192_*` / §4.192 查过没人占（§4.147）） | **0.14：坍缩模式空手也能放**（用户原话见 §9）。① 三处门一起放行（`use` / `onUseTick` / `fire`），只有坍缩模式不要求副手方块（§4.192①）。② 种子方块用 `Blocks.AIR` 当哨兵 + `loadFrom` 只对**非坍缩**模式把 AIR 当"方块没了"（§4.192②）。③ 空手开火那句话换新键 `gravity.fired.everything`（**替用户做的决定**，五语种 691 / lzh 693，§4.192③）。④ **探针判据的环境坑**：无 tick 的探针里 `addFreshEntity` 返回 true 但实体可能还在 pending ⇒ 实体类判据必须放进**出生点区块**、且"两状态对比"用**同一个洞量两次**（§4.192④）；`Zf190Check` 按此重写后重跑 **16/0**。⑤ **探针 `Zf192Check` 6/0** + 回归 `Zf186Check` 20/0、`Zf188Check` 4/0。⑥ 门 `_zf192_verify.py` **13/0**、反证刀 **9/9**；并**跟平三道老门的判据**（键数 690/692→691/693 与 Zf190 的探针数）。⑦ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.192 |
"""

S9 = u"""### ZF192（0.14）坍缩模式**空手也能放**

- 切到红色那档「**坍缩模式-危险**」之后，**副手空着也能蓄力、也能放**；
  另外两个模式（吞噬 / 牵引）仍然要先在副手放好要吸的那种方块（它们靠"引子"决定吸什么）。
- 空手放出来的洞和放了引子的洞**行为一模一样**：无差别吸方块与生物、销毁掉落物、越吸越猛。
- 空手放时动作栏那句提示改成「**黑洞成形：它开始吸取周围的一切了**」
  （为这一句加了 1 个语言键，五语种都有 —— 原来那句要填"副手方块的名字"，空手时没得填）。
- **实测**（真服务端，6/0）：空手放 ⇒ 扣 4M、装置完好、黑洞出现；那个洞照样搬走 15 格外的石头、
  销毁掉落物；空手**蓄力不会**被中途取消；普通模式空手**依然放不出来**（反面自证）；
  空手的洞**过了存档 / 读档还在**。
- 顺手把上一轮的探针判据重写了（实体类判据挪进出生点区块、同一个洞量两次），重跑 **16/0**。
"""

HAND48 = u"""48. **ZF192 的账（0.14：坍缩模式空手也能放）**：① 用户原话见档案 §9；三处门与 AIR 哨兵见 §4.192①②。
    ② ⚠ **探针判据的环境坑（本轮最贵的一课）**：探针跑在 `ServerStartedEvent`（服务端还没 tick），
    `isLoaded()` 为真**不代表**区块的**实体表**可用 —— `addFreshEntity` 返回 true、实体却还在 pending，
    `getEntitiesOfClass`/`getEntities().get(id)` 都看不到（诊断实测「老牛在实体表 false」）；
    修法：**实体类判据放进出生点区块**（START 票）+ **两状态对比用同一个洞量两次**；
    `setChunkForced` 救不了（要等区块源 tick）。见 §4.192④。
    ③ 探针 `Zf192Check` **6/0**、`Zf190Check`（重写判据后重跑）**16/0**、`Zf186Check` 20/0、`Zf188Check` 4/0；
    门 `_zf192_verify.py` **13/0**、反证刀 **9/9**；跟平 `_zf190_verify.py`（键数 + 探针数）与 `_zf188_verify.py`（键数）。
    ④ ⚠ **加了一个语言键** `gravity.fired.everything`（上轮用户说"别加键"，但空手时原来那句没得填）——
    这是替用户做的决定，已在档案 §4.192③ 与 §9 里写明，想换写法是几行的事。
"""

BIL_ZH = u"""
- **0.14 追加（ZF192）坍缩模式空手也能放**：切到红色那档之后**副手空着也能蓄力、也能放**；
  空手放出来的洞和放了引子的洞行为一样（无差别吸、销毁掉落物、越吸越猛）。
  空手时动作栏那句改成「它开始吸取周围的一切了」（为此加了 1 个语言键，五语种都有）。
"""

BIL_EN = u"""
- **0.14 follow-up (ZF192) - Collapse mode can be fired with an empty offhand:** switch to the red mode
  and you no longer need a block in your offhand to charge and fire it. A seed-less black hole behaves
  exactly like a seeded one (pulls everything, destroys item drops, gets stronger over time). The
  action-bar line now reads "it starts devouring everything around it" (one new translation key, all
  five languages).
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
    if u"### 4.192 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF192 |" not in doc:
        a2 = u"（class 410；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.190 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF190 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF192（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"48. **ZF192 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND48 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    # ── ① `_zf149_verify.py`：哈希/体积靶子 ──
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    if vn == v149:
        if (u'WANT_SHA = u"%s"' % h) in v149:
            print(u"  （_zf149_verify.py 的靶子已经就是这份成品，跳过）")
        else:
            fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    # ── ② `_zf190_verify.py`：键数 690/692 → 691/693；探针数不变（16/0）；jar 内键数 ──
    v190 = read(V190)
    n190 = v190.replace(u'(690, u"坍缩模式-危险")', u'(691, u"坍缩模式-危险")')
    n190 = n190.replace(u'(690, u"Collapse mode - DANGER")', u'(691, u"Collapse mode - DANGER")')
    n190 = n190.replace(u'(692, u"坍縮之式-危")', u'(693, u"坍縮之式-危")')
    n190 = n190.replace(u'(690, u"崩壊モード - 危険")', u'(691, u"崩壊モード - 危険")')
    n190 = n190.replace(u'(690, u"Режим коллапса - ОПАСНО")', u'(691, u"Режим коллапса - ОПАСНО")')
    n190 = n190.replace(u"keys_jar == 690", u"keys_jar == 691")
    n190 = n190.replace(u"u\"B9 五语种各 +1 键（690 / lzh 692）", u"u\"B9 五语种各 +1 键（691 / lzh 693）")
    n190 = n190.replace(u"u\"D2 成品里没有探针类、语言键跟得上（690）", u"u\"D2 成品里没有探针类、语言键跟得上（691）")
    # ── ④ `_zf190_verify.py` 的 A3 跟平：`use()` 里先取一次 mode（ZF192 空手放行要看模式）──
    old_a3 = (u'    check(u"int cost = summonCost(getMode(stack));" in use and u"getEnergy(stack) < cost" in use\n'
              u'          and u"gravityCapacity()" not in use,')
    new_a3 = (u'    # 0.14 ZF192 跟平：`use()` 先取一次 mode（空手放行要看模式）⇒ 判据改成看**意图**\n'
              u'    # （闸门走 summonCost、不直接拿容量当费用），强度没降。\n'
              u'    check(u"summonCost(" in use and u"getEnergy(stack) < cost" in use\n'
              u'          and u"gravityCapacity()" not in use,')
    if old_a3 in n190:
        n190 = n190.replace(old_a3, new_a3, 1)
        print(u"  `_zf190_verify.py`：A3 判据已跟平（闸门看 summonCost 而不是字面量）")
    elif new_a3 in n190:
        print(u"  `_zf190_verify.py`：A3 已经是新判据，跳过")
    else:
        fails.append(u"_zf190_verify.py：A3 锚点找不到（跟平失败）")

    if n190 != v190:
        print(u"  `_zf190_verify.py`：键数判据已跟平（691 / lzh 693）")
        if write and not fails:
            io.open(V190, "w", encoding="utf-8", newline=u"").write(n190)
    elif u'(691, u"坍缩模式-危险")' in v190:
        print(u"  `_zf190_verify.py`：键数已经是 691，跳过")
    else:
        fails.append(u"_zf190_verify.py：键数锚点找不到（跟平失败）")

    # ── ③ `_zf188_verify.py`：键数 690/692 → 691/693 ──
    v188 = read(V188)
    n188 = v188.replace(u'{u"zh_cn.json": 690, u"en_us.json": 690, u"lzh.json": 692,\n'
                        u'                   u"ja_jp.json": 690, u"ru_ru.json": 690}',
                        u'{u"zh_cn.json": 691, u"en_us.json": 691, u"lzh.json": 693,\n'
                        u'                   u"ja_jp.json": 691, u"ru_ru.json": 691}')
    if n188 != v188:
        print(u"  `_zf188_verify.py`：C1 键数已跟平（691 / lzh 693）")
        if write and not fails:
            io.open(V188, "w", encoding="utf-8", newline=u"").write(n188)
    elif u'{u"zh_cn.json": 691' in v188:
        print(u"  `_zf188_verify.py`：键数已经是 691，跳过")
    else:
        fails.append(u"_zf188_verify.py：键数锚点找不到（跟平失败）")

    ann = read(ANN)
    if u"## New in 0.14 ZF192" not in ann:
        a5 = u"## New in 0.14 ZF190 - A flat summon price, and a third mode that eats everything"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF190 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF192 - Collapse mode can be fired with an empty offhand\n\n"
                     u"- The **Collapse mode - DANGER** can now be charged and fired with an **empty\n"
                     u"  offhand**; the other two modes still need a block in your offhand (that block is\n"
                     u"  what decides which blocks they pull).\n"
                     u"- An empty-handed black hole behaves exactly like a seeded one: it pulls every block\n"
                     u"  and mob, destroys item drops and keeps getting stronger.\n"
                     u"- With no seed block the action-bar line now reads \"The black hole forms: it starts\n"
                     u"  devouring everything around it\" (one new translation key, present in all five\n"
                     u"  languages - the old line had to be filled with the offhand block's name).\n"
                     u"- Measured on a real server (6 checks, all green): an empty offhand spends 4M and\n"
                     u"  leaves the device intact with a black hole in front of you; that hole still moves a\n"
                     u"  block 15 blocks away and destroys item drops; charging with an empty offhand is not\n"
                     u"  cancelled mid-way; a normal-mode device with an empty offhand still refuses to\n"
                     u"  fire; and a seed-less black hole survives a save/load round.\n"
                     u"- Also: the previous round's probe had its checks rewritten (entity-based checks now\n"
                     u"  run inside the spawn chunks and compare one and the same black hole at two ages)\n"
                     u"  and re-ran green (16/16).\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加（ZF192）" not in bil:
        az2 = u"  而且**不损坏装置**；任何黑洞活过 **2 分钟**会**真炸一下 30 威力**。⚠ 别在基地里放。\n"
        ae2 = u"  with a real 30-power explosion. Do not use it next to your base.\n"
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
