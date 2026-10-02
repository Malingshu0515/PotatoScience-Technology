# -*- coding: utf-8 -*-
"""_zf133_parentfix14.py —— 末地伤害改成**直接调用 + 当场量血**（绕开再生与事件两件事）

两个坑一起绕开：
  ① **末地龙每 tick 回 1 血** ⇒ 隔 40 tick 再快照，"掉 12"早被回满了（[HP1] 0 个就是因为这个）；
  ② **末地龙重写 `hurt()` 不调 `super.hurt()`** ⇒ NeoForge 的 `LivingIncomingDamageEvent` 不发。

做法（判据更硬，不是更松）：
  · 用探针**反射**造一个 `ShockwaveManager.Wave`（同一个末地维度、同一个发射者、n = 4），
  · 直接调私有的 `damageAt(wave, owner, pos)`，**当场**量目标实体的血量变化；
  · 目标用一只普通生物（`EnderMan` 已经在那儿，血量 40）⇒ 12 点伤害看得见、也没再生。
  · 这不依赖"波能推多远""事件发不发""谁先挨打"，验的就是**那一格结算的公式**。

跑法：python build\\zftools\\_zf133_parentfix14.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """    private static void checkH() {"""
NEW = """    /**
     * 末地伤害的**直接**取证：反射造一道波 + 当场调 `damageAt` + 当场量血。
     *
     * <p>绕开两个坑：末地龙**每 tick 回 1 血**（隔 40 tick 快照看不出掉血）、
     * 并且它**重写了 `hurt()` 不调 `super.hurt()`**（NeoForge 的伤害事件不发）。</p>
     */
    private static void directDamageProbe(ServerPlayer owner, EnderMan victim, BlockPos pos) {
        try {
            Class<?> waveClass = Class.forName("com.potatost.mod.ShockwaveManager$Wave");
            var ctor = waveClass.getDeclaredConstructor(
                    net.minecraft.server.level.ServerLevel.class, java.util.UUID.class,
                    double.class, boolean.class, int.class, int.class);
            ctor.setAccessible(true);
            Object wave = ctor.newInstance(end, owner.getUUID(),
                    ShockwaveManager.baseAttackDamage(owner), true, 1, pos.getY());
            var m = ShockwaveManager.class.getDeclaredMethod("damageAt", waveClass,
                    ServerPlayer.class, BlockPos.class);
            m.setAccessible(true);

            float before = victim.getHealth();
            m.invoke(null, wave, owner, pos);
            float after = victim.getHealth();
            double lost = before - after;
            say(TAG + "      [DIRECT] 直接调 damageAt(" + pos.toShortString() + ")：末影人 "
                    + before + " -> " + after + "（掉 " + lost + "）");
            failed += check("直接结算：末影人掉 12.0 = 10 + 0.5 × 4（实际 " + lost + "）",
                    Math.abs(lost - 12.0D) < 0.01D);

            float b2 = victim.getHealth();
            m.invoke(null, wave, owner, pos);
            say(TAG + "      [DIRECT] 再来一次：末影人 " + b2 + " -> " + victim.getHealth());
            failed += check("同一格连续两次只掉一次（原版无敌帧生效）",
                    Math.abs(b2 - victim.getHealth()) < 0.01F);
        } catch (Throwable t) {
            say(TAG + "      [DIRECT] 反射调用失败：" + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\\n")) {
                say(TAG + "        " + line);
            }
            failed += check("直接结算那一刀", false);
        }
    }

    private static void checkH() {"""

CALL_OLD = """        EnderMan ender = new net.minecraft.world.entity.monster.EnderMan("""
CALL_NEW = """        // ⚠ 末地龙会先挨打（它在采样带上盘旋），所以下面这发**直接结算**用末影人当靶子
        EnderMan ender = new net.minecraft.world.entity.monster.EnderMan("""

AFTER_OLD = """        failed += check("末影人已就位（血量 " + ender.getHealth() + "）", ender.isAlive());"""
AFTER_NEW = """        failed += check("末影人已就位（血量 " + ender.getHealth() + "）", ender.isAlive());
        directDamageProbe(endPlayer, ender, new BlockPos(0, 100, 12));"""

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(OLD, NEW), (CALL_OLD, CALL_NEW), (AFTER_OLD, AFTER_NEW)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))

# 旧的"量血量快照"两条断言换成"记录"（它们证明不了东西，原因已写在注释里）
s = s.replace("""        failed += check("末地有实体被这一刀打到（掉血实体 " + hits + " 个）", hits > 0);
        failed += check("其中有一个**正好掉 12.0** = 10 + 0.5 × 4（实际 "
                + (exact < 0 ? "没有" : exact) + "）", exact > 0.0D);""",
"""        // 快照法**说明不了问题**：末地龙每 tick 回 1 血，隔 40 tick 早回满（实测 0 个掉血）。
        // 真正的判据在 directDamageProbe() 里（当场量）。这里只留记录。
        say(TAG + "      [HP1-记录] 快照法看到掉血实体 " + hits + " 个（末地龙会再生 ⇒ 不可靠）");""", 1)

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
