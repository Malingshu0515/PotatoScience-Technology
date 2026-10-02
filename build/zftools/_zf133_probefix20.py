# -*- coding: utf-8 -*-
"""_zf133_probefix20.py —— 修探针的**末地假玩家维度**（第一轮 3 个 FAIL 的真因）+ 两处配套整理

根因（有现场证据，不是猜的）：

  `PlayerList.placeNewPlayer` 里有这么一段（字节码 offset 89 → 147）：

      Optional<ResourceKey<Level>> dim = load(player)
              .flatMap(<存档里的 Dimension 字段>)
              .orElse(Level.OVERWORLD);          // 89: getstatic Level.OVERWORLD
      ... player.setServerLevel(server.getLevel(dim) 或 overworld);   // 147

  全新假玩家没有 playerdata ⇒ **一律被丢到主世界**。于是 `makePlayer(..., end, "zf133end", ...)`
  造出来的"末地玩家"其实站在主世界，而 `ShockwaveManager.fire` 取的是 `player.serverLevel()`
  —— 波跟着玩家走 ⇒ 末地那场发射的波在主世界飞，`wave.level.dimension() == Level.END`
  一次都没成立 ⇒ `damageAt` 从没被调用 ⇒ 末影人 0 次命中。

  现场证据（build/zftools/_zf133_runSrv.log 第 4388-4389 行，第一轮带 trace 的版本打的）：

      [TRLOOP] tick 波数=1 [165268f5 travelled=0 total=0 dim=minecraft:overworld]
      [TRENTRY] tick 进入 owner=zf133end alive=true removed=false serverPlayers=3 travelled=0

  产品代码没问题（真玩家进末地时 serverLevel() 就是末地）⇒ 修在探针里。

本脚本做五件事（每处锚点都断言"只出现一次"）：

  E1 makePlayer：placeNewPlayer 之后把维度抢回来（`setServerLevel`，就是原版自己用的那一句）
  E2 场景编号改成**时间线顺序**（①..⑨），与 `_zf133_verify.py` 的 G4 和 T_* 注释一致
  E3 buildH：补一条"末地假玩家真的在末地"的前提断言；[DMG] 那行改成打**真实维度**
  E4 T_I_ALIVE 520 → 510（520 已在 64 格射程之外，第一轮第 4 个 FAIL 的真因）+ 判据措辞说人话
  E5 类注释里的场景清单同步（原来的 tick 值和编号都是旧的）

跑法：python build\\zftools\\_zf133_probefix20.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---------------------------------------------------------------- E1
A1 = """        server.getPlayerList().placeNewPlayer(conn, p, cookie);
        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）"""
I1 = """        server.getPlayerList().placeNewPlayer(conn, p, cookie);
        // ⚠⚠ **入表之后必须把维度抢回来**：`PlayerList.placeNewPlayer` 里有一句
        //   `player.setServerLevel(server.getLevel(<存档里的重生维度>).orElse(overworld))`
        //   —— 它的字节码 offset 89 是 `getstatic Level.OVERWORLD`、offset 147 就是那句
        //   `ServerPlayer.setServerLevel`。全新假玩家没有 playerdata ⇒ **一律落到主世界**，
        //   也就是"在末地造一台假玩家"实际造在了主世界。
        //   后果极隐蔽：`ShockwaveManager.fire` 取的是 `player.serverLevel()`，波**跟着玩家走**
        //   ⇒ 末地那场发出去的波在主世界推进，`wave.level.dimension() == Level.END` 一次都没成立，
        //   末影人永远吃不到那一刀，而报告看上去只是"伤害没抓到"。
        //   第一轮的现场证据（带 trace 的那版打的）：
        //     `[TRLOOP] tick 波数=1 [165268f5 travelled=0 total=0 dim=minecraft:overworld]`
        //   紧跟着的 `[TRENTRY] tick 进入 owner=zf133end alive=true ... travelled=0` 说明
        //   那道波正是末地假玩家发的。**这不是产品缺陷**（真玩家进末地时 serverLevel() 就是末地），
        //   是探针把假玩家放错了维度，所以修在探针里。
        //   `setServerLevel` 就是 placeNewPlayer 自己用的那一句，只改两个字段
        //   （`Entity.level` 与 `ServerPlayerGameMode.level`），不发包、不碰区块。
        if (p.serverLevel() != where) {
            String wrongly = p.serverLevel().dimension().location().toString();
            p.setServerLevel(where);
            say(TAG + "      [DIM] placeNewPlayer 把 " + name + " 丢到了 " + wrongly
                    + "，已抢回 " + where.dimension().location());
        }
        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）"""

# ---------------------------------------------------------------- E2 编号（时间线顺序）
RENUM = [
    # (老, 新) —— 段注释与 say 的抬头
    ("    // ------------------------------------------------------------ ⑤ (f) 冷却",
     "    // ------------------------------------------------------------ ⑦ (f) 冷却"),
    ('        say(TAG + "⑤ (f) 15 秒冷却");',
     '        say(TAG + "⑦ (f) 15 秒冷却");'),
    ("    // ------------------------------------------------------------ ⑥ (g) 耐久门槛",
     "    // ------------------------------------------------------------ ⑧ (g) 耐久门槛"),
    ('        say(TAG + "⑥ (g) 耐久不够一次 120");',
     '        say(TAG + "⑧ (g) 耐久不够一次 120");'),
    ("    // ------------------------------------------------------------ ⑦ (c) 创造模式",
     "    // ------------------------------------------------------------ ⑨ (c) 创造模式"),
    ('        say(TAG + "⑦ (c) 创造模式");',
     '        say(TAG + "⑨ (c) 创造模式");'),
    ("    // ------------------------------------------------------------ ⑧ (h) 末地伤害",
     "    // ------------------------------------------------------------ ⑥ (h) 末地伤害"),
    ('        say(TAG + "⑧ (h) 末地：10 + 0.5n 的远程伤害");',
     '        say(TAG + "⑥ (h) 末地：10 + 0.5n 的远程伤害");'),
]

# ---------------------------------------------------------------- E3 末地：前提断言 + 真维度
A3 = """        failed += check("末地那台假玩家活着（hp=" + endPlayer.getHealth() + "/"
                + endPlayer.getMaxHealth() + " alive=" + endPlayer.isAlive() + "）",
                endPlayer.isAlive() && endPlayer.getHealth() > 0.0F);"""
I3 = A3 + """

        // ⚠ 前提判据（§4.30：前提不成立时后面所有绿灯都不算数）：**"这台玩家在末地"必须先钉死**。
        //   上面那条"活着"挡不住第一轮那个坑 —— 它在主世界活着、波也在主世界飞，
        //   一路绿灯到最后一拍才报"末影人一次都没被打到"。
        //   可证伪：把 makePlayer 里那句 `p.setServerLevel(where)` 删掉，这条当场变红。
        failed += check("末地那台假玩家的维度**真的是末地**（实际 "
                + endPlayer.serverLevel().dimension().location() + "）",
                endPlayer.serverLevel() == end);"""

A3B = """        say(TAG + "      [DMG] 末影人 @ " + String.format("%.2f,%.2f,%.2f",
                ender.getX(), ender.getY(), ender.getZ())
                + " 发射者 @ " + String.format("%.2f,%.2f,%.2f",
                        endPlayer.getX(), endPlayer.getY(), endPlayer.getZ())
                + " 维度=" + end.dimension().location());"""
I3B = """        // ⚠ 这一行第一版只打了探针自己的 `end` 变量（`end.dimension()`），**两个实体的真实维度
        //   一个都没打** ⇒ 读日志的人（包括写下"两者都在末地"那条结论的人）被它骗了。
        //   诊断必须打**现场值**：谁在哪个维度，各打各的。
        say(TAG + "      [DMG] 末影人 @ " + String.format("%.2f,%.2f,%.2f",
                ender.getX(), ender.getY(), ender.getZ())
                + " 维度=" + ender.level().dimension().location()
                + " 发射者 @ " + String.format("%.2f,%.2f,%.2f",
                        endPlayer.getX(), endPlayer.getY(), endPlayer.getZ())
                + " 维度=" + endPlayer.serverLevel().dimension().location()
                + "（探针手里的 end 变量 = " + end.dimension().location() + "）");"""

# ---------------------------------------------------------------- E4 T_I_ALIVE
A4 = """    private static final int T_I_ALIVE = 520;    //    之后第 150 tick：必须还活着
    private static final int T_I_DEAD = 750;     //    之后第 300 tick：必须已散"""
I4 = """    // ⚠ 这两个值必须**跟着 MAX_DISTANCE=64 定**：波 1 格/tick ⇒ 第 65 次 tick 就超射程自己散。
    //   它在 t=450 那一刻出生、**同一 tick** 就被 ShockwaveManager 推第一步（探针的 tick 钩子
    //   排在 ShockwaveManager 之前，实测 t=800 先打 [WAVES] 再打 travelled=40 的那行 trace），
    //   所以它在 t=450+travelled 那一拍采样、travelled=65 那一拍（t=515）返回 false。
    //   旧的 T_I_ALIVE=520 **已经落在射程之外** ⇒ 永远查到 activeCount=0（第一轮第 4 个 FAIL）。
    //   ⚠ 顺带记一笔：`IDLE_LIMIT_TICKS=200`（"10 秒没碰到木头就消失"）在当前射程下
    //   **永远轮不到它触发**（64 < 200）—— (e)/(i) 两场绿灯真正的护栏都是射程上限，不是闲置计时。
    private static final int T_I_ALIVE = 510;    //    拆到木头（t=453）之后 57 tick：还活着且在射程内
    private static final int T_I_DEAD = 750;     //    远超 64 格射程：必须已散"""

A4B = """    /** (i) 之后第 150 tick：还活着（证明计时被重置过，不是从起手一路算）。 */
    private static void checkIAlive() {
        failed += check("拆到木头之后 150 tick，波**还活着**（滚动窗口重置了计时；activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 1);
    }

    /** (i) 之后第 300 tick：已散（>200 tick 没再碰到木头）。 */
    private static void checkIDead() {
        failed += check("再飞 150 tick（合计 300 tick 没碰到木头）⇒ 波已散（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 0);
    }"""
I4B = """    /**
     * (i) 之后第 60 tick：**还活着**。
     *
     * <p>这条能证的：波拆到木头之后不会当场散掉，也不会在射程内提前消失。</p>
     *
     * <p>⚠ <b>它证不了"计时被重置"</b>：滚动窗口是 200 tick，而射程上限只有 64 格（64 tick），
     * 波**永远先撞射程、后轮到期** ⇒ "重置过"与"没重置"在观测量上不可区分。
     * 要真的证滚动窗口，得先让 {@code IDLE_LIMIT_TICKS} 短于 {@code MAX_DISTANCE}（那是改产品数值），
     * 探针造不出这个差异。写在这里，免得下次有人把这条绿灯当成"滚动窗口已验证"。</p>
     */
    private static void checkIAlive() {
        failed += check("拆到木头之后 57 tick（仍在 64 格射程内），波**还活着**（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 1);
    }

    /** (i) 之后第 300 tick：已散（此时早已超出 64 格射程）。 */
    private static void checkIDead() {
        failed += check("再飞 300 tick（远超 64 格射程）⇒ 波已散（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 0);
    }"""

# ---------------------------------------------------------------- E5 类注释的场景清单
A5 = """ * <p><b>九个场景</b>（时间线全在同一场里跑，靠 tick 排队）：
 * <ol>
 *   <li>t=20   物品与档位静态事实（1192 耐久 / 钻石级 / 花费 120 / 冷却 300 / 基础伤害摘得干净）；</li>
 *   <li>t=40   (b) 一整排 6 根原木 + 头顶树叶 ⇒ 全拆光，且 A7（宽度外那一格）原样；</li>
 *   <li>t=120  (d) 石头墙 + 墙后一根原木 ⇒ 波停在墙前、墙后那根**必须还在**；</li>
 *   <li>t=200  (e) 起点是空旷地 ⇒ 拆完再飞 200 tick ⇒ 波自己散掉（用户第 2 条）；</li>
 *   <li>t=450  (i) **滚动窗口**：拆到木头就重新计时 ⇒ 第 150 tick 还活着、第 300 tick 已散；</li>
 *   <li>t=760  (f) 冷却：出手进 300 tick 冷却、冷却中再右键不出手，
 *              **显式 tick 满 300 次之后必须解开**（假玩家不在 PlayerList，等不来真实 tick）；</li>
 *   <li>t=780  (g) 耐久不够 120 时拒绝出手、且不进冷却；</li>
 *   <li>t=820  (c) 创造模式玩家照常出手（用户没给限制）；</li>
 *   <li>t=860  (h) 末地：末影人吃到 10 + 0.5n（n=玩家基础伤害）的伤害 ——
 *              用力量效果把 n 从 1 抬到 4（+3），所以期望值 = 10 + 2 = **12.0**。</li>
 * </ol>"""
I5 = """ * <p><b>九个场景</b>（时间线全在同一场里跑，靠 tick 排队）：**序号 = 实际执行顺序**，
 * 与报告里的 ①..⑨ 抬头、以及下面各 T_xxx 常量的注释一一对应。</p>
 * <ol>
 *   <li>t=20   ① 物品与档位静态事实（1192 耐久 / 钻石级 / 花费 120 / 冷却 300 / 基础伤害摘得干净）；</li>
 *   <li>t=40   ② (b) 一整排 6 根原木 + 头顶树叶 ⇒ 全拆光，且 A7（宽度外那一格）原样；</li>
 *   <li>t=130  ③ (d) 石头墙 + 墙后一根原木 ⇒ 波停在墙前、墙后那根**必须还在**；</li>
 *   <li>t=200  ④ (e) 起点是空旷地 ⇒ 拆完再飞一会儿 ⇒ 波自己散掉（实际死因是 64 格射程）；</li>
 *   <li>t=450  ⑤ (i) 拆到木头之后 60 tick 还活着、300 tick 后已散（同上：射程先到期）；</li>
 *   <li>t=760  ⑥ (h) 末地：末影人吃到 10 + 0.5n（n=玩家基础伤害）的伤害 ——
 *              用力量效果把 n 从 1 抬到 4（+3），所以期望值 = 10 + 2 = **12.0**；</li>
 *   <li>t=810  ⑦ (f) 冷却：出手进 300 tick 冷却、冷却中再右键不出手，
 *              **显式 tick 满 300 次之后必须解开**（假玩家不在 PlayerList，等不来真实 tick）；</li>
 *   <li>t=830  ⑧ (g) 耐久不够 120 时拒绝出手、且不进冷却；</li>
 *   <li>t=870  ⑨ (c) 创造模式玩家照常出手（用户没给限制）。</li>
 * </ol>"""


def main():
    raw = io.open(CHK, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    edits = [(A1, I1), (A3, I3), (A3B, I3B), (A4, I4), (A4B, I4B), (A5, I5)]
    edits += [(a, b) for a, b in RENUM]
    for a, b in edits:
        n = s.count(a)
        assert n == 1, "锚点出现 %d 次：%r" % (n, a[:80])
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    io.open(CHK, "wb").write(out.encode("utf-8"))
    print("[OK] 已应用 %d 处改动（换行 = %s）" % (len(edits), "CRLF" if crlf else "LF"))


main()
