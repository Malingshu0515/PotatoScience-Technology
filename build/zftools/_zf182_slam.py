# -*- coding: utf-8 -*-
u"""_zf182_slam.py —— ZF182（0.14）「振金剑斩首被动」按**口径 B** 落地（用户选 B：只有猛砸技能击杀才算）。

一次做完四件事：
  ① `VibraniumSwordItem`：加自定义伤害类型 `potato_s_t:vibranium_slam` 与 `slamSource(player)`，
     猛砸那一下的伤害改用它 ⇒ 「是不是技能杀的」变成一条**可判定的判据**；tooltip 行数 3 → 4；
  ② 新数据包条目 `data/potato_s_t/damage_type/vibranium_slam.json`（照 `star_steel_slash.json` 换 id）；
  ③ `VibraniumBeheading`：触发判据从「手里拿着剑」改成 `source.is(VIBRANIUM_SLAM)`；
  ④ 五语补两个键：tooltip 第 4 行（斩首说明）+ 死亡文案 `death.attack.potato_s_t.vibranium_slam`。

跑法：python build\\zftools\\_zf182_slam.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
DTYPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\damage_type")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
TIP = u"tooltip.potato_s_t.vibranium_sword.4"
DEATH = u"death.attack.potato_s_t.vibranium_slam"

JAVA_CONST = u"""    /**
     * 猛砸技能的伤害类型（0.14 ZF182）：**斩首被动只认它**。
     *
     * <p>用户对「斩首怎么算」选了 **B 口径 = 只有技能（猛砸）击杀才算** ⇒ 平砍不掉头颅。
     * 把猛砸的伤害换成我们自己的数据包条目之后，「是不是技能杀的」就成了一条**可判定的判据**
     * （{@code source.is(VIBRANIUM_SLAM)}），不用去猜时间窗、也不用挂标记。</p>
     */
    public static final ResourceKey<DamageType> VIBRANIUM_SLAM = ResourceKey.create(
            Registries.DAMAGE_TYPE,
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_slam"));

    /**
     * 猛砸的伤害来源：**以玩家为来源实体** ⇒ 击杀照常算玩家的（掉落 / 经验 / 进度都走原版那条路），
     * 但伤害类型是我们自己的条目（换文案，同时给斩首被动当判据）。
     *
     * <p>⚠ {@code getHolderOrThrow} 在「数据包缺了这个伤害类型」时会抛 —— 那正是要的行为：
     * 宁可当场炸出来，也不要静默退回一个通用伤害类型（与星璨钢剑气同一条口径）。</p>
     */
    public static DamageSource slamSource(ServerPlayer player) {
        Holder<DamageType> type = player.level().registryAccess()
                .registryOrThrow(Registries.DAMAGE_TYPE)
                .getHolderOrThrow(VIBRANIUM_SLAM);
        return new DamageSource(type, player);
    }

    public static int slam(ServerPlayer player) {"""

BEHEAD_OLD = (u"        if (!(event.getSource().getEntity() instanceof Player killer)\n"
              u"                || !VibraniumSwordItem.isHolding(killer)) {\n"
              u"            return;\n"
              u"        }")
BEHEAD_NEW = (u"        // 用户对「斩首怎么算」选了 **B 口径：只有猛砸技能（Shift+右键）击杀才算** ⇒ 平砍不掉。\n"
              u"        // 判据是**伤害类型**（见 VibraniumSwordItem.VIBRANIUM_SLAM），不是「手里拿着剑」。\n"
              u"        if (!event.getSource().is(VibraniumSwordItem.VIBRANIUM_SLAM)) {\n"
              u"            return;\n"
              u"        }")

TIP_V = {
    u"zh_cn": u"被动·斩首：被猛砸（Shift+右键）击杀的生物会掉落它的头颅（玩家掉落本人头颅）",
    u"en_us": u"Passive - Beheading: mobs you kill with the ground slam (sneak + right-click) drop "
              u"their own head (players drop their own head)",
    u"ja_jp": u"パッシブ・斬首：地面叩きつけ（スニーク＋右クリック）で倒した Mob は自分の頭を落とす",
    u"ru_ru": u"Пассивно — Обезглавливание: убитые ударом о землю (присесть + правый клик) роняют свою голову",
    u"lzh": u"被動·斬首：以猛砸（潛行右擊）斃之者，墮其首（人則墮己首）",
}
DEATH_V = {
    u"zh_cn": u"%1$s 被 %2$s 一记猛砸砸碎了",
    u"en_us": u"%1$s was smashed into the ground by %2$s",
    u"ja_jp": u"%1$s は %2$s に叩き潰された",
    u"ru_ru": u"%1$s был раздавлен %2$s",
    u"lzh": u"%1$s 為 %2$s 所砸斃",
}


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def patch(path, pairs, write):
    text = read(path)
    before = text
    for a, b in pairs:
        if a not in text:
            print(u"  !! %s：找不到锚点 → %s" % (os.path.basename(path), a[:56]))
            return False
        text = text.replace(a, b, 1)
    n = sum(1 for l1, l2 in zip(before.split(u"\n"), text.split(u"\n")) if l1 != l2)
    print(u"  %-28s 改 %d 行" % (os.path.basename(path), n))
    if write:
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
    return True


def main(argv):
    write = u"--write" in argv
    ok = True
    ok &= patch(os.path.join(JAVA, u"VibraniumSwordItem.java"), [
        (u"import net.minecraft.core.Holder;",
         u"import net.minecraft.core.Holder;\nimport net.minecraft.core.registries.Registries;"),
        (u"import net.minecraft.network.chat.Component;",
         u"import net.minecraft.network.chat.Component;\n"
         u"import net.minecraft.resources.ResourceKey;\n"
         u"import net.minecraft.resources.ResourceLocation;"),
        (u"import net.minecraft.world.damagesource.DamageSource;",
         u"import net.minecraft.world.damagesource.DamageSource;\n"
         u"import net.minecraft.world.damagesource.DamageType;"),
        (u"    public static int slam(ServerPlayer player) {", JAVA_CONST),
        (u"        DamageSource source = level.damageSources().playerAttack(player);",
         u"        // 0.14 ZF182：猛砸改用我们自己的伤害类型 ⇒ 斩首被动（口径 B）据此判定「技能击杀」\n"
         u"        DamageSource source = slamSource(player);"),
        (u"    private static final int TOOLTIP_LINES = 3;",
         u"    /** 0.14 ZF182：斩首被动多一行说明（3 → 4）。 */\n"
         u"    private static final int TOOLTIP_LINES = 4;"),
    ], write)

    ok &= patch(os.path.join(JAVA, u"VibraniumBeheading.java"), [(BEHEAD_OLD, BEHEAD_NEW)], write)

    src = os.path.join(DTYPE, u"star_steel_slash.json")
    dst = os.path.join(DTYPE, u"vibranium_slam.json")
    if not os.path.isfile(dst):
        text = read(src).replace(u"potato_s_t.star_steel_slash", u"potato_s_t.vibranium_slam")
        print(u"  新建 vibranium_slam.json")
        if write:
            io.open(dst, "w", encoding="utf-8", newline=u"\n").write(text)
    else:
        print(u"  vibranium_slam.json 已存在")

    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = read(p)
        before = json.loads(text)
        add = []
        if TIP not in before:
            add.append((TIP, TIP_V[loc]))
        if DEATH not in before:
            add.append((DEATH, DEATH_V[loc]))
        if not add:
            print(u"  %s：两键都在" % loc)
            continue
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(eol)
        idx = next((i for i, ln in enumerate(lines)
                    if ln.strip().startswith(u'"tooltip.potato_s_t.vibranium_sword.3"')), None)
        if idx is None:
            print(u"  !! %s：找不到 tooltip .3 锚点" % loc)
            ok = False
            continue
        ind = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
        ins = [ind + u'"%s": %s,' % (k, json.dumps(v, ensure_ascii=False)) for k, v in add]
        lines = lines[:idx + 1] + ins + lines[idx + 1:]
        new_text = eol.join(lines)
        parsed = json.loads(new_text)
        if len(parsed) != len(before) + len(add):
            print(u"  !! %s：键数对不上" % loc)
            ok = False
            continue
        print(u"  %s：+%d 键（%d → %d）" % (loc, len(add), len(before), len(parsed)))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(new_text)
    print(u"模式：%s ｜ 结果：%s" % (u"落盘" if write else u"干跑", u"OK" if ok else u"有错"))
    return 0 if ok else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
