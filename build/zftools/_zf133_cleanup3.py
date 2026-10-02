# -*- coding: utf-8 -*-
"""_zf133_cleanup3.py —— 精修探针里的诊断残留（按行号定位，改完复核）

盘上还剩 6 处（`_zf133_cleanup2.py` 扫出来的，行号就是它的输出）：
  358-359  `[DBG] 摆好之后玩家在哪`
  361-368  打开 `ShockwaveManager.DEBUG` + `[DBG] 放完后 ...` 循环 + `[DBG] 玩家视线`
  390-397  `[DBG] 树叶位 ...`（含那两行 tags / 注册表转储）

⚠ 214 行那句注释**留着**：它记的是"假玩家不登记就找不到人"这条真教训，
  下次读这段代码的人需要它。

跑法：python build\\zftools\\_zf133_cleanup3.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

BLOCKS = [
    # ① 摆好后玩家位置
    """
        say(TAG + "      [DBG] 摆好之后玩家在哪：" + player.blockPosition().toShortString()
                + "（他脚下那格已清空 ⇒ 不会被卡住）");""",

    # ② 打开 DEBUG + 逐格打印 + 视线
    """        // ⚠ 临时诊断（ZF133）：打开波内部的逐格 trace，并把采样格直接读出来对照
        ShockwaveManager.DEBUG = true;
        for (int z = -3; z <= 3; z++) {
            BlockPos p = new BlockPos(X0 + 1, Y0, Z0 + z);
            say(TAG + "      [DBG] 放完后 " + p.toShortString() + " = "
                    + level.getBlockState(p).getBlock().getName().getString()
                    + "（可砍=" + (!level.getBlockState(p).isAir()) + "）");
        }
        say(TAG + "      [DBG] 玩家 " + player.blockPosition().toShortString()
                + " 视线 " + player.getLookAngle() + " 朝向 " + player.getDirection());""",
]

# ③ 树叶那一整段（含标签转储）用正则
LEAF_BLOCK = None


def main():
    s = io.open(P, encoding="utf-8").read()

    # ⚠ 顺序要紧：**先**做下标切片（因为它依赖原文的行号/位置），**再**做文本替换。
    #   第一版倒过来写：两次 replace 已经改了字符串长度，切片自然找不到起点
    #   —— 而且失败时前面两次 replace 还在内存里、没写盘，所以文件没被改坏（运气好）。
    start = s.find("            net.minecraft.world.level.block.state.BlockState ls =")
    if start > 0:
        end = s.find("            if (!ls.isAir())", start)
        assert end > start, "找不到树叶段终点"
        s = s[:start] + s[end:]
        print("[OK] 撤掉树叶位那段（含标签转储）")
    else:
        print("[SKIP] 树叶位那段已经不在（dbg6 的插入当时就失败了）")

    for i, b in enumerate(BLOCKS):
        n = s.count(b)
        assert n == 1, "第 %d 段锚点 %d 次：%r" % (i + 1, n, b.strip().split("\n")[0][:70])
        s = s.replace(b, "", 1)
        print("[OK] 撤掉第 %d 段" % (i + 1))

    io.open(P, "w", encoding="utf-8", newline="\n").write(s)

    body = io.open(P, encoding="utf-8").read()
    for m in ("A133DBG", "DEBUG", "[DBG]"):
        print("  残留 %-10s = %s" % (m, m in body))


main()
