# -*- coding: utf-8 -*-
u"""_zf121_java.py —— ZF121 的 Java 改动（**用户改口后的最终版**，锚点替换 + 逐处断言）

用户原话（第一版）：「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭
                    粗振金+钻石+2下界合金碎片+1红石粉 14500Fe/t 产出1振金」

用户原话（**改口·最终**）：「对不起刚才忘了合金炉的限制 这是新振金合金冶炼炉配方；
                    1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片
                    14500Fe/t 产出1振金」

> 差别：消耗品从 **4 样**（粗振金 / 钻石 / 下界合金碎片 / 红石粉）收窄成 **2 样**
> （粗振金 ×1 + 下界合金碎片 ×2）—— 正好装进本机**原有的 2 个消耗槽**。
> 我按第一版已经把消耗槽扩到 4 个（补丁存档在 `_zf121_java_v1.py`），用户随即自己改口
> ⇒ **本轮把槽位改动整个撤掉**，机器规格与 ZF49/ZF111 一模一样。

最终改六件事（`PotatoST.java` 本轮**不动**，但它照样在改前件里 —— §4.94 连着两轮漏抄过它）：
  ① `AlloySmelterRecipes`：第四条配方（5 输入 + 2 消耗品 → 1 振金锭，600 tick、14500 FE/t）
     + `MAX_ENERGY_PER_TICK` 12000 → 14500（ZF42 那条静态守卫读的就是它）。
  ② `AlloySmelterBlockEntity`：只改**注释**（槽位数一个都没动）+ 守卫注释 12000 → 14500。
  ③ `AlloySmelterMenu`：**撤掉 ZF49 留下的 consume 槽 mayPlace = false** —— ZF111 已经把
     方块实体那层放开成"配方点名的才收"，菜单这层还恒 false ⇒ 手动一个都放不进去
     （只有漏斗/管道塞得进），而 ZF111 与本轮两条配方都要求消耗槽里有东西 —— 那是死路。
     顺带让消耗品也能 shift 点击。
  ④ `MachineRecipes` / `AlloySmelterScreen`：两处口径注释跟上。

跑法：
    python build\\zftools\\_zf121_java.py --proof     # 反推证明：当前盘 = 改前件 + v1（不改盘）
    python build\\zftools\\_zf121_java.py --write     # 先还原到改前件，再打最终补丁
    python build\\zftools\\_zf121_java.py             # 只校验锚点（不动盘）
"""
import hashlib
import importlib.util
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
BK = r"C:\PotatoST救援\zf121_pre"
V1 = os.path.join(TOOLS, "_zf121_java_v1.py")

RECIPES = os.path.join(JAVA, "AlloySmelterRecipes.java")
BE = os.path.join(JAVA, "AlloySmelterBlockEntity.java")
MENU = os.path.join(JAVA, "AlloySmelterMenu.java")
MREC = os.path.join(JAVA, "MachineRecipes.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
SCREEN = os.path.join(JAVA, "client", "AlloySmelterScreen.java")

PATCHED = [RECIPES, BE, MENU, MREC, MAIN, SCREEN]
REL = [os.path.relpath(p, ROOT) for p in PATCHED]

# ============================================================
#  ① AlloySmelterRecipes.java
# ============================================================
R1_OLD = u'''     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 12_000;'''
R1_NEW = u'''     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     *
     * <p><b>0.11 ZF121：12000 → 14500</b>（用户原话「…粗振金+2下界合金碎片 14500Fe/t 产出1振金」），
     * 仍然 {@code 14500 ≤ 32768}（储能），静态守卫不会吭声。</p>
     *
     * <p>⚠⚠ <b>这一轮被抓到的一个真雷（探针当场红）</b>：ZF111 写星璨钢那条时，
     * 每 tick 耗电用的是<b>这个常量</b>（当时它正好等于 12000）—— 而它是"全表最贵那条"的意思，
     * 会随新配方长大。ZF121 把它抬到 14500 之后，<b>星璨钢那条也偷偷从 12000 变成了 14500</b>
     * （用户 ZF111 给的是 12000）⇒ 本轮把两条数各自拆成独立常量：</p>
     * <ul>
     *   <li>{@link #STAR_STEEL_ENERGY_PER_TICK}（12000，ZF111 用户给的数）；</li>
     *   <li>{@link #VIBRANIUM_ENERGY_PER_TICK}（14500，ZF121 用户给的数）。</li>
     * </ul>
     * <p>规矩：<b>配方表不许引用 {@code MAX_ENERGY_PER_TICK}</b> —— 它只是给 static 守卫读的
     * "全表最大值"，谁引用它，谁就会在下一个人加配方时被静默改数（见档案 §4.96）。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 14_500;

    /** 星璨钢那条配方的每 tick 耗电（ZF111 用户给的 12000）。
     * <b>写死成自己的常量</b>：它以前借的是 {@link #MAX_ENERGY_PER_TICK}，见上面那段。 */
    public static final int STAR_STEEL_ENERGY_PER_TICK = 12_000;

    /** 振金那条配方的每 tick 耗电（ZF121 用户给的 14500）。 */
    public static final int VIBRANIUM_ENERGY_PER_TICK = 14_500;'''

R2_OLD = u'''        table = List.copyOf(list);'''
R2_NEW = u'''        // ④ 1 硬质钛合金 + 8 热力金属 + 2 高碳钢 + 3 银锭 + 12 金锭，
        //    再消耗 1 粗振金 + 2 下界合金碎片 → 1 振金锭（0.11 ZF121，用户口述）
        //    用户原话（**改口后的最终版**）：「对不起刚才忘了合金炉的限制 这是新振金合金冶炼炉配方；
        //              1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片
        //              14500Fe/t 产出1振金」
        //    ⚠ 他第一版给的是「粗振金+钻石+2下界合金碎片+1红石粉」= **4 样消耗品**，比本机的
        //      2 个消耗槽多一倍；他随后自己发现"忘了合金炉的限制"并把那两样删掉
        //      ⇒ **槽位数不动**（仍是 5 输入 / 3 输出 / 2 消耗槽），2 样消耗品正好用满。
        //    ⚠ 时长用户**没给** ⇒ 沿用本机规格 30 秒（600 tick）⇒ 一件 14500 × 600 = 8,700,000 FE。
        //    金锭走原版/NeoForge 的 c:ingots/gold（与 ZF111 的 netherite/copper 同一条口径；
        //    解包核过：neoforge-21.1.235 的 data/c/tags/item/ingots/ 里有 gold.json）。
        //    下界合金碎片按**具体物品**认（Items.NETHERITE_SCRAP），不走标签 —— 与 ZF111 的
        //    末影水晶同一条口径（用户点的就是这两样具体东西）。
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
                        new Consume(Items.NETHERITE_SCRAP, 2)),
                new ItemStack(ModItems.VIBRANIUM_INGOT.get(), 1),
                DURATION_TICKS, VIBRANIUM_ENERGY_PER_TICK));

        table = List.copyOf(list);'''

# ③ 星璨钢那条：把借来的 MAX_ENERGY_PER_TICK 换成自己的常量（本轮探针抓到的真雷）
R4_OLD = u'''                new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 3),
                DURATION_TICKS, MAX_ENERGY_PER_TICK));'''
R4_NEW = u'''                new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 3),
                // ⚠ ZF121 从 MAX_ENERGY_PER_TICK 改成自己的常量：那个常量是"全表最贵那条"，
                //   本轮振金那条把它抬到 14500 ⇒ 星璨钢会跟着从 12000 偷偷变成 14500
                //   （探针当场抓到）。用户给的数就得写死成自己的常量。
                DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));'''

R3_OLD = u''' * <b>12000 × 600 = 7,200,000 FE</b>。这个数是"按本机规格补的"，不是用户说的 ——
 * 要改就改这条配方最后一个参数（或者 {@link #DURATION_TICKS}）。</p>
 */'''
R3_NEW = u''' * <b>12000 × 600 = 7,200,000 FE</b>。这个数是"按本机规格补的"，不是用户说的 ——
 * 要改就改这条配方最后一个参数（或者 {@link #DURATION_TICKS}）。</p>
 *
 * <p><b>0.11 ZF121 新增第四条配方（振金锭）</b>。用户原话（改口后的最终版）：
 * 「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片
 * 14500Fe/t 产出1振金」。这条打破本机一个上限：<b>每 tick 耗电第一次超过 12000</b>（14500）
 * ⇒ {@link #MAX_ENERGY_PER_TICK} 跟着改，否则 ZF42 那条静态守卫会报"最贵的一条跑不起来"。
 * 槽位数<b>一个都没动</b>（用户第一版给了 4 样消耗品，他自己发现"忘了合金炉的限制"后收窄成 2 样）。</p>
 *
 * <p>⚠ <b>顺带拆掉一个真雷</b>：星璨钢那条原来借 {@link #MAX_ENERGY_PER_TICK} 当自己的耗电，
 * 那个常量一涨，星璨钢就跟着从 12000 变成 14500（探针当场抓到）⇒ 现在两条数各归各的常量
 * （{@link #STAR_STEEL_ENERGY_PER_TICK} / {@link #VIBRANIUM_ENERGY_PER_TICK}），
 * 配方表<b>不许</b>再引用 {@code MAX_ENERGY_PER_TICK}。</p>
 *
 * <p>⚠ <b>时长用户没给</b>：沿用本机规格 30 秒（600 tick）⇒ 一件
 * <b>14500 × 600 = 8,700,000 FE</b>。储能 32768 只够 2.26 秒 ⇒ 必须持续供上 14500 FE/t。</p>
 */'''

# ============================================================
#  ② AlloySmelterBlockEntity.java（只改注释，槽位数不动）
# ============================================================
B1_OLD = u''' *       —— 星璨钢那条要 12000 FE/t，是别的配方的 15 倍（ZF62 写表时就说过"多条配方各带各的"）。</li>
 * </ul>
 */'''
B1_NEW = u''' *       —— 星璨钢那条要 12000 FE/t，是别的配方的 15 倍（ZF62 写表时就说过"多条配方各带各的"）。</li>
 * </ul>
 *
 * <p><b>0.11 ZF121：槽位数一个都没动</b>（仍是 5 输入 / 3 输出 / <b>2 消耗槽</b>）—— 振金那条要点名
 * 「1 粗振金 + 2 下界合金碎片」两样消耗品，正好把 2 个槽用满。变的是<b>最贵那条的每 tick 耗电</b>：
 * 星璨钢的 12000 → 振金的 14500（静态守卫读的 {@link AlloySmelterRecipes#MAX_ENERGY_PER_TICK}
 * 跟着改，14500 ≤ 32768 仍然成立）。</p>
 */'''

B2_OLD = u'''     * {@code 12000 ≤ 32768} ✓（0.11 ZF111 起，最贵的是星璨钢那条）。'''
B2_NEW = u'''     * {@code 14500 ≤ 32768} ✓（0.11 ZF121 起，最贵的是振金那条；ZF111 那会儿是星璨钢的 12000）。'''

B3_OLD = u'''    /** 消耗槽（0.11 ZF111 起放开）：放配方点名要消耗的东西（深层钴矿石 / 末影水晶）。 */'''
B3_NEW = u'''    /**
     * 消耗槽（0.11 ZF111 起放开）：放配方点名要消耗的东西。
     * 星璨钢那条是深层钴矿石 / 末影水晶；<b>振金那条（ZF121）是粗振金 ×1 + 下界合金碎片 ×2</b>
     * —— 两样，正好把这 2 个槽用满（用户第一版给了 4 样，他自己发现"忘了合金炉的限制"后收窄成 2 样）。
     */'''

# ============================================================
#  ③ AlloySmelterMenu.java
# ============================================================
M1_OLD = u''' * <p>用户原话：「五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽（目前放不了东西）」。
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，
 * 这里只负责摆位置；消耗槽<b>也照画出来</b>（让玩家看见那儿以后会有东西），但同样放不进去。</p>
 */'''
M1_NEW = u''' * <p>用户原话：「五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽（目前放不了东西）」。
 * 输入槽的"只收锭"由 {@code AlloySmelterBlockEntity} 的 {@code isItemValid} 管，这里只负责摆位置。</p>
 *
 * <p><b>0.11 ZF121：消耗槽终于能用手放进去了</b>。ZF49 那句"目前放不了东西"当初留了两层门，
 * 方块实体那层 ZF111 已经放开成"某条配方真的会消耗它才收"，<b>可菜单这层的恒 false 还留着</b>
 * ⇒ 手动一个都放不进去（只有漏斗/管道塞得进），而 ZF111 与本轮两条配方都要求消耗槽里有东西
 * —— 那是一条死路。现在交给 {@code machineInventory.isItemValid} 判（没激活时它照样返回 false，
 * 垃圾也照旧进不去，"不能当第二个背包用"这条口径没变）。</p>
 */'''

M2_OLD = u'''        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;       // 用户：「目前放不了东西」——以后放石墨电极
                }
            });
        }'''
M2_NEW = u'''        // 0.11 ZF121：这 2 槽**不再拦** —— 能不能放由方块实体的 isItemValid 说了算
        //（"某条配方真的会消耗它"才收，没激活时一律 false）。ZF49 那句"目前放不了东西"
        // 从 ZF111 放开方块实体那一刻起就已经名不副实了，这里把它撤掉。
        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y));
        }'''

M3_OLD = u'''            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
        }
        return -1;
    }'''
M3_NEW = u'''            if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
                return AlloySmelterBlockEntity.INPUT_FIRST + k;
            }
        }
        // 0.11 ZF121：消耗品也走 shift 点击 —— 能不能放交给 isItemValid（配方点名的才收）。
        // 不认这个的话，玩家 shift 点一下粗振金只会被丢回背包，得一个个手动拖。
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
N1_NEW = u'''            // 0.11 ZF111：消耗品（深层钴矿石 / 末影水晶）也画出来 —— 它们要放进机器的 2 个消耗槽。
            // 0.11 ZF121：振金那条同理画 7 个输入（5 锭 + 1 粗振金 + 2 个下界合金碎片），
            //   与星璨钢那条一样多 ⇒ JEI 分类尺寸一个字都不用改。'''

N2_OLD = u''' * <p>5 输入 + 3 输出 + 2 消耗槽（画出来但放不进东西），右侧一根能量条，'''
N2_NEW = u''' * <p>5 输入 + 3 输出 + 2 消耗槽（0.11 ZF121 起这条路才通：能放"某条配方点名要消耗"的东西），右侧一根能量条，'''

N3_OLD = u'''        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物）'''
N3_NEW = u'''        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物；ZF121 起消耗槽也能手放）'''

PATCHES = [("AlloySmelterRecipes.java", RECIPES, R1_OLD, R1_NEW, u"MAX 12000 → 14500 + 拆两个专属常量",
            u"VIBRANIUM_ENERGY_PER_TICK = 14_500;"),
           ("AlloySmelterRecipes.java", RECIPES, R2_OLD, R2_NEW, u"第四条配方（振金锭，2 消耗品）",
            u"new Consume(ModItems.RAW_VIBRANIUM.get(), 1),"),
           ("AlloySmelterRecipes.java", RECIPES, R4_OLD, R4_NEW, u"星璨钢那条改用专属常量（探针抓到的雷）",
            u"DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));"),
           ("AlloySmelterRecipes.java", RECIPES, R3_OLD, R3_NEW, u"类注释补 ZF121 段",
            u"0.11 ZF121 新增第四条配方（振金锭）"),
           ("AlloySmelterBlockEntity.java", BE, B1_OLD, B1_NEW, u"类注释：槽位数没动 + 14500",
            u"0.11 ZF121：槽位数一个都没动"),
           ("AlloySmelterBlockEntity.java", BE, B2_OLD, B2_NEW, u"静态守卫注释 12000 → 14500",
            u"14500 ≤ 32768"),
           ("AlloySmelterBlockEntity.java", BE, B3_OLD, B3_NEW, u"消耗槽注释补振金那两样",
            u"振金那条（ZF121）是粗振金 ×1 + 下界合金碎片 ×2"),
           ("AlloySmelterMenu.java", MENU, M1_OLD, M1_NEW, u"菜单类注释（撤 mayPlace）",
            u"0.11 ZF121：消耗槽终于能用手放进去了"),
           ("AlloySmelterMenu.java", MENU, M2_OLD, M2_NEW, u"撤掉消耗槽 mayPlace = false",
            u"这 2 槽**不再拦**"),
           ("AlloySmelterMenu.java", MENU, M3_OLD, M3_NEW, u"消耗品也能 shift 点击",
            u"消耗品也走 shift 点击"),
           ("MachineRecipes.java", MREC, N1_OLD, N1_NEW, u"JEI 那条注释",
            u"振金那条同理画 7 个输入"),
           ("PotatoST.java", MAIN, N3_OLD, N3_NEW, u"㉗ 能力注册注释",
            u"ZF121 起消耗槽也能手放"),
           ("AlloySmelterScreen.java", SCREEN, N2_OLD, N2_NEW, u"界面类注释",
            u"0.11 ZF121 起这条路才通")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


# 探针挂载点（`_zf121_unprobe.py` 摘掉它；反推证明先剥掉这一行）
# ⚠ 不带前后空行：那一行是**插在空行与 `    }` 之间**的，多带一个换行剥掉就会少一个空行
#   （ZF121 第一次反推就是这么假红了一次）。
HOOK = u"        Zf121Check.register();   // ← 临时探针（ZF121），跑完删\n"

# ---- 上一代（v2）盘上形态 → 改前件原样（只给反推证明用）----
V2_R1 = u'''     * 所以最贵的那个数在这里写成字面量：守卫读它、配方表也读它，两边永远一致。</p>
     *
     * <p><b>0.11 ZF121：最贵的变成振金那条（14500 FE/t）</b> —— 用户原话
     * 「…粗振金+2下界合金碎片 14500Fe/t 产出1振金」。
     * 12000 → 14500 之后仍然 {@code 14500 ≤ 32768}（储能），静态守卫不会吭声。</p>
     */
    public static final int MAX_ENERGY_PER_TICK = 14_500;'''

V2_R3 = u''' * <p><b>0.11 ZF121 新增第四条配方（振金锭）</b>。用户原话（改口后的最终版）：
 * 「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+2下界合金碎片
 * 14500Fe/t 产出1振金」。这条打破本机一个上限：<b>每 tick 耗电第一次超过 12000</b>（14500）
 * ⇒ {@link #MAX_ENERGY_PER_TICK} 跟着改，否则 ZF42 那条静态守卫会报"最贵的一条跑不起来"。
 * 槽位数<b>一个都没动</b>（用户第一版给了 4 样消耗品，他自己发现"忘了合金炉的限制"后收窄成 2 样）。</p>
 *
 * <p>⚠ <b>时长用户没给</b>：沿用本机规格 30 秒（600 tick）⇒ 一件
 * <b>14500 × 600 = 8,700,000 FE</b>。储能 32768 只够 2.26 秒 ⇒ 必须持续供上 14500 FE/t。</p>
 */'''

V2_R2 = R2_NEW.replace(u"DURATION_TICKS, VIBRANIUM_ENERGY_PER_TICK));",
                       u"DURATION_TICKS, MAX_ENERGY_PER_TICK));")

V2_REVS = [(RECIPES, V2_R1, R1_OLD),
           (RECIPES, V2_R2, u'''        table = List.copyOf(list);'''),
           # ⚠ 别漏开头的 ` *`：v2 那段是"空注释行 + 新段落"，只换段落会多留一个 ` *`
           (RECIPES, u" *\n" + V2_R3, u''' */''')]


def load_v1():
    spec = importlib.util.spec_from_file_location("zf121java_v1", V1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PATCHES


def proof(fails):
    u"""反推证明：把**各代**补丁反向套回当前盘上，必须与改前件逐字节相同。

    四代同堂（都是本轮留下的，别的地方没有写权限）：
      ① 改前件原样（`zf121_pre`）；
      ② v1：把消耗槽扩到 4 个那一版（用户随后改口 ⇒ 已撤，存档 `_zf121_java_v1.py`）；
      ③ v2：改口后的第一版（星璨钢那条还借着 `MAX_ENERGY_PER_TICK`）；
      ④ 最终版（本脚本 PATCHES，两条数各归各的常量）。
    每一代的 new 串互不相同（同一位置只会有一个在盘上）⇒ 反推无歧义。
    """
    v1 = load_v1()
    revs = [(p, new, old) for (_n, p, old, new, _l) in v1] \
        + list(V2_REVS) \
        + [(p, new, old) for (_n, p, old, new, _l, _m) in PATCHES]
    ok = 0
    for path, rel in zip(PATCHED, REL):
        txt = read(path)
        # 探针那一行是本脚本的挂载点（跑完由 _zf121_unprobe.py 摘掉）⇒ 反推时先剥掉
        if u"Zf121Check" in txt:
            txt = txt.replace(HOOK, u"", 1)
        for p, new, old in revs:
            if p == path and new in txt:
                txt = txt.replace(new, old, 1)
        cur = hashlib.sha1(txt.encode("utf-8")).hexdigest()
        bk = hashlib.sha1(open(os.path.join(BK, rel), "rb").read()).hexdigest()
        if cur == bk:
            ok += 1
            print(u"  [证明] %-30s 反推 == 改前件（%s）" % (os.path.basename(rel), bk[:16]))
        else:
            fails.append(u"%s 反推 %s ≠ 改前件 %s —— 有人动过这个文件，**不敢还原**"
                         % (rel, cur[:16], bk[:16]))
    print(u"反推证明通过 %d/%d" % (ok, len(PATCHED)))
    return ok == len(PATCHED)


def main(argv):
    do_write = "--write" in argv
    do_proof = "--proof" in argv or do_write
    fails = []

    if do_proof and not proof(fails):
        print(u"\n证明不过，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    # 还原到改前件（有了上面的证明才敢）
    if do_write:
        for rel in REL:
            write(os.path.join(ROOT, rel), read(os.path.join(BK, rel)))
        print(u"已还原 %d 个文件到改前件" % len(REL))

    cache, done = {}, 0
    for name, path, old, new, label, marker in PATCHES:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        # ⚠ 幂等判据必须用**补丁自己的标记串**，不能用 "old not in txt"：
        #   R2/N1 这类补丁的 new 里**故意包含** old（新块尾部就是旧那几行）⇒
        #   用 old 判会把补丁重复叠第二遍（配方会被插两次）。ZF121 第一版就踩了这个。
        if marker in txt:
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
        print(u"锚点对不上，**一个字节都没再写**（盘上就是刚还原的改前件）：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for path, txt in cache.items():
            write(path, txt)
        print(u"\n落盘：%d 个文件" % len(cache))
    elif not do_proof:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
