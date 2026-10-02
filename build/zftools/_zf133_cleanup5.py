# -*- coding: utf-8 -*-
"""_zf133_cleanup5.py —— 撤掉 ShockwaveManager / Zf133Check 里**最后一轮**的诊断（trace）

`_zf133_trace.py` 插进去的那套 `TRACE` / `[TR]` / `[TRLOOP]` / `[TRENTRY]` 现在还在产品代码里
（`_zf133_verify.py` 的 B23 就是盯这个的，它当场红了 —— 这正是那条判据的用处）。

撤法：先扫盘上有哪些行带标记，再按"块"删（用行首行尾配对，不靠记忆里的长锚点）。

跑法：python build\\zftools\\_zf133_cleanup5.py          # 只看
      python build\\zftools\\_zf133_cleanup5.py --write  # 删
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
WRITE = "--write" in sys.argv

# 要整块删掉的片段（逐条列出；每条都必须恰好命中 1 次）
BLOCKS = [
    # TRACE 开关字段
    """
    /** ⚠ 临时 trace 开关（ZF133 查"波为什么停"，修好前一直留着）。 */
    public static boolean TRACE = false;
""",
    # onServerTick 里的 TRLOOP
    """        if (TRACE && !WAVES.isEmpty()) {
            StringBuilder sb = new StringBuilder("[TRLOOP] tick 波数=" + WAVES.size());
            for (Wave w : WAVES) {
                sb.append(" [" + w.owner.toString().substring(0, 8)
                        + " travelled=" + w.travelled + " total=" + w.totalTicks
                        + " dim=" + w.level.dimension().location() + "]");
            }
            System.out.println(sb);
        }
""",
    # tick() 进入时的 TRENTRY
    """        if (TRACE) {
            System.out.println("[TRENTRY] tick 进入 owner=" + (owner == null ? "null" : owner.getName().getString())
                    + " alive=" + (owner != null && owner.isAlive())
                    + " removed=" + (owner != null && owner.isRemoved())
                    + " serverPlayers=" + wave.level.getServer().getPlayerList().getPlayers().size()
                    + " travelled=" + wave.travelled);
        }
""",
    """            if (TRACE) {
                System.out.println("[TRENTRY] -> 就地散掉（owner null 或已死）");
            }
""",
    # 采样循环里的 tr 变量 + air trace
    """                boolean tr = TRACE;
""",
    """                if (state.isAir()) {
                    if (tr) {
                        System.out.println("[TR] t" + wave.totalTicks + " " + pos.toShortString()
                                + " air");
                    }
                    continue;
                }""",
]

# 用正则处理"多行、结构不规则"的两处
REGEX_BLOCKS = [
    # 采样打印（[TR] ... chop= ... tool= ...）
    re.compile(r"""                if \(tr\) \{\n                    System\.out\.println\("\[TR\][\s\S]*?\n                \}\n"""),
    # destroy 打印
    re.compile(r"""                if \(tr\) \{\n                    System\.out\.println\("\[TR\][\s\S]*?\n                \}\n"""),
]


def main():
    s = io.open(SHOCK, encoding="utf-8").read()
    print("=== 盘上带标记的行 ===")
    for i, line in enumerate(s.split("\n")):
        if any(m in line for m in ("TRACE", "[TR]", "trace", "System.out")):
            print("  %4d| %s" % (i + 1, line.strip()[:130]))
    if not WRITE:
        print("\n（只看；要删加 --write）")
        return

    for i, b in enumerate(BLOCKS):
        n = s.count(b)
        if n != 1:
            print("[SKIP] 第 %d 段命中 %d 次（不在盘上或已删）：%r" % (i + 1, n, b.strip()[:60]))
            continue
        s = s.replace(b, "", 1)
        print("[OK ] 第 %d 段已删" % (i + 1))

    for r in REGEX_BLOCKS:
        s, n = r.subn("", s, count=1)
        print("[%s] 正则块：删了 %d 处" % ("OK " if n == 1 else "SKIP", n))

    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
    left = [l.strip()[:120] for l in s.split("\n")
            if any(m in l for m in ("TRACE", "[TR]", "trace", "System.out"))]
    print("--- 残留 ---")
    print("\n".join(left) if left else "（干净）")


main()
