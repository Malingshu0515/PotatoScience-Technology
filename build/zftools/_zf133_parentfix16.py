# -*- coding: utf-8 -*-
"""_zf133_parentfix16.py —— 补上 `directDamageProbe` 本体（上一次脚本在写盘前就断言失败了）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

ANCHOR = "    private static void checkH() {"
BODY = '''    /**
     * 末地伤害的**直接**取证：反射造一道波 + 当场调 `damageAt` + 当场量血。
     *
     * <p>绕开两个坑：① 末地龙**每 tick 回 1 血**（隔 40 tick 快照看不出掉血，
     * 实测 [HP1] 是 0 个）；② 它**重写了 `hurt()` 不调 `super.hurt()`**
     * ⇒ NeoForge 的 `LivingIncomingDamageEvent` 根本不发（实测监听器 0 次，
     * 而 `hurt(...)` 明明返回 true）。**事件的覆盖范围取决于被观测对象怎么实现** ——
     * 拿它当判据会漏，所以这里改成"当场量血"。</p>
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
            say(TAG + "      [DIRECT] damageAt(" + pos.toShortString() + ")：末影人 "
                    + before + " -> " + after + "（掉 " + lost + "）");
            failed += check("直接结算：末影人掉 12.0 = 10 + 0.5 × 4（实际 " + lost + "）",
                    Math.abs(lost - 12.0D) < 0.01D);

            float b2 = victim.getHealth();
            m.invoke(null, wave, owner, pos);
            say(TAG + "      [DIRECT] 同一格再来一次：末影人 " + b2 + " -> " + victim.getHealth());
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

'''

s = io.open(CHK, encoding="utf-8").read()
assert s.count(ANCHOR) == 1, "锚点 %d 次" % s.count(ANCHOR)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, BODY + ANCHOR, 1))
print("[OK] directDamageProbe 已补上")
