# -*- coding: utf-8 -*-
u"""_zf104_docs.py —— ZF104 往 `docs/开发档案.md` 加 §4.70 / §4.71 两条雷区

⚙ 只做**一次插入**（锚点唯一性先查后改，§4.6）；不做任何全文件重写。
⚠ 用 Python 三引号原文写 Markdown（不用 PowerShell 双引号串，§11.1 末尾那条）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ANCHOR = u"""② `MachineScreen#mouseClicked` 先让部件过一遍，**吃掉就不再往下传**（否则会顺手触发原版"点背包槽位/丢东西"）。
"""

NEW = u"""② `MachineScreen#mouseClicked` 先让部件过一遍，**吃掉就不再往下传**（否则会顺手触发原版"点背包槽位/丢东西"）。


### 4.70 【实现雷】原版盔甲材料**喂不进小数**，而 `Tier` 那套写法**不能照抄**（0.11 ZF104）

用户给的两套盔甲里，钛合金头盔是 **护甲值 +2.5**、靴子 **+4.5**；星璨钢是 **+5.5 / +9.5 / +7.5 / +5.5**，
韧性还是**逐件不同**的 **0.5 / 1 / 0.5 / 0.5**。原版两条路都堵死：

| 想走的"正常路" | 为什么走不通 |
|---|---|
| `new ArmorMaterial(defense, ...)` | `defense` 是 `Map<ArmorItem.Type, **Integer**>` —— **整数**，2.5 进去就变 2 |
| 材料级 `toughness` | 它对**四件一视同仁**，表达不出"头 0.5 / 胸 1.0" |
| 抄 `ModTiers` 那样写个自定义 `Tier` | **盔甲没有 `Tier`**：`ArmorItem` 的护甲值/韧性是从 `ArmorMaterial` 物理写进属性修饰符的（`ArmorItem.java:70-94`） |

**可行的路**：照原版 `ArmorItem` 构造器里那几行**自己拼一份**
`ItemAttributeModifiers`（`AttributeModifier` 的 amount 是 `double`），覆写 `getDefaultAttributeModifiers()`。
两条附带结论：

- **修饰符 id 换命名空间**：原版用 `minecraft:armor.<部位>`；我们用自己的 `potato_s_t:armor.<部位>`，
  免得与别的装备**撞 id 被覆盖**。
- **工具提示不用额外做**：`ItemStack.addModifierTooltip` 对 `ADD_VALUE` 直接显示原值
  （`#.##` 格式），所以 `+2.5` 显示成 `+2.5`；会乘 100 的只有 `ADD_MULTIPLIED_*`，
  会乘 10 的只有 `KNOCKBACK_RESISTANCE`。

### 4.71 【校验雷】常量池查不到三类字面量 —— 探针首跑报了 26 条**假 FAIL**（0.11 ZF104）

本轮的交付门 `_zf103_verify.py` 第一版想"从 `.class` 的常量池证明 16 个数都编进去了"。
结果 8 个耐久数 + 3 个小数**全部被判成"没编进去"**。三类漏网之鱼：

| 源码写法 | 编出来是什么 | 常量池里有吗 |
|---|---|---|
| `int durability = 2801` | `sipush 2801`（0x11 + 2 字节立即数） | **没有** |
| `small = 2 / 10 / 16` | `bipush`（0x10）或 `iconst_*` | **没有** |
| `double t = 8.0` | `ldc2_w // double 8.0d` | 有（CONSTANT_Double，与 float **分开**） |
| `double t = 0.0 / 1.0` | `dconst_0` / `dconst_1` | **没有**（JVM 内建常量） |

⇒ **两条可执行的规矩**：
① 探针要么扫**字节码立即数**（`bipush`/`sipush`/`iinc` + `ldc/ldc_w/ldc2_w` 指向的 float/double），
   要么干脆用 `javap -p -c -constants` 反汇编；
② **别只信"文件里有这个名字"**：`grep`/常量池只能证明"这个名字被引用过"——
   把整个覆写删掉，那些断言全部照过（K5 那一刀就是这么漏的）。
   所以**"覆写还在不在"必须单独断言**（源码签名 + `@Override` 计数），并且
   该覆写体内的**关键分支**也要断言（本轮：`damageItem` 体内必须真的出现 `isNight()` 与 `return 0;`）。

> 这一轮的反证刀（`_zf103_falsify.py`，8 刀）**首跑就砍穿了 2 刀**（K4 韧性 1.0→0.0、K5 抽掉夜晚分支），
> 修完探针才全绿。**"探针自己没被反证过 = 探针不算数"**（§4.17）。
"""


def main():
    text = io.open(DOC, encoding="utf-8").read()
    if ANCHOR not in text:
        print(u"!! 锚点找不到")
        return 1
    hits = text.count(ANCHOR)
    if hits != 1:
        print(u"!! 锚点命中 %d 次（应为 1）" % hits)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text.replace(ANCHOR, NEW, 1))
    print(u"§4.70 / §4.71 已插入（%d → %d 字节）" % (len(text), len(text) + len(NEW) - len(ANCHOR)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
