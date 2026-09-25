# -*- coding: utf-8 -*-
r"""_zf106_docs4.py —— ZF106 补记之四：8 张盔甲配方（逐格照抄原版铁套）

用户原话：「钛合金套和星璨套配方加上 套用原版合成配方（铁合金用轻质钛合金）星辰套就用星璨钢」
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

A = u"**第三次跟\"活体数字\"**：并行的另一条线本轮又给四语言加了 **48 个成就键**（350 → **398**），\n"
N = u"""**⚠ 用户第四条：两套盔甲的合成配方（同日）**

原话：「钛合金套和星璨套配方加上 套用原版合成配方（铁合金用轻质钛合金）星辰套就用星璨钢」

- [x] **图纸逐格照抄原版铁套**（不是自己设计的）。原版那四张从 `client.jar` 的
      `data/minecraft/recipe/iron_*.json` **现场抠**（不靠记忆）：
      头盔 `XXX / X X`、胸甲 `X X / XXX / XXX`、护腿 `XXX / X X / X X`、靴子 `X X / X X`，
      `category = equipment`、单字母 `X`、`count = 1`。
- [x] **材料**（用户点名的是**具体物品**，所以用精确 id 而不是 `#c:ingots/*` 标签）：
      钛合金套 → `potato_s_t:light_titanium_alloy`；星璨钢套 → `potato_s_t:star_steel_ingot`。
- [x] **进了生成器** `_zf45_recipes.py`（+8 条，表从 22 → **30** 条）⇒ 以后改图纸改那里再
      `--write`，顺手拿到"每格字符都在 key 里 / key 无冗余 / id 真实存在"的机械核对。
      盘上定形配方总数 43 → **51**。
- [x] **新常驻门** `_zf106_recipes_check.py`（**81 条断言**）：逐格对照原版 / 材料 / 不许残留
      `minecraft:iron_ingot` / 不许用标签 / result 与 count / 生成器里有条目 / 盘上总数。
      **反证刀**：把星璨钢胸甲的材料换成铁锭 ⇒ 当场两条 FAIL，还原后回全绿。
- [x] 往轮 8 份脚本里的"定形配方总数"锚点跟到 **51**（`_zf106_retarget2.py`）。

**⚠ 又修了一个"取证范围写窄"的假 FAIL**

`_zf45_recipes.py` 的 `mod_ids()` 只扫 `ModItems.java` + `ModBlocks.java` 两个文件 ——
而 0.11 起「**同一个 `DeferredRegister` 可以跨类写**」成了本工程的惯例
（`PotatoSTOres` 先例、`ModArmorItems` 把 9 个物品注册进 `ModItems.ITEMS`）。
⇒ 它把**已经注册好的 id** 判成"不存在"，本轮一上来就报了 **12 条假 FAIL**。
修法：名单加 `ModArmorItems.java` + `PotatoSTOres.java`（抽查到的 id 从 85 → **94** 个）。
**教训**：这类"扫源码找注册名"的探针，名单要跟着"谁在注册东西"一起涨 ——
与 §4.71 / §4.76 同源：**取证范围本身就是判据的一部分**。

**第三次跟"活体数字"**：并行的另一条线本轮又给四语言加了 **48 个成就键**（350 → **398**），
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
