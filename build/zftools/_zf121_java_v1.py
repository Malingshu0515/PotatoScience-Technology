# -*- coding: utf-8 -*-
u"""_zf121_java.py —— ZF121 的五处 Java 改动（锚点替换，逐处断言"原文只出现一次"）

用户原话：「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+钻石+
2下界合金碎片+1红石粉 14500Fe/t 产出1振金」

改五件事：
  ① `AlloySmelterRecipes`：第四条配方（5 输入 + 4 消耗品 → 1 振金锭，600 tick、14500 FE/t）
     + `MAX_ENERGY_PER_TICK` 12000 → 14500（静态守卫读的就是它）。
  ② `AlloySmelterBlockEntity`：`CONSUME_COUNT` 2 → 4（新增两槽排在序号 10/11，老存档不丢东西）。
  ③ `AlloySmelterMenu`：4 个消耗槽摆成 2×2，**并撤掉 ZF49 留下的 mayPlace=false** ——
     ZF111 放开了方块实体那层，菜单这层还拦着 ⇒ 手放不进任何东西、配方是条死路。
  ④ `MachineRecipes` / `PotatoST` / `AlloySmelterScreen`：三处口径注释跟上（免得下次读代码被误导）。

跑法：
    python build\\zftools\\_zf121_java.py            # 只校验（不动盘）
    python build\\zftools\\_zf121_java.py --write    # 打补丁
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")

RECIPES = os.path.join(JAVA, "AlloySmelterRecipes.java")
BE = os.path.join(JAVA, "AlloySmelterBlockEntity.java")
MENU = os.path.join(JAVA, "AlloySmelterMenu.java")
MREC = os.path.join(JAVA, "MachineRecipes.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
SCREEN = os.path.join(JAVA, "client", "AlloySmelterScreen.java")

# ============================================================
#  ① AlloySmelterRecipes.java
# ============================================================
R1_OLD = u'''     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 12_000;'''
R1_NEW = u'''     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     *
     * <p><b>0.11 ZF121：最贵的变成振金那条（14500 FE/t）</b> —— 用户原话
     * 「振金合金冶炼炉配方；…1红石粉 14500Fe/t 产出1振金」。
     * 12000 → 14500 之后仍然 {@code 14500 ≤ 32768}（储能），静态守卫不会吭声。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 14_500;'''

R2_OLD = u'''        table = List.copyOf(list);'''
R2_NEW = u'''        // ④ 1 硬质钛合金 + 8 热力金属 + 2 高碳钢 + 3 银锭 + 12 金锭，
        //    再消耗 1 粗振金 + 1 钻石 + 2 下界合金碎片 + 1 红石粉 → 1 振金锭（0.11 ZF121，用户口述）
        //    用户原话：「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭
        //              粗振金+钻石+2下界合金碎片+1红石粉 14500Fe/t 产出1振金」
        //    ⚠ 时长用户**没给** ⇒ 沿用本机规格 30 秒（600 tick）⇒ 一件 14500 × 600 = 8,700,000 FE。
        //    金锭走原版/NeoForge 的 c:ingots/gold（与 ZF111 的 netherite/copper 同一条口径；
        //    解包核过：neoforge-21.1.235 的 data/c/tags/item/ingots/ 里有 gold.json）。
        //    ⚠ 硬质钛合金与热力金属**本来都不在 #c:ingots 里**（输入槽只收这个标签 ⇒ 放不进去、
        //      配方永远开不了工）⇒ 本轮把这两样登记进了 GenCommonTags.py 的 ALLOYS 表。
        //    ⚠ 硬质钛合金挂的是 c:ingots/hard_titanium_alloy，**没有**并进 c:ingots/titanium_alloy ——
        //      那格是配方②的输入（轻质钛合金），并进去会让②变成"硬质钛合金 → 硬质钛合金"的复制漏洞。
        list.add(new Smelt(
                List.of(new Need(ingot("hard_titanium_alloy"), 1),
                        new Need(ingot("thermal_metal"), 8),
                        new Need(ingot("steel"), 2),
                        new Need(ingot("silver"), 3),
                        new Need(ingot("gold"), 12)),
                List.of(new Consume(ModItems.RAW_VIBRANIUM.get(), 1),
                        new Consume(Items.DIAMOND, 1),
                        new Consume(Items.NETHERITE_SCRAP, 2),
                        new Consume(Items.REDSTONE, 1)),
                new ItemStack(ModItems.VIBRANIUM_INGOT.get(), 1),
                DURATION_TICKS, MAX_ENERGY_PER_TICK));

        table = List.copyOf(list);'''

R3_OLD = u''' * <b>12000 × 600 = 7,200,000 FE</b>。这个数是"按本机规格补的"，不是用户说的 ——
 * 要改就改这条配方最后一个参数（或者 {@link #DURATION_TICKS}）。</p>
 */'''
R3_NEW = u''' * <b>12000 × 600 = 7,200,000 FE</b>。这个数是"按本机规格补的"，不是用户说的 ——
 * 要改就改这条配方最后一个参数（或者 {@link #DURATION_TICKS}）。</p>
 *
 * <p><b>0.11 ZF121 新增第四条配方（振金锭）</b>。用户原话：
 * 「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+钻石+
 * 2下界合金碎片+1红石粉 14500Fe/t 产出1振金」。这条同时打破本机的两个上限：</p>
 * <ul>
 *   <li><b>消耗品第一次要 4 样</b>（粗振金 / 钻石 / 下界合金碎片 ×2 / 红石粉）⇒
 *       消耗槽从 2 个扩到 4 个（见 {@code AlloySmelterBlockEntity.CONSUME_COUNT}）；</li>
 *   <li><b>每 tick 耗电第一次超过 12000</b>（14500）⇒ {@link #MAX_ENERGY_PER_TICK} 跟着改，
 *       否则 ZF42 那条静态守卫会报"最贵的一条跑不起来"。</li>
 * </ul>
 *
 * <p>⚠ <b>时长用户没给</b>：沿用本机规格 30 秒（600 tick）⇒ 一件
 * <b>14500 × 600 = 8,700,000 FE</b>。储能 32768 只够 2.26 秒 ⇒ 必须持续供上 14500 FE/t。</p>
 */'''

# ============================================================
#  ② AlloySmelterBlockEntity.java
# ============================================================
B1_OLD = u''' * <b>5 个输入槽</b>（只能放"锭"，按 {@code c:ingots} 标签认）、<b>3 个输出槽</b>、
 * <b>2 个消耗槽</b>（用户原话「目前放不了东西 以后出类似于沉浸电弧炉石墨电极的东西」）。</p>'''
B1_NEW = u''' * <b>5 个输入槽</b>（只能放"锭"，按 {@code c:ingots} 标签认）、<b>3 个输出槽</b>、
 * <b>4 个消耗槽</b>（用户原话「目前放不了东西 以后出类似于沉浸电弧炉石墨电极的东西」；
 * <b>0.11 ZF121 从 2 个扩到 4 个</b>——振金那条配方点名要消耗 4 样东西，2 个格子装不下，
 * 见 {@link #CONSUME_COUNT}）。</p>'''

B2_OLD = u'''     * {@code 12000 ≤ 32768} ✓（0.11 ZF111 起，最贵的是星璨钢那条）。'''
B2_NEW = u'''     * {@code 14500 ≤ 32768} ✓（0.11 ZF121 起，最贵的是振金那条；ZF111 那会儿是星璨钢的 12000）。'''

B3_OLD = u'''    /** 消耗槽（0.11 ZF111 起放开）：放配方点名要消耗的东西（深层钴矿石 / 末影水晶）。 */
    public static final int CONSUME_FIRST = OUTPUT_FIRST + OUTPUT_COUNT;
    public static final int CONSUME_COUNT = 2;
    public static final int SLOT_COUNT = CONSUME_FIRST + CONSUME_COUNT;   // = 10'''
B3_NEW = u'''    /**
     * 消耗槽（0.11 ZF111 起放开）：放配方点名要消耗的东西
     * （星璨钢那条是深层钴矿石 / 末影水晶；振金那条是粗振金 / 钻石 / 下界合金碎片 ×2 / 红石粉）。
     *
     * <p><b>0.11 ZF121：2 → 4</b>。用户给的振金配方要点名消耗 <b>4 样</b>东西，2 个格子装不下。
     * 新增的两槽排在序号 10 / 11 ⇒ <b>老存档里已经放进消耗槽的东西一个都不会丢</b>
     * （序号 8 / 9 没动，界面里那两格也还在原地，新增的两格摆在它们上面一行）。</p>
     */
    public static final int CONSUME_FIRST = OUTPUT_FIRST + OUTPUT_COUNT;
    public static final int CONSUME_COUNT = 4;
    public static final int SLOT_COUNT = CONSUME_FIRST + CONSUME_COUNT;   // = 12'''

# ============================================================
#  ③ AlloySmelterMenu.java
# ============================================================
M1_OLD = u'''/**
 * 合金冶炼炉菜单（0.10 ZF49）：<b>5 输入 + 3 输出 + 2 消耗槽</b>，界面 176×186。
 *
 * <p>用户原话：「五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽（目前放不了东西）」。
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，
 * 这里只负责摆位置；消耗槽<b>也照画出来</b>（让玩家看见那儿以后会有东西），但同样放不进去。</p>
 */'''
M1_NEW = u'''/**
 * 合金冶炼炉菜单（0.10 ZF49）：<b>5 输入 + 3 输出 + 4 消耗槽</b>，界面 176×186。
 *
 * <p>用户原话：「五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽（目前放不了东西）」。
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，这里只负责摆位置。</p>
 *
 * <p><b>0.11 ZF121 两件事</b>：</p>
 * <ol>
 *   <li><b>消耗槽 2 → 4，摆成 2×2</b>（振金那条配方要点名 4 样消耗品）；</li>
 *   <li><b>撤掉 mayPlace = false</b> —— 那是 ZF49 的"目前放不了东西"。ZF111 已经把方块实体那层
 *       放开成"某条配方真的会消耗它才收"，<b>可菜单这层的恒 false 还留着</b> ⇒ 手动一个都放不进去
 *       （只有漏斗/管道塞得进），而 ZF111 与 ZF121 两条配方都要求消耗槽里有东西 ——
 *       那是一条死路。现在交给 {@code machineInventory.isItemValid} 判（没激活时它照样返回 false）。</li>
 * </ol>'''

M2_OLD = u'''    /** 2 个消耗槽：右下角，与输出错开 */
    public static final int CONSUME_X = 116;
    public static final int CONSUME_Y = 62;'''
M2_NEW = u'''    /**
     * 4 个消耗槽：右下角摆成 2×2（0.11 ZF121 从 2 个扩到 4 个）。
     *
     * <p><b>前两个仍然在原地</b>（x=116 / 134、y=62），新增的两个摆在<b>上面一行</b>（y=44）——
     * 这样老存档里已经放进消耗槽的东西在界面里<b>一个像素都不动</b>（槽位序号也没变）。
     * 右边界 134+18 = 152 正好接上能量条的左沿（{@code AlloySmelterScreen.ENERGY_X = 152}）。</p>
     */
    public static final int CONSUME_X = 116;
    public static final int CONSUME_Y = 62;
    public static final int CONSUME_Y2 = 44;
    /** 第 k 个消耗槽的坐标：0/1 是原来那两格（下排），2/3 是新增的（上排）。 */
    private static final int[][] CONSUME_POS = {
            {CONSUME_X, CONSUME_Y}, {CONSUME_X + 18, CONSUME_Y},
            {CONSUME_X, CONSUME_Y2}, {CONSUME_X + 18, CONSUME_Y2}};'''

M3_OLD = u'''        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;       // 用户：「目前放不了东西」——以后放石墨电极
                }
            });
        }'''
M3_NEW = u'''        // 0.11 ZF121：这 4 槽**不再拦** —— 能不能放由方块实体的 isItemValid 说了算
        //（"某条配方真的会消耗它"才收，没激活时一律 false）。ZF49 那句"目前放不了东西"
        // 从 ZF111 放开方块实体那一刻起就已经名不副实了，这里把它撤掉。
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_POS[k][0], CONSUME_POS[k][1]));
        }'''

M4_OLD = u'''            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
        }
        return -1;
    }'''
M4_NEW = u'''            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
        }
        // 0.11 ZF121：消耗品也走 shift 点击 —— 能不能放交给 isItemValid（配方点名的才收）。
        // 不认这个的话，玩家 shift 点一下钻石只会被丢回背包，得一个个手动拖。
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            int slot = AlloySmelterBlockEntity.CONSUME_FIRST + k;
            if (!this.machineInventory.isItemValid(slot, stack)) {
                continue;
            }
            ItemStack cur = this.machineInventory.getStackInSlot(slot);
            if (cur.isEmpty()) {
                return slot;
            }
            if (ItemStack.isSameItemSameComponents(cur, stack) && cur.getCount() < cur.getMaxStackSize()) {
                return slot;
            }
        }
        return -1;
    }'''

# ============================================================
#  ④ 口径注释
# ============================================================
N1_OLD = u'''            // 0.11 ZF111：消耗品（深层钴矿石 / 末影水晶）也画出来 —— 它们要放进机器的 2 个消耗槽。'''
N1_NEW = u'''            // 0.11 ZF111：消耗品（深层钴矿石 / 末影水晶）也画出来 —— 它们要放进机器的消耗槽。
            // 0.11 ZF121：消耗槽 2 → 4，振金那条一次画 **9 个输入**（5 锭 + 4 消耗品）⇒
            //   输入区按 IN_COLS=4 折成 3 行。分类高度是**按最坏的一条配方算的**，会自动长高，
            //   不用手改尺寸（那正是 ZF20 定下的规矩）。'''

N2_OLD = u'''        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物）'''
N2_NEW = u'''        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 4 消耗槽（ZF121 起；自动化可投锭、可取产物）'''

N3_OLD = u''' * <p>5 输入 + 3 输出 + 2 消耗槽（画出来但放不进东西），右侧一根能量条，'''
N3_NEW = u''' * <p>5 输入 + 3 输出 + 4 消耗槽（0.11 ZF121 起；能放"某条配方点名要消耗"的东西），右侧一根能量条，'''

PATCHES = [("AlloySmelterRecipes.java", RECIPES, R1_OLD, R1_NEW, u"MAX_ENERGY_PER_TICK 12000 → 14500"),
           ("AlloySmelterRecipes.java", RECIPES, R2_OLD, R2_NEW, u"第四条配方（振金锭）"),
           ("AlloySmelterRecipes.java", RECIPES, R3_OLD, R3_NEW, u"类注释补 ZF121 段"),
           ("AlloySmelterBlockEntity.java", BE, B1_OLD, B1_NEW, u"类注释 2 消耗槽 → 4"),
           ("AlloySmelterBlockEntity.java", BE, B2_OLD, B2_NEW, u"静态守卫注释 12000 → 14500"),
           ("AlloySmelterBlockEntity.java", BE, B3_OLD, B3_NEW, u"CONSUME_COUNT 2 → 4（序号 10/11）"),
           ("AlloySmelterMenu.java", MENU, M1_OLD, M1_NEW, u"菜单类注释"),
           ("AlloySmelterMenu.java", MENU, M2_OLD, M2_NEW, u"4 个消耗槽 2×2 坐标"),
           ("AlloySmelterMenu.java", MENU, M3_OLD, M3_NEW, u"撤掉 mayPlace = false"),
           ("AlloySmelterMenu.java", MENU, M4_OLD, M4_NEW, u"消耗品也能 shift 点击"),
           ("MachineRecipes.java", MREC, N1_OLD, N1_NEW, u"JEI 那条注释"),
           ("PotatoST.java", MAIN, N2_OLD, N2_NEW, u"㉗ 能力注册注释"),
           ("AlloySmelterScreen.java", SCREEN, N3_OLD, N3_NEW, u"界面类注释")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done = [], 0
    cache = {}
    for name, path, old, new, label in PATCHES:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        if new in txt and old not in txt:
            print(u"  [跳过] %-28s %s（已打过，幂等）" % (name, label))
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点「%s」匹配到 %d 次（应为 1）" % (name, label, n))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-28s %s" % (name, label))
        done += 1
    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for path, txt in cache.items():
            write(path, txt)
        print(u"\n落盘：%d 个文件" % len(cache))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
