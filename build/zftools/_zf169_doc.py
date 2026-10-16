#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF169 文档记账：往 docs/开发档案.md 插入
   ① §5 的 ZF169 行（插在 ZF165 行之后）
   ② §4.177 一条雷（本轮真正浪费时间的那个）
   ③ §9 的 ZF169 待实测段
  以及把 §6.23（让一种流体/粉尘和别的 mod 通用要动哪几处）补上硫这个实例。

一律按行锚点插入；写前整份留底到 build/tmp/zf169/。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARCHIVE = r"E:\PotatoST\PotatoSTneoforge1.21.1\docs\开发档案.md"
STASH = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\tmp\zf169"

ROW = '''| ZF169 | ⚠ **本轮没有单独建 `zf169_pre`** —— 改动只有 3 个 java（`ModItems` / `AcidicReactionChamberBlockEntity` / `AcidicReactionChamberMenu`）+ 1 个新数据文件 + 1 行父标签，全部都是**加行**；且开工前盘上已有 `zf165_pre` 与 `zf166_pre` 两份近照。 | **0.13：硫 / 硫磺粉统一到 `#c:dusts/sulfur`，酸性反应室认别家的硫磺**（用户原话「硫和别的mod硫磺统一标签 酸性反应室也认别的mod的硫磺」）。① **先查「对端到底用哪条标签」，再挂**：从盘上三个 jar 逐条取证 —— 通用机械 `data/c/tags/item/dusts/sulfur.json` → `mekanism:dust_sulfur`；沉浸工程同名文件 → `immersiveengineering:dust_sulfur`；机械动力：柴油动力的除草剂配方、沉浸工程的火药/肥料/除草剂三条配方，吃的也都是 `c:dusts/sulfur`。**三家没有一家用光秃秃的 `c:sulfur`** ⇒ 用户说的「硫磺」在这里就是「硫磺粉」（dust），挂的必须是 `c:dusts/sulfur`；只挂 `c:sulfur` 会得到一个「谁都不认」的空标签（**看着做了，其实一点用没有**）。② **只挂这一条**：`c:sulfur` 不挂、`c:storage_blocks/sulfur` 不挂（我们没有硫块）。③ **§4.167 那条「挂之前先查反向配方」逐条核过，没有闭环**：能吃这条标签的是 Mek 的 enriching（→1 火药）/ oxidizing（→100 mB 二氧化硫）/ chemical_conversion（→2 mB 硫酸）与 IE 的火药/肥料/除草剂；反过来能**产出**它的只有 Mek 的 injecting（火药+氯化氢→硫粉）、IE 的烈焰粉/煤矿/青金石/石英**副产物**、沉浸原油的加氢处理（含硫柴油→硫粉）—— **没有一条能把火药、二氧化硫或硫酸变回硫**。另一条看着像环的（沉浸原油焦化炉吃 `c:bitumen`）**不存在**：我们的沥青没挂那条标签。④ **三道门禁只留一份判据**（§4.51）：新增 `ModItems.SULFUR_TAG` + `ModItems.isSulfur(ItemStack)`，酸性反应室的**方块实体 `isItemValid` / 菜单槽 `mayPlace` / Shift 快移 `getMachineSlotFor`** 三处全部转调它；全工程不再有第二处写死的 `stack.is(ModItems.SULFUR.get())`（常驻门 B3 在盯）。⚠ **产出侧故意不动**：加氢脱硫反应室仍然只产出我们自己的 `potato_s_t:sulfur`，它的输出槽判定照旧写死我方物品（门 B3 的白名单把这一条显式放行）。⑤ **真服务端探针 `Zf167Check` 28/0**（把沉浸工程 12.4.2 + 通用机械 10.7.19 拷进 `run/server/mods` 跑、跑完删掉）：`#c:dusts/sulfur` 成员实测 = `[immersiveengineering:dust_sulfur, mekanism:dust_sulfur, potato_s_t:sulfur]`（**三家同一条**）、父标签 `#c:dusts` 传递包含成立、三道门禁对我方与 Mek/IE 的硫粉全放行、铁粉/火药/圆石三道门全拒；**最硬的一条**：拿沉浸工程真配方 `immersiveengineering:crafting/gunpowder_from_dusts` 的**第 4 个成分对象**直接 `Ingredient.test(我们的硫)` = **true**（火药 = false）—— 不是我们复刻标签逻辑，是上游自己的判据认了。⑥ **顺带白捡**：IE 那几条「矿石粉碎副产硫粉」的配方带着 `neoforge:tag_empty c:dusts/sulfur` 条件（标签空就关着），我们挂上去只是再加一员。⑦ 常驻门 `_zf169_gate.py` **27 项**（数据 / 源码三道门禁 / 负面对照 / 探针报告 / 文档）；**五份 lang 一个字节没改**（硫那两句文案本来就是通用说法「要 10 个」）。⑧ ⚠ **本轮没重打成品**（与 ZF165 同一批欠账，下次打包一起带上）。 | 见 §9 ｜ 见 §4.167 / §4.177 / §6.23 |'''

L176 = '''### 4.177 【工具雷】先看清方法签名再写调用：`RecipeManager#byKey` 收的是 `ResourceLocation` 而不是 `ResourceKey`；以及「尺子坏了」会把整段判据变成废纸（0.13 ZF169）

这一轮为了一条「最硬的判据」（拿上游**自己的** `Ingredient.test` 去问收不收我们的硫）写探针，
结果在**工具**上连续翻了四次车，值得单独记一笔。

**第一坑：签名凭印象写。**
我按记忆里 Forge 时代的形状写成
`server.getRecipeManager().byKey(ResourceKey.create(Registries.RECIPE, rl))`，
编译器连着报「不存在类型变量 T 的实例，以使 ResourceKey<T> 与 ResourceLocation 一致」。
我以为是泛型推不出来，加类型见证、换 `ResourceKey.<Recipe<?>>create(...)`，
甚至改成「遍历 `getRecipes()` 比字符串」—— 全是在错误的方向上打补丁。
**真相**：1.21.1 的这个方法是
`public Optional<RecipeHolder<?>> byKey(ResourceLocation recipeId)`（源码 `RecipeManager.java:137`）
—— **它压根不收 ResourceKey**。改成 `byKey(ResourceLocation.parse(id))` 一行就好了。

⇒ **规矩**：编译错说「类型对不上」时，**先把那个方法的签名打出来看**（`javap`，或者直接读
`build/neoForm/.../steps/transformSource/transformed/` 下的原版源码），别顺着自己的假设往下加限定。

**第二坑（更值钱）：判据的「尺子」自己坏了，却把结论写成 FAIL。**
第一版探针用一个自制的「只装一件东西」的输入容器，把整套配方表逐张 `matches()` 跑一遍。
它报「认得我们的硫的配方 = **0 张**」—— 我差点当成「标签没接上」。
**幸好**顺手加了一条自检：拿**木棍**去跑同一把尺子 —— 也是 0 张，
**连 `minecraft:stick` 都扫不出任何配方**。尺子是坏的：那种自制输入容器喂不进各家配方类型。

⇒ 两条规矩：

1. **任何「批量扫描/统计」型判据，必须先拿一个**已知一定有命中**的样本自检**（正对照）。
   正对照不过，那个数字一个都不能信 —— 不是「结果是 0」，是「尺子坏了」。
2. 尺子坏了的时候，**不要把 0 写成 FAIL**：那是**工具局限**，不是被测代码的问题。
   本轮把它降成 `[INFO]` 并在门里说明，举证改由「配方在位 + 上游成分判据」承担
   —— 见 §4.156（门红的时候先想是不是自己的期望值/工具过时了）。

**第三坑：`SimpleContainer` 不是 `RecipeInput`。**
1.21 的 `Recipe<T extends RecipeInput>` 要的是 `RecipeInput`，而 `SimpleContainer` 并没有实现它；
   自制输入容器要实现 `getItem(int)` + `size()`。

**结论**：这一轮最终留下的是 `C1`（四条配方在真表里都在）+ `C2/C3`
（IE 那条配方的第 4 个成分对象自己 `test(我们的硫)=true`、`test(火药)=false`）——
比「扫描器说 0」结实得多。'''

SEC9 = '''### ZF169（0.13）硫 / 硫磺粉统一到 `#c:dusts/sulfur`，酸性反应室认别家的硫磺 —— **待你实测**

**要你做的**：

1. JEI 里搜 `immersiveengineering:dust_sulfur`（沉浸工程硫粉）或 `mekanism:dust_sulfur`
   （通用机械硫粉）：**它们和我们那袋黄色的「硫」应当能互相替代** ——
   比如沉浸工程的**火药**配方（4 硝石粉 + 1 硫粉 + 木炭 → 6 火药），
   三个硫粉里放哪个都该能合出来。
2. **酸性反应室的硫槽**：把沉浸工程 / 通用机械的硫粉放进去（直接放、或 Shift 快移），
   应当和放我们自己的硫一模一样 —— 10 个 + 100 mB 水 → 100 mB 硫酸（5 秒）。
3. 反面对照：铁粉、火药、圆石**放不进去**（三条路都进不去）。

**数值与口径**：

- 挂的标签是 **`c:dusts/sulfur`**（不是 `c:sulfur`）。理由见 §5 的 ZF169 行：
  三个对端**没有一家**用光秃秃的 `c:sulfur`；用户说的「硫磺」= 硫磺粉 = dust。
- **只挂这一条**；`c:storage_blocks/sulfur` 不挂（我们没有硫块）。
- 判据只有一份：`ModItems.isSulfur(ItemStack)`，酸性反应室三道门全部转调它。

**说明一件我核过、但你可能关心的事**：挂上之后，**加氢脱硫反应室仍然只产出我们自己的硫**
（产出侧没动），而**别的 mod 的硫粉不能**被当成它的产物塞进输出槽 —— 这是有意的。
'''

SEC623_ADD = '''
**ZF169 补的第二个实例（硫）**：同一套做法，但**先查「对端用的是哪条标签」这一步救了命** ——
三家（通用机械 / 沉浸工程 / 机械动力：柴油动力）吃的**都是** `c:dusts/sulfur`，
**没有一家**用光秃秃的 `c:sulfur`。所以「统一标签」挂的是**粉尘**那一条；
只挂 `c:sulfur` 会得到一个谁都不认的空标签（看着做了，其实一点用没有）。
⚠ 顺带把§4.167 那条「挂之前先查有没有反向配方」也走了一遍：能吃这条标签的配方
（Mek 的 enriching / oxidizing / chemical_conversion、IE 的火药/肥料/除草剂）与
能产出它的配方（Mek 的 injecting、IE 的矿石副产、沉浸原油的加氢处理）之间
**没有一条能反向变回硫**，闭环不成立。完整推导见 §5 的 ZF169 行。
'''


def insert_lines(path, anchor_prefix, block, backup_name, label, after_body):
    src = io.open(path, "r", encoding="utf-8", newline="").read()
    if "\r\n" in src:
        print("!! %s 是 CRLF，停手" % path)
        return False
    first = next((x for x in block.split("\n") if x.strip()), "")
    if first and first in src:
        print("!! %s 已经有 %s，拒绝重复插入" % (os.path.basename(path), label))
        return False
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(anchor_prefix)]
    if len(idx) != 1:
        print("!! %s 的锚点 %r 不唯一（%d 处）" % (path, anchor_prefix, len(idx)))
        return False
    os.makedirs(STASH, exist_ok=True)
    bak = os.path.join(STASH, backup_name)
    if not os.path.exists(bak):
        io.open(bak, "w", encoding="utf-8", newline="").write(src)
        print("留底 -> " + bak)
    if after_body:
        j = idx[0] + 1
        while j < len(lines) and not lines[j].startswith("### ") and not lines[j].startswith("## "):
            j += 1
        lines[j:j] = [""] + block.split("\n")
    else:
        lines[idx[0]:idx[0]] = block.split("\n") + [""]
    io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("已插入 %s（%s）" % (label, os.path.basename(path)))
    return True


def main():
    okk = True
    okk &= insert_lines(ARCHIVE, "| ZF165 |", ROW, "开发档案.md.before-zf169", "§5 ZF169 行", False)
    okk &= insert_lines(ARCHIVE, "### 4.175 ", L176, "开发档案.md.before-zf176", "§4.177", True)
    okk &= insert_lines(ARCHIVE, "### ZF165（0.13）", SEC9, "开发档案.md.before-zf9", "§9 ZF169 段", True)
    okk &= insert_lines(ARCHIVE, "### 6.23 ", SEC623_ADD, "开发档案.md.before-zf623", "§6.23 补硫实例", True)
    return 0 if okk else 1


if __name__ == "__main__":
    sys.exit(main())
