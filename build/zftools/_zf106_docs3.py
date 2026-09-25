# -*- coding: utf-8 -*-
r"""_zf106_docs3.py —— ZF106 补记之三：伤害吸收**不许提前续**（护盾不要立马就恢复）

⚠ 编号回避：并行的另一条线已经用了 **ZF107**（成就那一轮），所以本轮不再新开编号，
  继续挂在 ZF106 条目下（同一轮的用户反馈，本来也该在一起）。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

A = u"> 三条合起来还是 §4.71 那条：**\"名字在不在\"是最弱的判据**。\n> 要证明一个行为，得断言**调用形状 / 调用点 / 关键分支**。\n"
N = A + u"""

**⚠ 用户第三条修正（同日）：伤害吸收**不许提前续****

原话：「没有伤害吸收效果不需要立即重置 末地15s给12伤害吸收 晚上45秒才给10s是为了平衡 护盾不要立马就恢复」

- [x] **病灶**：`ensure(...)` 原来只有一个固定的补充阈值 `REFRESH_MARGIN = 40`（剩余 &lt; 2 s 就补），
      **伤害吸收和持续型效果共用它** ⇒ 护盾还没扣完就被补满，等于"永久满护盾"，
      把 3 s / 35 s 的空窗全吃掉了 —— **而那段空窗就是平衡点本身**。
- [x] **改法**：`ensure(...)` 多一个 `refreshMargin` 参数，两档语义分开写死：
      · `KNOCKBACK_MARGIN = 40` —— 持续型（抗性 / 力量 / 恢复）提前 2 s 续，玩家察觉不到断档；
      · `ABSORPTION_REFRESH = 0` —— **必须等效果彻底结束**（被打空或时长走完）才给下一次。
      周期因此恢复成用户要的 **末地 15 s / 主世界 45 s**，护盾该破的时候就会破。
- [x] **四语言 tooltip 写清楚**：加了"伤害吸收是**周期性给的一次性护盾**：这一次的时长走完
      （或者被打空）才会给下一次，不会提前补满"（**不用** Markdown 的 `**`，MC 的 tooltip 不认）。

**⚠ 探针这次一开始**抓不到**这条（K13 砍穿）—— 补的是"**调用点实参**"取证**

`ABSORPTION_REFRESH = 0` 这个**零值**在字节码里是 `iconst_0`，**常量池里什么都没有**
（§4.71 那三类漏网字面量的近亲）。所以原来那套"查名字/查 int 池"对它完全失效。
补法是换一个取证口 —— **`javap -constants` 会把编译期常量直接打在字段声明行上**：

```
private static final int KNOCKBACK_MARGIN = 40;
private static final int ABSORPTION_REFRESH = 0;
```

再配合"**调用点实参序列**"（javap 把压栈的数字写在同一条指令行里）就能证明语义：
`..., 240, 0, invokestatic ensure` = 吸收（时长 12 s、阈值 0）、
`..., 320, 40, invokestatic ensure` = 持续型（时长 16 s、阈值 40）。
⇒ 探针升到 **198 条**，反证刀升到 **13 把**（K13 就是这一条），全过。

**第三次跟"活体数字"**：并行的另一条线本轮又给四语言加了 **48 个成就键**（350 → **398**），
锚点已跟着改（`_zf106_retarget.py`）。这已经是第四次（335→349→350→398）——
**建议**：以后新写的校验脚本，语言键数这类"会一直涨"的数字**只断言"四份一致"**，
不要写死具体值；写死的那些每加一个键就要全库 retarget 一遍。
"""
ANCHOR = A


def main():
    text = io.open(DOC, encoding="utf-8").read()
    n = text.count(ANCHOR)
    print(u"锚点命中 %d 次" % n)
    if n != 1:
        print(u"!! 锚点不唯一，一个字节都不写")
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text.replace(ANCHOR, N, 1))
    print(u"已插入（%d → %d 字节）" % (len(text), len(text) + len(N) - len(ANCHOR)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
