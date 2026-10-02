# -*- coding: utf-8 -*-
u"""_zf182_docs.py —— ZF182 文档落笔（§4.182 + §5 行 + §9 段 + 交接第 43 条 + 英文公告）+ 哈希跟平。

主题：振金剑「斩首」被动（口径 B：只有猛砸技能击杀才算）。版本线 **0.14**。

跑法：python build\\zftools\\_zf182_docs.py [--write]
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
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.182 【事件雷】「被某某击杀」别靠猜 —— 给技能一个**自己的伤害类型**（0.14 ZF182）

用户原话：「**给振金剑加个新被动buff 被振金剑技能击杀的生物掉落它的头颅 玩家掉落本人头颅 原版有头颅的
掉落自己的头颅 没有的则不掉**」；"斩首怎么算"我给了两个口径，用户选了 **B = 只有猛砸技能击杀才算**。

**坑在哪**：猛砸（`VibraniumSwordItem.slam`）原来用的是原版 `player.damageSources().playerAttack(player)`
—— 于是"这一下是技能打的"和"玩家平砍"在**伤害源上完全一样**，靠它根本分不出来。常见的三种将就写法都不好：

| 将就写法 | 为什么不行 |
|---|---|
| 判"凶手手里是不是拿着振金剑" | 那是**口径 A**；用户要 B ⇒ 平砍也会掉头 |
| 记一个"最近放过技能"的时间窗 | 时间窗内平砍也算，边界全是玄学 |
| 给生物挂一个标记（NBT/attachment） | 得自己清理、还得处理跨存档，越写越脏 |

**正解**：给技能**自己的伤害类型**。本工程早就有这条路（星璨钢剑气 `potato_s_t:star_steel_slash`、
振金反伤 `potato_s_t:vibranium_reflect`）⇒ 照抄第三条 `potato_s_t:vibranium_slam`：
`ResourceKey<DamageType>` 常量 + `data/potato_s_t/damage_type/vibranium_slam.json` +
`slamSource(player)`（**仍以玩家为来源实体**，所以掉落/经验/进度照常算玩家的），
斩首处理器只认 `source.is(VIBRANIUM_SLAM)` —— 判据从"猜"变成"读"。

**顺带的两条**：① 掉落走 `LivingDropsEvent`（`getDrops().add(new ItemEntity(...))`），
玩家头颅用 `player_head` + `DataComponents.PROFILE` = **被杀者本人**的 `GameProfile`
（1.21.1 是**构造器** `new ResolvableProfile(GameProfile)`，没有 `createResolved(...)`，编译期抓出来的）；
② **别给没有头颅物品的生物编头颅** —— 尸壳/溺尸/流浪者这些原版没有头，用户口径是"没有的则不掉"。

"""

ROW = u"""| ZF182 | **无新备份根**（改 `VibraniumSwordItem` + 新增 `VibraniumBeheading` + 1 份 damage_type JSON + 五语各 +2 键 + 门/探针；⚠ 轮号 `_zf182_*` 开工前查过没人占（§4.147）） | **0.14：振金剑「斩首」被动（口径 B）**（用户原话见 §9；口径二选一里用户选 B）。① **判据链**（§4.182）：新增自定义伤害类型 **`potato_s_t:vibranium_slam`**，**猛砸那一下的伤害改用它** ⇒ 斩首处理器只认 `source.is(VIBRANIUM_SLAM)`，**平砍（原版 player_attack）自然被排除**；伤害源仍以玩家为来源实体 ⇒ 掉落/经验/进度照常算玩家的。② **掉什么**：僵尸→僵尸头、骷髅→骷髅头、凋灵骷髅→凋灵骷髅头、苦力怕→苦力怕头、猪灵→猪灵头、末影龙→龙首；**玩家→本人头颅**（`player_head` + 被杀者自己的 `GameProfile`，1.21.1 用构造器 `new ResolvableProfile(...)`）；**表里没有的一律不掉**（不给尸壳/溺尸编不存在的头颅）。③ **文案**：振金剑 tooltip 3 → **4 行**（第 4 行 = 斩首说明）+ 死亡文案 `death.attack.potato_s_t.vibranium_slam`，五语各 +2 键（**653 → 655**，lzh 655 → 657）。④ **真服务端探针 `Zf182Check` 13/0**：真调 `slam()` 砸死僵尸/骷髅/苦力怕 ⇒ 掉落里各有自己的头颅；玩家受害者 ⇒ `player_head` 且 PROFILE 是**被杀者本人**；负对照：牛被砸死**不掉**、同一个持剑玩家**平砍**打死僵尸**不掉**。⑤ 门 `_zf182_verify.py` **19/0**、反证刀 **5/5**。⑥ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.182 |
"""

S9 = u"""### ZF182（0.14）振金剑「斩首」被动（口径 B = 只有猛砸技能击杀）—— **待你实测**

你选的是 **B 计划**：**只有猛砸（Shift+右键）那一下砸死的才算**，平砍不算。

**怎么做到"分得清技能与平砍"**：给猛砸配了**它自己的伤害类型** `potato_s_t:vibranium_slam`
（本工程第三条自定义伤害类型，前两条是星璨钢剑气与振金反伤）—— 猛砸的伤害换成它之后，
斩首处理器只认这个类型，平砍（原版 `player_attack`）自然被排除。伤害源仍以**玩家**为来源实体，
所以掉落/经验/进度照常算玩家的。

**掉什么**：僵尸→僵尸头、骷髅→骷髅头、凋灵骷髅→凋灵骷髅头、苦力怕→苦力怕头、猪灵→猪灵头、末影龙→龙首；
**玩家→本人头颅**（头颅上就是他的皮肤，因为我们把被杀者自己的 profile 写进去了）；
**没有头颅物品的生物（牛/猪/蜘蛛/尸壳/溺尸…）不掉** —— 没给它们编不存在的头颅。

**实测（真服务端，13/0）**：真调那个猛砸技能砸死僵尸/骷髅/苦力怕 ⇒ 掉落里各有自己的头颅；
玩家受害者 ⇒ `player_head` + 本人 profile；**负对照**：牛被砸死**不掉**、同一个持剑玩家**平砍**打死僵尸**不掉**。

**要你实测**：拿振金剑 Shift+右键猛砸 —— 砸死上表这几种生物应该掉头；**PVP 砸死玩家**掉他本人的头；
平常平砍、以及砸牛这类，都不掉。
"""

HAND43 = u"""43. **ZF182 的账（0.14：振金剑斩首被动，口径 B）**：① 用户原话与口径选择见档案 §9；**判据链**见 §4.182 ——
    给猛砸配**自己的伤害类型** `potato_s_t:vibranium_slam`（第三条自定义类型），斩首处理器只认
    `source.is(VIBRANIUM_SLAM)` ⇒ 平砍自然不算（**别用"手里拿着剑"或时间窗那种将就写法**）。
    ② 掉落：僵尸/骷髅/凋灵骷髅/苦力怕/猪灵/末影龙 → 各自头颅；玩家 → `player_head` + **被杀者本人**
    的 profile（1.21.1 是构造器 `new ResolvableProfile(GameProfile)`，**没有** `createResolved`）；
    没有头颅物品的生物不掉。③ tooltip 3 → 4 行 + 死亡文案，五语各 +2 键（653→655，lzh 655→657）。
    ④ 探针 `Zf182Check` **13/0**（真技能 + 负对照：牛不掉 / 平砍不掉）；门 `_zf182_verify.py` **19/0**、反证刀 **5/5**。
    ⑤ ⚠ FakePlayer **砸不动**（`invulnerable=false` 也 `hits=0`）⇒ 探针里"玩家那条路"改用 `headFor()` 直接验
    （与生物共用同一条代码路径，玩家特有的只有 PROFILE 那一步），这一条**如实记着**，别写成"也实测了"。
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
        print(u"!! 成品不在：%s" % JAR)
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"成品 %s：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d"
          % (os.path.basename(JAR), size, h, cls, recipes, keys_zh, keys_lzh))
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
        return text

    doc = read(DOC)
    if u"### 4.182 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF182 |" not in doc:
        a2 = u"（阶段一改文件、阶段二读新成品跟平文档）。 | 见 §9 ｜ 见 §4.150 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF181 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = (ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h)
                   .replace(u"{cls}", str(cls)))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF182（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"43. **ZF182 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND43 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = v149
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, vn, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == v149:
        fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.14 ZF182" not in ann:
        a5 = u"## New in 0.14 ZF181 - The version line is now 0.14"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF181 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF182 - Beheading: the vibranium sword takes heads\n\n"
                     u"- **New passive on the Vibranium Sword: Beheading.** Mobs you kill with the\n"
                     u"  sword's ground slam (sneak + right-click) drop **their own head** - zombie head,\n"
                     u"  skeleton skull, wither skeleton skull, creeper head, piglin head, dragon head.\n"
                     u"- **Players drop their own head**, skin included: the victim's profile is written\n"
                     u"  into the head item.\n"
                     u"- **Only the slam counts** (the option you picked): ordinary swings do not take\n"
                     u"  heads. This is enforced by giving the slam **its own damage type**\n"
                     u"  (`potato_s_t:vibranium_slam`) instead of guessing.\n"
                     u"- Mobs that have no head item in vanilla (cows, pigs, spiders, husks, drowned...)\n"
                     u"  drop nothing extra.\n"
                     u"- Verified on a real server with the real skill: zombie / skeleton / creeper killed\n"
                     u"  by the slam drop their own heads, a player victim's head carries the victim's own\n"
                     u"  profile, and two negative controls hold (a cow drops no head; a plain swing takes\n"
                     u"  no head). 13/0.\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
