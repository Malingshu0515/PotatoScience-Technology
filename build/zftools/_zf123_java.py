# -*- coding: utf-8 -*-
u"""_zf123_java.py —— ZF123：修 JEI 那个"一崩全没"的客户端雷（锚点替换，逐处断言只命中一次）

**病根**（`PotatoSTJeiPlugin`）：
  · `MACHINES` 里 12 台机器，`iconFor()` 的 switch 只有 **11 个 case** ——
    ZF112（0a286b8）加 `lithium_battery_plant` 时**只加了 MACHINES、忘了加 case**
    ⇒ 返回 `ItemStack.EMPTY`；
  · `registerCategories` 拿它去 `gui.createDrawableItemStack(...)` ⇒ JEI 抛
    `IllegalArgumentException: Ingredient is invalid and cannot be used as a drawable ingredient: 0 minecraft:air`；
  · `registerRecipeCatalysts` 再抛一次（`Recipe catalyst must be a valid ingredient`）；
  · JEI 的 `PluginCaller` 捕获后**把整个插件这一次注册的结果全丢掉**
    ⇒ **12 台机器一台的 JEI 页面都没有**（用户看到的"合金炉配方没了"只是他顺手点的那台）。
  时间线（客户端日志）：`2026-09-25-1`（22:24 那场）还绿，`2026-09-25-2`（22:30 那场）起每一场都红
  —— 正好卡在 ZF112 那个 22:19 的提交上。

**三处改**：
  ① 补上 `case "lithium_battery_plant"`（真正的修）；
  ② `registerCategories` / `registerRecipeCatalysts` 各加一道**兜底**：icon 为空就
     **记 ERROR + 跳过这一台**，而不是让 JEI 把**所有**分类一起丢掉
     —— 以后再有人加机器忘了加 case，坏的是那一台，不是整个模组的 JEI；
  ③ 补一句启动横幅（注册了几台 / 有没有被跳过的），让"JEI 到底活没活"在日志里一眼可见。

跑法：
    python build\\zftools\\_zf123_java.py            # 只校验
    python build\\zftools\\_zf123_java.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
P = os.path.join(ROOT, r"src\main\java\com\potatost\mod\client\jei\PotatoSTJeiPlugin.java")

# ① 补 case（放在 ammonia 那行之后、default 之前，与 MACHINES 的顺序一致）
C1_OLD = u'''            case "ammonia_synthesis_chamber" -> new ItemStack(ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_ITEM.get());
            default -> ItemStack.EMPTY;'''
C1_NEW = u'''            case "ammonia_synthesis_chamber" -> new ItemStack(ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_ITEM.get());
            // ⚠ 0.11 ZF123 补：ZF112 把 `lithium_battery_plant` 加进 MACHINES 时**漏了这个 case**
            //   ⇒ 返回 ItemStack.EMPTY ⇒ JEI 抛 "Ingredient is invalid … 0 minecraft:air"
            //   ⇒ **整个插件的分类与配方全被丢弃**（12 台机器一台的 JEI 页面都没有，2026-09-25 22:19 起）。
            case "lithium_battery_plant" -> new ItemStack(ModBlocks.LITHIUM_BATTERY_PLANT_ITEM.get());
            default -> ItemStack.EMPTY;'''

# ②a registerCategories 兜底
C2_OLD = u'''            categories.add(new MachineRecipeCategory(
                    TYPES.get(machine),
                    Component.translatable("block.potato_s_t." + machine),
                    gui.createDrawableItemStack(iconFor(machine)),
                    gui, maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfo));'''
C2_NEW = u'''            // ⚠ 0.11 ZF123 兜底：icon 为空**只跳过这一台**，绝不让 JEI 把整个插件的结果丢掉。
            //   以前这里直接把 ItemStack.EMPTY 交给 JEI ⇒ 它抛异常 ⇒ **所有**机器的 JEI 页面一起消失
            //   （ZF112 漏一个 case 就够整个模组的 JEI 全灭，而且服务端探针一条都查不到 —— 见档案 §4.101）。
            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI SKIPPED '{}': iconFor() 没有这一台的 case（返回了空物品）"
                        + " —— 补 PotatoSTJeiPlugin.iconFor 的 switch，否则这一台在 JEI 里搜不到", machine);
                skipped.add(machine);
                continue;
            }
            categories.add(new MachineRecipeCategory(
                    TYPES.get(machine),
                    Component.translatable("block.potato_s_t." + machine),
                    gui.createDrawableItemStack(icon),
                    gui, maxInItems, maxInFluids, maxOutItems, maxOutFluids, maxInfo));
            served.add(machine);'''

# ②b 声明两个记账表 + 收尾横幅
C3_OLD = u'''        IGuiHelper gui = registration.getJeiHelpers().getGuiHelper();
        List<IRecipeCategory<?>> categories = new ArrayList<>();
        for (String machine : MACHINES) {'''
C3_NEW = u'''        IGuiHelper gui = registration.getJeiHelpers().getGuiHelper();
        List<IRecipeCategory<?>> categories = new ArrayList<>();
        List<String> served = new ArrayList<>();
        List<String> skipped = new ArrayList<>();
        for (String machine : MACHINES) {'''

C4_OLD = u'''        registration.addRecipeCategories(categories.toArray(new IRecipeCategory<?>[0]));
        LOGGER.info("[potato_s_t] JEI: registered {} machine recipe categories {}", MACHINES.size(), MACHINES);'''
C4_NEW = u'''        registration.addRecipeCategories(categories.toArray(new IRecipeCategory<?>[0]));
        if (skipped.isEmpty()) {
            LOGGER.info("[potato_s_t] JEI: registered {} machine recipe categories {}",
                    served.size(), served);
        } else {
            LOGGER.error("[potato_s_t] JEI: {} categories registered, {} SKIPPED {}（见上面每一条的 ERROR）",
                    served.size(), skipped.size(), skipped);
        }'''

# ②c registerRecipeCatalysts 同样的兜底
C5_OLD = u'''        for (String machine : MACHINES) {
            registration.addRecipeCatalyst(iconFor(machine), TYPES.get(machine));
        }'''
C5_NEW = u'''        for (String machine : MACHINES) {
            // ⚠ 0.11 ZF123：同 registerCategories 的兜底 —— 空 icon 会让 JEI 抛
            //   "Recipe catalyst must be a valid ingredient"，一样是**整个插件**一起没。
            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI catalyst SKIPPED '{}'（iconFor 空物品）", machine);
                continue;
            }
            registration.addRecipeCatalyst(icon, TYPES.get(machine));
        }'''

PATCHES = [(C1_OLD, C1_NEW, u"补 lithium_battery_plant 的 case", u'case "lithium_battery_plant"'),
           (C2_OLD, C2_NEW, u"registerCategories 兜底（空 icon 只跳过这一台）", u"JEI SKIPPED '{}'"),
           (C3_OLD, C3_NEW, u"两张记账表", u"List<String> skipped = new ArrayList<>();"),
           (C4_OLD, C4_NEW, u"收尾横幅（跳过谁一眼可见）", u"categories registered, {} SKIPPED"),
           (C5_OLD, C5_NEW, u"registerRecipeCatalysts 兜底", u"JEI catalyst SKIPPED")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    txt = read(P)
    fails, done, out = [], 0, txt
    for old, new, label, marker in PATCHES:
        if marker in out:
            print(u"  [跳过] %-34s（已打过，幂等）" % label)
            done += 1
            continue
        n = out.count(old)
        if n != 1:
            fails.append(u"「%s」的锚点命中 %d 次（应为 1）" % (label, n))
            continue
        out = out.replace(old, new, 1)
        print(u"  [改]   %-34s" % label)
        done += 1
    # 自检：MACHINES 里每一台都必须有 case（修完之后应当为 0）
    import re
    machines = re.findall(r'List\.of\((.*?)\);', out, re.S)[0]
    ids = re.findall(r'"([a-z_]+)"', machines)
    cases = set(re.findall(r'case "([a-z_]+)"', out))
    missing = [m for m in ids if m not in cases]
    print(u"  [自检] MACHINES %d 台；iconFor 覆盖 %d 台；缺 %s"
          % (len(ids), len(ids) - len(missing), missing if missing else u"无"))
    if missing:
        fails.append(u"自检不过：iconFor 还缺 %s" % missing)
    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        write(P, out)
        print(u"\n落盘：%s" % os.path.relpath(P, ROOT))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
