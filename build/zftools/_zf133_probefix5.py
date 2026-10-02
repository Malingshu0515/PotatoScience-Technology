# -*- coding: utf-8 -*-
"""_zf133_probefix5.py —— 判据修：服务端 `sidedSuccess` 给的是 CONSUME 不是 SUCCESS

`InteractionResultHolder.sidedSuccess(stack, false)` 在**服务端**等于
`InteractionResult.CONSUME`（客户端那一侧才是 SUCCESS）。原版
`Player#startUsingItem` 那一挂就是这么返回的。

所以探针的判据要写成"**出手了**（SUCCESS 或 CONSUME）"，而不是只认 SUCCESS；
反过来"该拒绝"的判据要写成"**不是这两个**"（PASS / FAIL 都算没出手）。

⚠ 保留 `consumesAction()` 的教训：原版 `PASS.consumesAction()` 也是 true，
   第一轮就是被它骗过去的 —— 这里用**枚举相等**，不用那个方法。

跑法：python build\\zftools\\_zf133_probefix5.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

HELPER_OLD = """    private static int check(String name, boolean ok) {"""
HELPER_NEW = """    /**
     * "这一下真的出手了吗"的判据。
     *
     * <p>⚠ 服务端 {@code InteractionResultHolder.sidedSuccess(stack, false)} 返回的是
     * {@code CONSUME}（SUCCESS 只给客户端那一侧）—— 所以只认 SUCCESS 会**假 FAIL**；
     * 而 {@code consumesAction()} 连 {@code PASS} 都算 true（第一轮的假通过）。
     * 判定只用枚举相等。</p>
     */
    private static boolean fired(net.minecraft.world.InteractionResult result) {
        return result == net.minecraft.world.InteractionResult.SUCCESS
                || result == net.minecraft.world.InteractionResult.CONSUME;
    }

    private static int check(String name, boolean ok) {"""

EDITS = [
    (HELPER_OLD, HELPER_NEW),
    ("""        failed += check("右键出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("右键出手（结果 = " + r.getResult() + "）", fired(r.getResult()));"""),
    ("""        failed += check("冷却中再右键不出手（结果 = " + r.getResult() + "）",
                r.getResult() != net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("冷却中再右键不出手（结果 = " + r.getResult() + "）", !fired(r.getResult()));"""),
    ("""        failed += check("耐久 119 < 120 ⇒ 拒绝出手（结果 = " + r.getResult() + "）",
                r.getResult() != net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("耐久 119 < 120 ⇒ 拒绝出手（结果 = " + r.getResult() + "）", !fired(r.getResult()));"""),
    ("""        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）", fired(r.getResult()));"""),
    ("""        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("创造模式玩家照常出手（结果 = " + r.getResult() + "）", fired(r.getResult()));"""),
    ("""        failed += check("末地出手成功（结果 = " + r.getResult() + "）",
                r.getResult() == net.minecraft.world.InteractionResult.SUCCESS);""",
     """        failed += check("末地出手成功（结果 = " + r.getResult() + "）", fired(r.getResult()));"""),
]


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次：%r" % (i + 1, n, a[:60])
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("判据已改：fired() = SUCCESS 或 CONSUME")


main()
