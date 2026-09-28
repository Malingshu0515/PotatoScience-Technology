# -*- coding: utf-8 -*-
r"""ZF153 侦察②：把"实现要照抄的那几段"逐字打出来（只读）。

第一版侦察漏了三处（needle 写错 / 只打了签名没打实现），这三处正好都是
"写错就悄悄错"的地方：

  ① `SwordItem.createAttributes` 与 `Item.createAttributes` 的**算式**
     —— 用户给的「24点伤害 1.4攻击速度」是显示总值，参数得反推；不看清算式就会写错 1 点。
  ② `MobEffectEvent.Applicable` 的 `Result` 枚举 + 它在 `LivingEntity.addEffect`
     里的**触发点** —— 决定"免疫"是挂在源头还是每 tick 抹（也决定探针怎么验）。
  ③ 原版**爆炸的击飞写法**（`setDeltaMovement` + `hurtMarked`）——
     「击飞」必须是服务端能同步到客户端的那种推法，自己拍一个 vec3 客户端会看见橡皮筋。
"""

import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")

OUT = []


def w(line=u""):
    OUT.append(line)


def flush():
    text = u"\n".join(OUT) + u"\n"
    with io.open(os.path.join(ZFTOOLS, "_zf153_recon2.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write(u"[zf153_recon2] 写出 %d 行 -> _zf153_recon2.txt\n" % len(OUT))


def src_of(zf, want):
    hit = [n for n in zf.namelist() if n.endswith(want)]
    return zf.read(hit[0]).decode("utf-8", "replace") if hit else None


def show(src, label, lo, hi):
    w(u"")
    w(u"---- %s（第 %d~%d 行）----" % (label, lo, hi))
    lines = src.split(u"\n")
    for i in range(lo, min(hi, len(lines)) + 1):
        w(u"  %5d | %s" % (i, lines[i - 1].rstrip()))


def find_all(src, needle, limit=12):
    return [i for i, line in enumerate(src.split(u"\n"), 1) if needle in line][:limit]


with zipfile.ZipFile(SOURCES_JAR) as zf:
    # ① 剑的属性算式
    s = src_of(zf, u"net/minecraft/world/item/SwordItem.java")
    show(s, u"SwordItem.java 全部 createAttributes", 30, 60)
    s2 = src_of(zf, u"net/minecraft/world/item/Item.java")
    w(u"")
    w(u"---- Item.java 里 createAttributes 的出现行号：%s ----" % find_all(s2, u"createAttributes"))
    for lo in find_all(s2, u"createAttributes"):
        show(s2, u"Item.java @%d" % lo, lo - 2, lo + 16)
    s3 = src_of(zf, u"net/minecraft/world/item/Items.java")
    w(u"")
    w(u"---- Items.java：netherite_sword 那一段 ----")
    lo = find_all(s3, u'"netherite_sword"')[0]
    show(s3, u"Items.java netherite_sword", lo - 2, lo + 4)
    t = src_of(zf, u"net/minecraft/world/item/Tiers.java")
    w(u"")
    w(u"---- Tiers.java：六档的 (耐久, 速度, 伤害加成, 附魔权重, 标签) ----")
    for i, line in enumerate(t.split(u"\n"), 1):
        if u"new Tier(" in line or u"int diamondLevel" in line or u"int netheriteLevel" in line:
            w(u"  %5d | %s" % (i, line.strip()))

    # ② 效果"能不能挂上"的事件与触发点
    s = src_of(zf, u"net/neoforged/neoforge/event/entity/living/MobEffectEvent.java")
    show(s, u"MobEffectEvent.Result 枚举", 144, 178)
    w(u"")
    w(u"---- MobEffectEvent.java 里 Applicable 的出现行号：%s ----" % find_all(s, u"Applicable"))
    s = src_of(zf, u"net/minecraft/world/entity/LivingEntity.java")
    w(u"")
    w(u"---- LivingEntity.java 里 Applicable 的出现行号：%s ----" % find_all(s, u"Applicable"))
    for lo in find_all(s, u"Applicable"):
        show(s, u"LivingEntity.java @%d" % lo, lo - 18, lo + 12)
    w(u"")
    w(u"---- LivingEntity.java：canBeAffected ----")
    for lo in find_all(s, u"canBeAffected"):
        show(s, u"LivingEntity.canBeAffected @%d" % lo, lo - 4, lo + 14)

    # ③ 原版爆炸的击飞写法
    s = src_of(zf, u"net/minecraft/world/level/Explosion.java")
    w(u"")
    w(u"---- Explosion.java 里 setDeltaMovement / hurtMarked 的出现行号：%s"
      % (find_all(s, u"setDeltaMovement") + find_all(s, u"hurtMarked")))
    for lo in find_all(s, u"setDeltaMovement") + find_all(s, u"hurtMarked"):
        show(s, u"Explosion.java @%d" % lo, max(1, lo - 14), lo + 6)

    # ④ 顺手：SwordItem 的 postHurtEnemy（剑的攻击磨损挂点，确认签名没变）
    s = src_of(zf, u"net/minecraft/world/item/SwordItem.java")
    w(u"")
    w(u"---- SwordItem.java：postHurtEnemy / getEnchantmentValue ----")
    for lo in find_all(s, u"postHurtEnemy") + find_all(s, u"getEnchantmentValue"):
        show(s, u"SwordItem.java @%d" % lo, lo - 3, lo + 10)

flush()
