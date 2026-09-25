# -*- coding: utf-8 -*-
u"""_zf79_fix3.py —— 收尾三件

① 校验脚本 G 区再加一条**公式级**断言：`arrowXFor` 里的左边界必须用 `usedCols`
   （只加"函数存在 + 几何自算"是不够的 —— 那把 `usedCols` 改成 `IN_COLS` 的刀就砍不到）
② 反证脚本加两把刀（K10 灌装机手放门禁改回写死、K11 箭头左边界改回写死 4 列）
③ 文档：§5 的 ZF79 行补这两处修复、§9 补一条"用户实测反馈"（哈希占位 __NEWSHA__）

⚠ 规矩（本文件自己踩过）：中文串里**只用「」**，绝不写 ASCII 双引号（§4.6 那条老雷）。
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
FAL = os.path.join(TOOLS, "_zf78_falsify.py")
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


ROW_OLD = u"⑧ 发布见 §9 | 见 §6.21 / §9 |"
ROW_NEW = (
    u"⑧ **发布后又按你 09-24 的两条实测反馈修了两处**（都是真 bug）："
    u"㈠「**灌装机没办法放油桶**」—— ZF73 把「槽里收什么」从写死高压气罐改成认 "
    u"`FluidContainerItem` 时**改了两处、漏了一处**（方块实体 ✅ / Shift 快移 ✅ / "
    u"**手放的 `mayPlace` ❌**）⇒ 症状正是「里面能灌、Shift 能进、手放不进去」；"
    u"已补齐并加了**负向断言**（菜单里不许再出现 `HighPressureTankItem`），雷记进 §4.51；"
    u"㈡「**液压机所有配方的箭头稍微左移一点**」—— 箭头原先固定居中于「4 列输入区与输出区之间」"
    u"那段空隙，而液压机每条配方只有 1 个输入 ⇒ 左边空 60px、箭头贴着输出槽；改成"
    u"**按这条配方实际占用的输入列数**算（1 个输入时落在输入与输出正中间、左移约 30px；"
    u"输入铺满 4 列时位置与原先**一模一样** ⇒ 12 输入那种配方不会压槽位）。⑨ 发布见 §9 | 见 §6.21 / §9 |"
)

SEC_OLD = u"- [ ] ZF79 说明：**柏油块除了建筑暂时没别的用途**"
SEC_NEW = u"""- [x] **ZF79 修复（你 2026-09-24 的两条实测反馈，都是真 bug）**（成品 `__NEWSHA__`；同版本重打包
      ⇒ 上一版 `71ffc245…` 作废）：
      ① **灌装机放不进油桶** —— ZF73 那次「槽里收什么」的判定有三道门，只改了两道：
      方块实体的 `isItemValid` ✅、Shift 快移 `getMachineSlotFor` ✅，而**玩家用手放的
      `SlotItemHandler#mayPlace` 漏了**（还写死 `HighPressureTankItem`）⇒ 症状是
      「机器内部能灌、Shift 能塞、**手放不进去**」。已改成一律认 `FluidContainerItem`，
      并加了一条负向断言（菜单里再出现那个写死的类名就当场挂）；雷记进 §4.51。
      ② **JEI 箭头位置** —— 箭头原先固定居中于「4 列输入区与输出区之间那段空隙」，
      可液压机每条配方只有 1 个输入 ⇒ 左边空出 60px、箭头却紧贴输出槽（就是你那截图）。
      改成**按这条配方实际占用的输入列数**算：1 个输入 = 落在输入与输出正中间（左移约 30px），
      输入铺满 4 列 = 与原先**逐像素相同**（所以 12 输入那种大配方不会压到槽位）。
      ⚠ 这个类别是**八台机器共用**的 ⇒ 别的机器上「输入少于 4 列」的配方也会一起受益（位置更居中）。
- [ ] ZF79 说明：**柏油块除了建筑暂时没别的用途**"""


def main():
    print(u"== ① 校验补「公式级」断言 ==")
    patch(VER,
          u'''    check(u"1 个输入：箭头左移 ≥20px（旧 x=%s → 新 x=%s）" % (old_x, new_one),''',
          u'''    check(u"左边界用的是**实际占用的列数**（不是写死 IN_COLS）",
          "int left = PAD + usedCols * SLOT;" in cat
          and "int usedCols = Math.max(1, Math.min(recipe.itemIn().size(), IN_COLS));" in cat)
    check(u"1 个输入：箭头左移 ≥20px（旧 x=%s → 新 x=%s）" % (old_x, new_one),''',
          u"G 区补公式级断言")

    print(u"== ② 反证加两把刀 ==")
    patch(FAL,
          u'''    (u"K9 液压机不再检查「数量够不够」",''',
          u'''    (u"K10 灌装机手放门禁改回写死高压气罐",
     os.path.join(SRC, "FillingMachineMenu.java"),
     u"                    return stack.getItem() instanceof FluidContainerItem;",
     u"                    return stack.getItem() instanceof HighPressureTankItem;"),
    (u"K11 JEI 箭头的左边界改回写死 4 列",
     os.path.join(SRC, "client", "jei", "MachineRecipeCategory.java"),
     u"        int usedCols = Math.max(1, Math.min(recipe.itemIn().size(), IN_COLS));",
     u"        int usedCols = IN_COLS;"),
    (u"K9 液压机不再检查「数量够不够」",''',
          u"K10/K11 两把刀")

    print(u"== ③ 文档 ==")
    patch(DOC, ROW_OLD, ROW_NEW, u"§5 行补两处修复")
    patch(DOC, SEC_OLD, SEC_NEW, u"§9 补两条修复记录")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
