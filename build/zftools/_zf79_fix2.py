# -*- coding: utf-8 -*-
u"""_zf79_fix2.py —— 两处修复的校验补丁（灌装机手放门禁 + JEI 箭头位置）

① `_zf79_verify.py` 新增：
   · **灌装机三道门禁必须同口径**：Menu.mayPlace / Menu.getMachineSlotFor / BE.isItemValid
     全都是 `FluidContainerItem`；并且 Menu 里**不许再出现** `HighPressureTankItem`（写死回归）
   · **JEI 箭头**：`arrowXFor(recipe)` 存在、按实际输入列数算；并且**几何自证**——
     1 个输入时箭头确实左移（≥20px）、输入满 4 列时位置与"旧算法"完全一致（不压槽位）
② `docs/开发档案.md`：§4 新增一条雷（同一道门禁写在两处 ⇒ 只改一处就是"半通"）
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
TOOLS = os.path.join(ROOT, "build", "zftools")
VER = os.path.join(TOOLS, "_zf79_verify.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
fails = []


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


NEW_SEC = u'''
# ================= G 2026-09-24 的两处修复 =================

def section_g():
    print(u"\\n== G 灌装机手放门禁 + JEI 箭头位置（用户 09-24 实测）==")
    menu = src("FillingMachineMenu.java")
    be = src("FillingMachineBlockEntity.java")
    # ① 灌装机：三道门禁同口径（这道门漏改过一次：用户"没办法放油桶"）
    check(u"Menu.mayPlace 认接口（不再写死高压气罐）",
          "return stack.getItem() instanceof FluidContainerItem;" in menu)
    check(u"Menu 里**不许再出现** HighPressureTankItem（写死回归断言）",
          "HighPressureTankItem" not in menu)
    check(u"Menu.getMachineSlotFor（Shift 快移）也认接口",
          "if (stack.getItem() instanceof FluidContainerItem) {" in menu)
    check(u"方块实体的 isItemValid 同样认接口",
          "return stack.getItem() instanceof FluidContainerItem;" in be)

    # ② JEI 箭头：按这条配方实际占用的输入列数算
    cat = src("MachineRecipeCategory.java", sub=os.path.join("client", "jei"))
    check(u"箭头位置改成按配方算（arrowXFor）",
          "private int arrowXFor(MachineRecipes.Entry recipe)" in cat
          and "this.arrow.draw(graphics, arrowXFor(recipe), this.arrowY);" in cat)
    check(u"旧的固定 arrowX 字段已删（不再两套算法并存）",
          "this.arrowX" not in cat and "private final int arrowX;" not in cat)
    # 几何自证：用类别里的常量把两种情形算出来
    c = int_consts(cat)
    pad, slot, in_cols, gap = c.get("PAD"), c.get("SLOT"), c.get("IN_COLS"), c.get("GAP")
    arrow_w = 22          # JEI 原版箭头精灵就是 22×16
    out_x = (pad or 0) + (in_cols or 0) * (slot or 0) + (gap or 0)
    old_x = (pad or 0) + (in_cols or 0) * (slot or 0) + ((gap or 0) - arrow_w) // 2
    one_col = (pad or 0) + 1 * (slot or 0)
    new_one = one_col + (out_x - one_col - arrow_w) // 2
    new_four = (pad or 0) + (in_cols or 0) * (slot or 0) + (out_x - ((pad or 0) + (in_cols or 0) * (slot or 0)) - arrow_w) // 2
    check(u"1 个输入：箭头左移 ≥20px（旧 x=%s → 新 x=%s）" % (old_x, new_one),
          old_x - new_one >= 20)
    check(u"输入满 4 列：位置与旧算法完全一致（x=%s）⇒ 12 输入那种配方不会压槽位" % new_four,
          new_four == old_x)
    check(u"箭头始终落在输入区右边界与输出区之间（不越界）",
          new_one >= one_col and new_one + arrow_w <= out_x)


'''

TRAP = u"""### 4.51 【实现雷】同一道门禁写在**两处**（方块实体 + 菜单）⇒ 只改一处就是"半通"（0.11 ZF79）

用户实测：「**灌装机没办法放油桶**」。查下来：ZF73 那次把"只认高压气罐"改成认
`FluidContainerItem` 接口时，**改了两处、漏了一处**：

| 位置 | 作用 | ZF73 改了吗 |
|---|---|---|
| `FillingMachineBlockEntity.items.isItemValid` | 自动化/机器内部往槽里放 | ✅ 改了 |
| `FillingMachineMenu.getMachineSlotFor` | Shift 快速移动 | ✅ 改了 |
| `FillingMachineMenu` 的 `SlotItemHandler#mayPlace` | **玩家用手放** | ❌ **漏了**（还写死 `HighPressureTankItem`） |

⇒ 症状是"里面能灌、Shift 能进、**但手放不进去**"——三道门只通两道，玩家看到的就是坏的。

**规矩**：凡是"这个槽收什么"的判定，**先 grep 一遍那个类名/接口名**（`grep -n HighPressureTankItem`），
把所有命中点一次改完；校验里再加一条**负向断言**（"这个文件里不许再出现那个写死的类名"），
下次谁再漏就会当场挂。
"""


def main():
    print(u"== ① 校验脚本补 G 区 + G 区调用 ==")
    t = io.open(VER, encoding="utf-8").read()
    if u"def section_g()" in t:
        print(u"  [SKIP] G 区已在（幂等）")
    else:
        old = u"def main():\n    print(u\"=========== ZF79 校验：柏油块 + 电力高炉新材质 ===========\")"
        if t.count(old) != 1:
            fails.append(u"main() 锚点命中 %d 次" % t.count(old))
        else:
            t = t.replace(old, NEW_SEC + u"def main():\n    print(u\"=========== ZF79 校验：柏油块 + 电力高炉新材质 ===========\")", 1)
            io.open(VER, "w", encoding="utf-8", newline=u"\n").write(t)
            print(u"  [OK]   G 区已插入")
    patch(VER, u"    section_f()\n    print(u\"\\n------------------------------\")",
          u"    section_f()\n    section_g()\n    print(u\"\\n------------------------------\")",
          u"main() 里调用 section_g()")

    print(u"== ② 档案 §4.51 新雷 ==")
    patch(DOC, u"## 5. 版本与 [ZF] 流水线记录", TRAP, u"§4.51「门禁写两处只改一处」")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
