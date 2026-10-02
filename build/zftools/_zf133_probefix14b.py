# -*- coding: utf-8 -*-
"""_zf133_probefix14b.py —— 同样的三处补丁，锚点按盘上实际文本（缩进是 8 空格不是 12）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

NEW_ARENA = """        ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）

        // ⚠⚠ 试验场必须**没有怪物**：平台铺在 y=159、厚度只有 1 格，台子下面是黑的 ⇒
        //   苦力怕/僵尸/骷髅在台子下面刷出来，爆炸会波及站在台面上的假玩家
        //   （受击记录：`[DEATH] zf133probe 死于 explosion.player ... blown up by Creeper`），
        //   连带把摆好的测试方块炸飞 —— (e) 那格木头"没被拆掉"的真因就是它先被炸掉了。
        //   和平难度不刷敌对生物；已存在的另用 discard() 清一遍（和平只对之后的刷怪生效）。
        level.getServer().setDifficulty(net.minecraft.world.Difficulty.PEACEFUL, true);
        int mobsCleared = 0;
        for (net.minecraft.world.entity.monster.Enemy mob : level.getEntitiesOfClass(
                net.minecraft.world.entity.monster.Enemy.class,
                new net.minecraft.world.phys.AABB(X0 - 48, Y0 - 48, Z0 - 48,
                        X0 + 48, Y0 + 48, Z0 + 48))) {
            mob.discard();
            mobsCleared++;
        }
        say(TAG + "试验场清怪：" + mobsCleared + " 只（难度已设和平）");"""

OLD2 = """            } else if (t == T_B) {
                buildB();"""
NEW2 = """            } else if (t == T_B) {
                keepAlive();
                buildB();"""

OLD3 = """    private static InteractionResultHolder<ItemStack> useAxe(ServerPlayer who) {"""
NEW3 = """    /** 每个动手的场景开局先确认假玩家活着（被怪打死过就救回来，免得整场结论作废）。 */
    private static void keepAlive() {
        if (!player.isAlive() || player.getHealth() < player.getMaxHealth()) {
            player.setHealth(player.getMaxHealth());
            player.deathTime = 0;
            player.revive();
            say(TAG + "      [KEEPALIVE] 假玩家被打死过 —— 已救回满血");
        }
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
    }

    private static InteractionResultHolder<ItemStack> useAxe(ServerPlayer who) {"""

s = io.open(CHK, encoding="utf-8").read()

a1 = "        ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）"
assert s.count(a1) == 1, "段1锚点 %d" % s.count(a1)
s = s.replace(a1, NEW_ARENA, 1)
print("[OK] 段1 试验场清怪 + 和平难度")

assert s.count(OLD2) == 1, "段2锚点 %d" % s.count(OLD2)
s = s.replace(OLD2, NEW2, 1)
print("[OK] 段2 keepAlive")

assert s.count(OLD3) == 1, "段3锚点 %d" % s.count(OLD3)
s = s.replace(OLD3, NEW3, 1)
print("[OK] 段3 keepAlive 实现")

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
