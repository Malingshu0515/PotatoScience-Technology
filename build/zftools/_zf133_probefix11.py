# -*- coding: utf-8 -*-
"""_zf133_probefix11.py —— 假玩家一出生就是死的（hp=0），先救活它

铁证（探针打印）：`[HP] t=20 hp=0.0 alive=false mode=SURVIVAL 视线=(1.0, 0, 1.2e-16)`
—— 从第一刻起血量就是 0。于是：
  · `ShockwaveManager.tick()` 的 `!owner.isAlive()` ⇒ 每一道波出生的下一 tick 就地散；
  · 探针那些 `level.destroyBlock(...)` / `hurtAndBreak(...)`（直接调方法）**照样执行** ——
    这正是"方块摆得上、耐久扣得掉，波却一格都不拆"的完整解释。

救法：`placeNewPlayer` 之后显式 `setHealth(getMaxHealth())` + `deathTime = 0` +
`revive()`（`LivingEntity#revive` 就是原版"复活"用的那个内部方法，探针里用得上），
并且**当场断言** hp 满、isAlive=true —— 这个前提不成立的话后面所有场景都不算数，
所以它必须是探针的第一条断言（"前提也要有判据"）。

跑法：python build\\zftools\\_zf133_probefix11.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）
        return p;
    }"""
NEW = """        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）
        // ⚠⚠ 假玩家一出生血量就是 0（`placeNewPlayer` 的副作用：登录流程里先按"未初始化"处理）。
        //   实测打印：`[HP] t=20 hp=0.0 alive=false`。后果极隐蔽 ——
        //   `ShockwaveManager.tick()` 第一句就是"人还在不在"，人死了波就散；
        //   而探针直接调的 `destroyBlock` / `hurtAndBreak` 完全不受影响 ⇒
        //   表现为"方块摆得上、耐久扣得掉、波一格都不拆"。**先救活，再断言。**
        p.setHealth(p.getMaxHealth());
        p.deathTime = 0;
        p.revive();
        p.hurtTime = 0;
        say(TAG + "      假玩家 " + name + " 入场：hp=" + p.getHealth() + "/" + p.getMaxHealth()
                + " alive=" + p.isAlive() + " 位置=" + p.blockPosition().toShortString());
        return p;
    }"""

OLD_CHECK = """            failed += check("假玩家已进服务端玩家表（getPlayer 查得到）",
                    event.getServer().getPlayerList().getPlayer(player.getUUID()) != null);"""
NEW_CHECK = """            failed += check("假玩家已进服务端玩家表（getPlayer 查得到）",
                    event.getServer().getPlayerList().getPlayer(player.getUUID()) != null);
            // ⚠ 前提判据：后面八个场景全都建立在"这台假玩家活着"之上，
            //   所以这条必须第一个断言（§4.30：前提不成立时后面的绿灯都不算数）。
            failed += check("假玩家满血且存活（hp=" + player.getHealth() + "/"
                    + player.getMaxHealth() + "）",
                    player.isAlive() && player.getHealth() == player.getMaxHealth());
            failed += check("假玩家朝向是东（视线 x > 0.9，实际 "
                    + String.format("%.3f", player.getLookAngle().x) + "）",
                    player.getLookAngle().x > 0.9D);"""


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate([(OLD, NEW), (OLD_CHECK, NEW_CHECK)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修：假玩家救活 + 前提断言")


main()
