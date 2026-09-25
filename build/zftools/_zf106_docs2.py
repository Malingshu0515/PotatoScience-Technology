# -*- coding: utf-8 -*-
r"""_zf106_docs2.py —— ZF106 补记：用户的两条修正（末地永久不掉耐久 / 传送前免摔落）

用户原话：

  「星璨钢末地并不是不消耗耐久 传送之前加个缓降还是什么免除一下摔落伤害 要不然就摔死了」

⚠ 锚点唯一性先查后改。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

A = u"**成品**：本轮**未打包**（原因同上）；`_zf106_armor.py` / `_zf106_verify` 这类脚本已就位，\n等两边都停下来一次性 build + 发布 + 活体数字对账。\n"
N = A + u"""

**⚠ 用户随后的两条修正（同日，已改完）**

原话：「星璨钢末地并不是不消耗耐久 传送之前加个缓降还是什么免除一下摔落伤害 要不然就摔死了」

- [x] **① 末地永久不掉耐久**：原实现里"耐久不消耗"只在 `level.isNight()` 成立，而末地是
      `hasFixedTime()` ⇒ `isNight()` 恒 false ⇒ **末地反而会掉耐久**，与"套装效果：末地维度盔甲
      不消耗耐久"正好相反。现在 `ModArmorPiece.damageItem` 有两条规则：
      ①**夜晚**（每件各自生效，不需满套）；②**末地 + 穿满四件星璨钢**（永久，不受昼夜影响）。
      判"满套"的辅助（`hasFullStarSteelSet` / `hasAnyStarSteelPiece`）**从 `ModArmorSet` 搬去
      `ModArmorMaterials`** —— 因为 `ModArmorPiece` 也要用，而它不该认识"套装效果"那个类。
- [x] **② 传送前免除摔落伤害**（新增 `preventFallDamage(player)`，**在 `teleportTo` 之前**调用）：
      · `resetFallDistance()` ⇒ 清掉"掉进虚空时**已经攒下**的那段坠落距离"
        （玩家是掉到 Y&lt;-64 才吃虚空伤害的，那时 fallDistance 早就很大，不归零的话落地照样结算）；
      · `MobEffects.SLOW_FALLING` 940 tick（47 s）⇒ 让 `LivingEntity.checkFallDamage` 里
        `if (this.fallDistance > 0)` 永远不成立，**传送后**从世界顶落到底也不结算。
      两条缺一不可：前者管"过去的账"，后者管"接下来的路"。
      落点 Y 轴不限 ⇒ 往上 320 格也可能中选，没这两条就是 300+ 格自由落体，必死。
- [x] **四语言 tooltip 跟着改**（`_zf106_lang.py`）：写清"末地永久不掉耐久"与"传送前给缓降"。
      ⚠ 顺手踩到一个坑：第一版文案里用了 Markdown 的 `**加粗**`，而 **MC 的 tooltip 不认这个**
      ⇒ 星号会原样显示；已全部去掉（这类"给机器看的语法混进给人看的文本"记在 §4.29 同源那一类）。
- [x] **探针升到 185 条**（+末地规则 2 条、缓降 3 条、Layer 调用形状 2 条），反证刀 **12 把**全过。

**⚠ 这一轮反证刀又砍穿了 3 刀（都当场修了）**

| 刀 | 漏在哪 | 怎么补的 |
|---|---|---|
| K11 删掉 `preventFallDamage` 的**调用** | 探针只断言"`resetFallDistance` / `SLOW_FALLING` 这些**名字**在常量池里"，函数**定义了但没人调**照样过 | 加一条**调用点**断言：`(preventFallDamage, (L…ServerPlayer;)V)` 必须出现在常量池的**方法引用**里 |
| K6 把 Layer 改成原版命名空间 | 探针只查"`potato_s_t` 这个字符串在不在"，而同类的 `ARMOR_MATERIAL` ResourceKey **也**用同一个 MODID 常量 ⇒ 改掉 Layer 那处字符串照样在 | 改成查**调用形状**：必须出现 `fromNamespaceAndPath(String,String)` 的方法引用，且 `withDefaultNamespace` **一次都不许出现** |
| K5 / K6 锚点 | 我改了实现，刀里的锚点文本没跟着改 ⇒ 报"锚点命中 0 次"（**不是**静默跳过，脚本会 FAIL 出来，这点是对的） | 锚点跟着新代码改 |

> 三条合起来还是 §4.71 那条：**"名字在不在"是最弱的判据**。
> 要证明一个行为，得断言**调用形状 / 调用点 / 关键分支**。
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
