# -*- coding: utf-8 -*-
"""_zf133_probefix14.py —— 试验场被怪物屠了：受击记录抓到真凶

`[DEATH] zf133probe 死于 explosion.player / zf133probe was blown up by Creeper`
—— 平台铺在 y=159，**平台下方没有光照**（41×41 的悬空石台，方块光是 0），
于是苦力怕/僵尸/骷髅在台子下面刷出来，爆炸波及到站在台面上的假玩家（台子只有 1 格厚）。
连带把测试用的方块也炸飞了（这才是 (e) 那格木头"没被拆掉"的真因 —— 它先被炸掉了）。

三步修：
  ① **和平难度**（`setDifficulty(Peaceful)`）：不刷敌对生物，已存在的会被清掉；
  ② `discard()` 掉试验场周围的 `Enemy`（双保险，和平难度只对**之后**的刷怪生效）；
  ③ 每场景开局把假玩家回满血 + 断言（既有的"满血存活"断言挪到开场之后一起看）。

跑法：python build\\zftools\\_zf133_probefix14.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """            ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）"""
NEW = """            ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）

            // ⚠⚠ 试验场必须**没有怪物**：平台铺在 y=159、厚度 1 格，台子下面是黑的 ⇒
            //   苦力怕/僵尸/骷髅在台子下面刷出来，爆炸会波及站在台面上的假玩家
            //   （受击记录：`[DEATH] zf133probe 死于 explosion.player ... blown up by Creeper`），
            //   连带把摆好的测试方块炸飞 —— (e) 那格木头"没被拆掉"的真因就是它先被炸掉了。
            //   和平难度不刷敌对生物；已存在的另用 discard() 清一遍（和平只对之后的刷怪生效）。
            level.getServer().setDifficulty(net.minecraft.world.Difficulty.PEACEFUL, true);
            int cleared = 0;
            for (net.minecraft.world.entity.monster.Enemy mob : level.getEntitiesOfClass(
                    net.minecraft.world.entity.monster.Enemy.class,
                    new net.minecraft.world.phys.AABB(X0 - 48, Y0 - 48, Z0 - 48,
                            X0 + 48, Y0 + 48, Z0 + 48))) {
                mob.discard();
                cleared++;
            }
            say(TAG + "试验场清怪：" + cleared + " 只（难度已设和平）");"""

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


def main():
    s = io.open(CHK, encoding="utf-8").read()
    for i, (a, b) in enumerate([(OLD, NEW), (OLD2, NEW2), (OLD3, NEW3)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修：和平难度 + 清怪 + 每场景保活")


main()
