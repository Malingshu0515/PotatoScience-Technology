# -*- coding: utf-8 -*-
"""_zf133_dbg12.py —— 监听 LivingDeathEvent + 打血量/游戏模式：查"假玩家为什么死了"

事实：`[TRENTRY] owner=zf133probe alive=false removed=false` —— 波没被拦住，是**玩家死了**。
（而 t=20 那三条 check 里 lookAngle 是 0/1.0/0 —— 那是**死人**的视线；
真人朝东应该是 (0.9999…, 0, 0.0000…)。这条也该早看出来。）

这一刀装一个死亡监听，把死因（伤害源 + 死亡消息）当场记下来。

跑法：python build\\zftools\\_zf133_dbg12.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

A1 = "    @SubscribeEvent\n    public static void onServerTick(ServerTickEvent.Post event) {"
B1 = """    @SubscribeEvent
    public static void onDeath(net.neoforged.neoforge.event.entity.living.LivingDeathEvent event) {
        say(TAG + "      [DEATH] " + event.getEntity().getName().getString()
                + " 死于 " + event.getSource().getMsgId()
                + " / " + event.getEntity().getCombatTracker().getDeathMessage().getString()
                + "（hp=" + event.getEntity().getHealth() + "）");
    }

""" + A1

A2 = "            long t = level.getGameTime() - t0;"
B2 = """            long t = level.getGameTime() - t0;
            if (t == T_STATIC || t == T_B || t == T_B_CHECK) {
                say(TAG + "      [HP] t=" + t + " hp=" + player.getHealth()
                        + " alive=" + player.isAlive() + " mode=" + player.gameMode.getGameModeForPlayer()
                        + " 视线=" + player.getLookAngle());
            }"""


def main():
    off = "--off" in sys.argv
    s = io.open(CHK, encoding="utf-8").read()
    for a, b in ([(B1, A1), (B2, A2)] if off else [(A1, B1), (A2, B2)]):
        n = s.count(a)
        assert n == 1, "锚点 %d 次：%r" % (n, a[:60])
        s = s.replace(a, b, 1)
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK] %s" % ("撤销" if off else "插入死亡监听 + 血量打印"))


main()
