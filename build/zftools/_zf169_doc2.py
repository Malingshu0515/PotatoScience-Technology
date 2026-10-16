#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF169 交接页记账：往 docs/多会话协作交接.md 插入
   ① §5.3.4（硫 / 硫磺粉统一标签这一轮的交接）
   ② §6 的第 38 条
   ③ §1 活体数字表加一行
一律按行锚点插入；写前留底到 build/tmp/zf169/。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOC = r"E:\PotatoST\PotatoSTneoforge1.21.1\docs\多会话协作交接.md"
STASH = r"E:\PotatoST\PotatoSTneoforge1.21.1\build\tmp\zf169"

SEC = '''### 5.3.4 ZF169：硫 / 硫磺粉统一到 `#c:dusts/sulfur` —— 一个"先查对端用哪条标签"的例子

用户原话：「硫和别的mod硫磺统一标签 酸性反应室也认别的mod的硫磺」。

**挂的是 `c:dusts/sulfur`，不是 `c:sulfur`**（这一条是本轮最值钱的发现）：
盘上三个对端逐条取证 —— 通用机械 `data/c/tags/item/dusts/sulfur.json` → `mekanism:dust_sulfur`；
沉浸工程同名文件 → `immersiveengineering:dust_sulfur`；
机械动力：柴油动力的除草剂配方、沉浸工程的火药/肥料/除草剂三条配方，吃的也都是
`{"tag": "c:dusts/sulfur"}`。**三家没有一家用光秃秃的 `c:sulfur`** ——
只挂那一条会得到一个"谁都不认"的空标签，**看着做了、其实一点用没有**。
（用户说的「硫磺」在这里就是"硫磺粉"= dust。）

**三道门禁只留一份判据**（§4.51）：`ModItems.SULFUR_TAG` + `ModItems.isSulfur(ItemStack)`，
酸性反应室的**方块实体 `isItemValid` / 菜单槽 `mayPlace` / Shift 快移 `getMachineSlotFor`**
三处全部转调它。⚠ **产出侧故意不动**：加氢脱硫反应室仍然只产出我们自己的硫，
输出槽判定照旧写死我方物品（常驻门 B3 把这一条显式放行）——别人的硫粉不该能被塞进输出槽。

**给别人接手时的三条提醒**：

1. 谁要再挂 `c:` 标签，**先做两件事**：① 把对端 jar 里**真正被引用的那个标签名**查出来
   （别照自己的直觉起名，`c:sulfur` vs `c:dusts/sulfur` 就是这么差出来的）；
   ② 走一遍 §4.167（挂之前先查有没有"反向配方"把产物变回原料）。
   本轮逐条核过**没有闭环**：能吃这条标签的是 Mek 的 enriching/oxidizing/chemical_conversion
   与 IE 的火药/肥料/除草剂；能产出它的只有 Mek 的 injecting、IE 的矿石副产、
   沉浸原油的加氢处理 —— 没有一条能把火药、二氧化硫或硫酸变回硫。
2. **父标签 `#c:dusts` 里我们写的是 `#c:dusts/sulfur`（子标签引用）**，而原来那三条
   （carbon / iron_powder / titanium_powder）写的是具体物品 id。两种写法在本工程里
   都能用（`TagLoader` 会解析引用、不会自引用死循环），保持现状即可；门 A2 盯着
   "原来那三条一个都不能少"。
3. **五份 lang 一个字节没改**：硫那两句界面文案本来就是通用说法（「硫数量不够（要 10 个）」），
   换成别家的硫粉也照样贴切 ⇒ 翻译线那些键数门一份都不用动。
'''

ITEM = '''38. **ZF169 的账（0.13：硫 / 硫磺粉统一到 `#c:dusts/sulfur`，酸性反应室认别家的硫磺）**：
    ① 改动只有 3 个 java + 1 个新数据文件 + 1 行父标签（全是加行），逐条见档案 §5 的 ZF169 行；
    两条新雷见 **§4.177**（`RecipeManager#byKey` 收的是 `ResourceLocation` 不是 `ResourceKey`；
    "尺子坏了"会把整段判据变成废纸）与 §4.167（挂标签前先查反向配方，本轮核过没有闭环）。
    ② **真服务端探针 `Zf169Check` 28/0**（把沉浸工程 12.4.2 + 通用机械 10.7.19 拷进
    `run/server/mods` 跑、跑完删掉；两份都已移回 `release/` 与 `libs/`）：
    `#c:dusts/sulfur` 成员实测 = `[immersiveengineering:dust_sulfur, mekanism:dust_sulfur,
    potato_s_t:sulfur]`（三家同一条）；最硬的一条是拿 IE 真配方的**成分对象**直接
    `Ingredient.test(我们的硫)` = true。
    ③ **常驻门 `_zf169_gate.py` 27/0**；**五份 lang 一个字节没改**。
    ④ ⚠ **本轮没重打成品**（与 ZF165 同一批欠账）。
'''

ROW = ("| ZF169 新增（**未打包**） | 新文件 `data/c/tags/item/dusts/sulfur.json`；"
       "`data/c/tags/item/dusts.json` +1 行；`ModItems` 加 `SULFUR_TAG` / `isSulfur`；"
       "酸性反应室 3 个文件把写死的物品比较改成转调 `isSulfur`。**五份 lang 未动** |")


def ins(anchor, block, backup, label, after_body):
    src = io.open(DOC, "r", encoding="utf-8", newline="").read()
    if "\r\n" in src:
        print("!! 交接页是 CRLF，停手")
        return False
    first = next((x for x in block.split("\n") if x.strip()), "")
    if first and first in src:
        print("!! 已经有 %s，拒绝重复插入" % label)
        return False
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(anchor)]
    if len(idx) != 1:
        print("!! 锚点 %r 不唯一（%d 处）" % (anchor, len(idx)))
        return False
    os.makedirs(STASH, exist_ok=True)
    bak = os.path.join(STASH, backup)
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
    io.open(DOC, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("已插入 %s" % label)
    return True


def main():
    okk = True
    okk &= ins("## 6. 我这边欠的账", SEC, "交接.md.before-zf169", "§5.3.4", False)
    okk &= ins("37. **ZF165 的账", ITEM, "交接.md.before-zf169item", "§6 第 38 条", True)
    okk &= ins("| ZF165 新增", ROW, "交接.md.before-zf169row", "§1 活体数字行", False)
    return 0 if okk else 1


if __name__ == "__main__":
    sys.exit(main())
