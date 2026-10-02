# -*- coding: utf-8 -*-
"""_zf133_cleanup.py —— 撤掉全部临时诊断（产品代码必须回到"只有功能"的样子）

清哪些（逐条列出，撤完自己再扫一遍关键字）：
  ShockwaveManager.java
    · `public static boolean DEBUG` 常量
    · `StringBuilder trace = ...` 与两处 `trace.append(...)`
    · `if (DEBUG) { ... }` 打印块（前缘 trace + 逐格采样 + 收尾）
  StarSteelAxeItem.java
    · `[A133DBG2] use(): ...` 那一段（冷却诊断）
  Zf133Check.java（探针，跑完也要干净）
    · `public static boolean DBG`、`DBG = true;`、`ShockwaveManager.DEBUG = true;`
    · 两处 `[DBG]` 打印（摆好后玩家位置 / 放完后逐格）
    · DBG6 那段标签转储（`isLEAVES=` / 注册表计数）
    · `t.printStackTrace` 那句是正经错误处理，**留着**

跑法：python build\\zftools\\_zf133_cleanup.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
AXE = r"E:\PotatoST\src\main\java\com\potatost\mod\StarSteelAxeItem.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

REMOVALS = {
    SHOCK: [
        """
    /** ⚠ 临时诊断开关（ZF133 查"波不拆方块"用，查完连同 trace 一起删）。 */
    public static boolean DEBUG = false;
""",
        """        StringBuilder trace = DEBUG ? new StringBuilder("t" + wave.totalTicks + " main=")
                .append(wave.mainCoord(wave.alongX ? ox : oz)) : null;
""",
        """                if (DEBUG && (state.isAir() || isChoppable(state) || !owner.getMainHandItem().isCorrectToolForDrops(state))) {
                    trace.append(' ').append(pos.toShortString()).append('=')
                            .append(state.getBlock().getName().getString());
                }
""",
        """                if (DEBUG) {
                    trace.append(" [destroy ").append(pos.toShortString()).append('=')
                            .append(destroyed).append(']');
                }
""",
        """        if (DEBUG) {
            System.out.println("[A133DBG] " + trace + " broke=" + broke + " blocked=" + blocked);
        }
""",
    ],
    AXE: [
        """        if (com.potatost.mod.Zf133Check.DBG) {
            System.out.println("[A133DBG3] addCooldown(" + SHOCKWAVE_COOLDOWN_TICKS + ") 之后 isOnCooldown="
                    + player.getCooldowns().isOnCooldown(this)
                    + " percent=" + player.getCooldowns().getCooldownPercent(this, 0.0F)
                    + " cd=" + player.getCooldowns());
        }
""",
    ],
    CHK: [
        """    /** ⚠ 临时诊断开关（ZF133 查冷却门禁用），查完删。 */
    public static boolean DBG = false;

""",
        """        DBG = true;
""",
        """        // ⚠ 临时诊断（ZF133）：打开波内部的逐格 trace，并把采样格直接读出来对照
        ShockwaveManager.DEBUG = true;
        for (int z = -3; z <= 3; z++) {
            BlockPos p = new BlockPos(X0 + 1, Y0, Z0 + z);
            say(TAG + "      [DBG] 放完后 " + p.toShortString() + " = "
                    + level.getBlockState(p).getBlock().getName().getString()
                    + "（可砍=" + (!level.getBlockState(p).isAir()) + "）");
        }
        say(TAG + "      [DBG] 玩家 " + player.blockPosition().toShortString()
                + " 视线 " + player.getLookAngle() + " 朝向 " + player.getDirection());
""",
        """
        say(TAG + "      [DBG] 摆好之后玩家在哪：" + player.blockPosition().toShortString()
                + "（他脚下那格已清空 ⇒ 不会被卡住）");""",
    ],
}

# DBG6 那段（用正则，因为它横跨多行且带 lambda）
CHK_TAGDUMP = re.compile(
    r"""            net\.minecraft\.world\.level\.block\.state\.BlockState ls = level\.getBlockState\(lp\);\n"""
    r"""            say\(TAG \+ "      \[DBG\] 树叶位 ".*?\n(?:.*?\n)*?            \}\n""", re.S)


def main():
    for path, blocks in REMOVALS.items():
        s = io.open(path, encoding="utf-8").read()
        before = len(s)
        for b in blocks:
            n = s.count(b)
            if n != 1:
                print("[FAIL] %s 里这段出现 %d 次：%r" % (path, n, b.strip().split("\n")[0][:70]))
                sys.exit(1)
            s = s.replace(b, "", 1)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        print("[OK ] %s  %d -> %d 字符" % (path, before, len(s)))

    s = io.open(CHK, encoding="utf-8").read()
    s2, n = CHK_TAGDUMP.subn("", s)
    if n != 1:
        print("[FAIL] DBG6 标签转储那段匹配 %d 次" % n)
        sys.exit(1)
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s2)
    print("[OK ] DBG6 标签转储已撤")

    print("-" * 60)
    for path in (SHOCK, AXE, CHK):
        body = io.open(path, encoding="utf-8").read()
        left = [k for k in ("A133DBG", "DEBUG", "DBG =", "[DBG]", "trace.append", "leavesLeft")
                if k in body]
        print("%s 残留：%s" % (path.split("\\")[-1], left if left else "无"))


main()
