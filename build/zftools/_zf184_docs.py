# -*- coding: utf-8 -*-
u"""_zf184_docs.py —— ZF184 文档落笔（§4.184 + §5 行 + §9 段 + 交接第 44 条 + 英文公告）+ 哈希跟平。

主题：猛砸伤害 = 玩家**当前**攻击伤害（含手持武器）+ **逐目标**附魔加成。版本线 0.14。
跑法：python build\\zftools\\_zf184_docs.py [--write]
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

S4 = u"""### 4.184 【数值雷】技能伤害该走**属性值**、附魔要**逐目标**算（0.14 ZF184）

用户原话：「**振金剑技能伤害n改一下 改成目前玩家的伤害（之前是基础伤害 不包括手持武器）
并且吃附魔例如亡灵杀手 锋利的加成 语言键不需要改**」。两件事，各有一个坑：

**① 基数要用属性值，不要用"基础攻击伤害"。** 猛砸原来写的是
`ShockwaveManager.baseAttackDamage(player)`（属性**基础值** + 玩家自身加成，**故意不含手持武器**）——
于是"换一把更好的剑"对技能毫无影响。改成 `player.getAttributeValue(Attributes.ATTACK_DAMAGE)`
（= 基础 + 玩家加成 + **手持武器那一份**）才对得上玩家面板上的那个数。

**② 附魔伤害不在 `LivingEntity.hurt` 里结算，得自己调。** 1.21 把锋利/亡灵杀手做成了
`EnchantmentEffectComponents.DAMAGE` 效果，由 `EnchantmentHelper.modifyDamage(level, 武器, 目标, 伤害源, 伤害)`
结算 —— 而它**只在原版玩家攻击那条路上被调用**（实测：`ServerPlayer.java:2163`、`Mob.java:1495`、
`AbstractArrow.java:360`、`ThrownTrident.java:120`）。我们的技能是直接 `target.hurt(source, damage)`，
**不经过那条路** ⇒ 必须自己调一次，否则"技能不吃附魔"。

**③ 而且必须写在循环里。** 亡灵杀手看**目标类型**：对僵尸加、对牛不加。原来 `damage` 在循环外只算一次，
搬过去就会变成"对谁都按第一个目标的类型算"。现在 `modifyDamage` 在 `for` 里逐目标调用。

**取证**（`Zf184Check`，6/0，量的是**血量差**不是公式）：空手 12.79 → **+9 攻击力 21.65**（基数跟着属性走）；
亡灵杀手 V 打僵尸 **25.09**、打牛 **13.0（=无附魔）**；锋利 V 打牛 **16.0**。
⚠ 假玩家（`FakePlayer`）**不 tick**，`detectEquipmentUpdates()` 是 private ⇒ 手里拿剑属性表也不会变，
所以"手持武器"那条用"手动 +9 攻击力"来验判据本身（详见探针里 `attackBonus` 的注释）。

"""

ROW = u"""| ZF184 | **无新备份根**（改 `VibraniumSwordItem` 一处 + 门/探针脚本 + 文档；⚠ 轮号 `_zf184_*` 查过没人占（§4.147）） | **0.14：猛砸伤害 = 玩家当前攻击伤害 + 逐目标附魔加成**（用户原话见 §9；**语言键不动**）。① 基数从 `ShockwaveManager.baseAttackDamage(player)`（**不含**手持武器）改成 `player.getAttributeValue(Attributes.ATTACK_DAMAGE)`（含手持武器）——§4.184①；② 附魔加成自己调 `EnchantmentHelper.modifyDamage(level, 主手, 目标, 伤害源, 伤害)`（原版只在玩家攻击那条路调，我们直接 `hurt` 不经过）——§4.184②；③ **挪进循环里逐目标算**（亡灵杀手看目标类型）——§4.184③。④ **真服务端探针 `Zf184Check` 6/0**（血量差实测）：空手 12.79 → +9 攻击力 21.65；亡灵杀手 V 打僵尸 25.09 / 打牛 13.0（=无附魔）；锋利 V 打牛 16.0。⑤ 门 `_zf184_verify.py` **9/0**、反证刀 **3/3**。⑥ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.184 |
"""

S9 = u"""### ZF184（0.14）猛砸伤害改成「玩家当前攻击伤害 + 吃附魔」—— **待你实测**

按你原话改的两件事：**① 基数**从"玩家基础伤害（不含手持武器）"换成**玩家当前攻击伤害**（属性值，含手持武器那一份）；
**② skill 现在吃附魔**（锋利、亡灵杀手这类），而且是**逐目标**算的 —— 亡灵杀手只对亡灵加、对别的生物不加。语言键没动。

**实测（真服务端，量的是一击打掉的血）**：空手 12.79 → **+9 攻击力 21.65**（基数确实跟着属性走）；
**亡灵杀手 V 打僵尸 25.09**、同一把剑**打牛 13.0**（与无附魔一模一样 ⇒ 逐目标算对了）；
**锋利 V 打牛 16.0**（通吃附魔也生效）。

**要你实测**：拿一把**带锋利/亡灵杀手**的振金剑 Shift+右键猛砸 —— 打亡灵（僵尸/骷髅/凋灵）应当明显更疼，
打普通生物吃锋利；再把主手换成更好的武器或加攻击力 buff，猛砸应当跟着变疼。
"""

HAND44 = u"""44. **ZF184 的账（0.14：猛砸伤害吃"当前攻击伤害 + 附魔"）**：① 用户原话见档案 §9；两处坑见 §4.184 ——
    **基数要用 `getAttributeValue(ATTACK_DAMAGE)`**（`baseAttackDamage` 故意不含手持武器）、
    **附魔伤害要自己调 `EnchantmentHelper.modifyDamage`**（1.21 只在玩家攻击那条路结算：`ServerPlayer.java:2163` 等四处），
    而且**必须逐目标写在循环里**（亡灵杀手看目标类型）。② 探针 `Zf184Check` **6/0**（血量差实测：+9 攻击力 → +8.9 伤害；
    亡灵杀手对僵尸 25.09 / 对牛 13.0；锋利对牛 16.0）；门 `_zf184_verify.py` **9/0**、反证刀 **3/3**。
    ③ ⚠ 假玩家 `FakePlayer` **不 tick**（`detectEquipmentUpdates()` 是 private）⇒ 手里拿剑属性表也不变，
    "手持武器"那条用**手动 +9 攻击力**验判据本身，别写成"手持武器也实测了"。④ 语言键**没动**（用户明说不用改）。
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
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d" % (size, h, cls, recipes, keys_zh, keys_lzh))
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
        text = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        return text

    doc = read(DOC)
    if u"### 4.184 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF184 |" not in doc:
        a2 = u"（阶段一改文件、阶段二读新成品跟平文档）。 | 见 §9 ｜ 见 §4.150 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF181 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = (ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls)))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF184（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"44. **ZF184 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND44 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    if vn == v149:
        fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.14 ZF184" not in ann:
        a5 = u"## New in 0.14 ZF182 - Beheading: the vibranium sword takes heads"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF182 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF184 - The ground slam now scales with your real attack damage\n\n"
                     u"- **The vibranium sword's ground slam now uses your current attack damage** (the\n"
                     u"  attribute value, which already includes the weapon in your hand) instead of the\n"
                     u"  bare base value that ignored the weapon.\n"
                     u"- **The slam also benefits from enchantments now** - Sharpness, Smite and friends -\n"
                     u"  and it is applied **per target**, so Smite hurts the undead and leaves everything\n"
                     u"  else alone.\n"
                     u"- Measured on a real server (health delta, not a formula): bare hand 12.79 -> +9\n"
                     u"  attack damage 21.65; Smite V 25.09 on a zombie but 13.0 on a cow (same as no\n"
                     u"  enchantment); Sharpness V 16.0 on a cow.\n"
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
