# -*- coding: utf-8 -*-
"""_zf133_probefix4.py —— 根因：假玩家没进 PlayerList（这是"波不拆方块"的真因）

诊断跑（`_zf133_runSrv.log`）给出的铁证：`ShockwaveManager.tick()` 里那句临时 trace
**一行都没打出来**，而波确实在 5 tick 内消失了。唯一能在打印之前就 `return false` 的是
第一句：

    ServerPlayer owner = wave.level.getServer().getPlayerList().getPlayer(wave.owner);
    if (owner == null || !owner.isAlive()) return false;

⇒ **探针那个 `new ServerPlayer(...)` 从来没进过服务端玩家表**，`getPlayer(uuid)` 恒为 null，
所以每一道波都在出生的下一 tick 就地散掉。这解释了全部症状：
  · 耐久扣了、冷却进了（那些在物品/玩家身上，与波无关）；
  · 一格方块都没拆（波压根没推进一步）；
  · (d) 那些"撞墙就停"的断言**假通过**（波本来就没了，墙后那根自然还在）；
  · 冷却"300 tick 后解开"也是假通过（没有玩家 tick ⇒ 手动 tick 时它确实解开了，但
    第 299 tick 那条其实是靠手动 tick 撑的，不算假通过）。

修法：建完假玩家就 `server.getPlayerList().add(player)`（真实加入 ⇒ getPlayer 能查到、
服务端也会 tick 它 ⇒ ItemCooldowns 会自己走）。

⚠⚠ 这条要记进档案：**探针里的假玩家必须进 PlayerList**，否则任何"按 UUID 找回玩家"的
   服务端逻辑都会判成"人已经走了"。ZF114 那次没踩，是因为它的仪式表查的是
   `ServerPlayer` 自己的引用、不查 PlayerList。

跑法：python build\\zftools\\_zf133_probefix4.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

EDITS = [
    ("""        p.setGameMode(mode);
        return p;
    }""",
     """        p.setGameMode(mode);
        // ⚠⚠ 必须真的进服务端玩家表：`ShockwaveManager` 是靠 UUID 从 PlayerList 里把发射者
        //   找回来的（人下线/死了波就散），假玩家不登记的话 getPlayer(uuid) 恒 null ⇒
        //   每道波在出生的下一 tick 就地消失（诊断 trace 一行都没打出来，就是卡在这一句）。
        //   顺带的好处：服务端会 tick 它 ⇒ 物品冷却会自己走、玩家自身的逻辑也真的在跑。
        event.getServer().getPlayerList().add(p);
        return p;
    }"""),

    ("""        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);
        end.addFreshEntity(endPlayer);""",
     """        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);
        end.addFreshEntity(endPlayer);
        // ⚠ 同上：末地这台玩家也得进玩家表，否则波一样找不到人
        player.getServer().getPlayerList().add(endPlayer);"""),
]


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修：假玩家进 PlayerList")


main()
