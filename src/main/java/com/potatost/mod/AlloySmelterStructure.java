package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 合金冶炼炉的结构定义（0.10 ZF49 立；<b>ZF55 起改成「围起来就能激活」</b>）。
 *
 * <p><b>尺寸：4 层 × 5 排 × 4 列 = 80 格</b>（用户原话逐层给的图纸）。</p>
 *
 * <p><b>ZF55 的判定规则（用户原话：「像沉浸改成那样的 直接激活的不行吗」）</b>：</p>
 * <ul>
 *   <li><b>要查的只有 58 格</b>（{@link #REQUIRED_CELLS}）＝<b>底面整张 20 格</b>
 *       ＋<b>三层高的墙</b>（第 1~3 层的外圈）＋<b>顶面图纸画了方块的那 10 格</b>。</li>
 *   <li>这 58 格每格只要是"机器方块"（{@link #isCasing}）就算数，<b>具体用哪一种随便</b>
 *       ——图纸里的高炉 / 加热装置 / 漏斗 / 炼药锅 / 散热装置<b>都不再是硬要求</b>。</li>
 *   <li><b>第 4 层（顶面）整层不查</b>，<b>内部 12 格完全不查</b>：图纸本来就是个敞口炉子
 *       （顶面只有一圈沿、还是断了两个角的），谁把它封上、往里面塞了什么，都不影响激活。</li>
 *   <li>另外外壳上至少要有一个<b>接线块</b>（唯一的进电口，一个都没有的机器没有意义）。</li>
 * </ul>
 *
 * <p>为什么改：ZF49 那版是"逐格照图纸对"——80 格里有 6 台高炉、6 个加热装置、漏斗、
 * 炼药锅、散热装置，错一格就激活不了；用户连报三轮"激活不了"。沉浸那种多方块只看
 * <b>壳有没有围起来</b>，不看内部装饰，这里就照那个来。</p>
 *
 * <p><b>两处特殊格（成型时会换掉）</b>：</p>
 * <ol>
 *   <li><b>控制器</b>：{@code alloy_smelter}，放在图纸第 2 层 · 最前排 · <b>最右列</b>那一格
 *       （ZF57 用户新图纸；图上写着 {@code 7}）。成型/拆解/开界面都靠它。</li>
 *   <li><b>接线口</b>：外壳上<b>每一个接线块</b>成型后都会换成 {@code alloy_smelter_port}。
 *       贴图与接线块**完全一样**，挖掉会掉回一个接线块。电只能从这里进
 *       （沿用电力高炉那条用户规则：「原来接线块的地方传电」）。</li>
 * </ol>
 *
 * <p><b>坐标约定</b>：图案里 {@code j} 是"排"（0 = 最后排，4 = 最前排 = 控制器那一排）、
 * {@code i} 是"列"（<b>3 = 控制器那一侧</b>，ZF57 起；i=0 在机器的另一头）、
 * {@code y} 是层（0 = 最底层）。世界坐标由 {@link #offset} 从控制器那格推出去。</p>
 */
public final class AlloySmelterStructure {

    public static final int WIDTH = 4;      // i: 0..3
    public static final int DEPTH = 5;      // j: 0..4
    public static final int HEIGHT = 4;     // y: 0..3
    public static final int CELLS = WIDTH * DEPTH * HEIGHT;   // 80

    /**
     * <b>判定要查的格数 = 58</b>：底面 20 + 三层墙 42 − 底面那圈 14 = 48，<b>再加顶面那 10 格</b>
     * （图纸第 4 层画了方块的【空·耐热·耐热·空】那两列 × 5 排）。
     *
     * <p>演进史：ZF55 一度只查底面 + 三格墙（48 格），于是"底面 + 三格墙一围满"就自动成型，
     * 而玩家照图纸是**从下往上一层一层搭**的 ⇒ 第 4 层往往是成型之后才摆上去的，
     * 那几块留在表面上和 OBJ 盒子 z-fighting，只能靠 {@code absorbNewHullBlocks()} 事后吸收。
     * <b>ZF59 用户拍板：「等第四层摆完再成型」</b> —— 顶面那 10 格也进判定，
     * 于是"成型"就等于"图纸 4 层全摆完"，不再有晚摆的方块。</p>
     *
     * <p>⚠ 这仍然<b>不是</b>"长方体的表面 68 格"：顶面那两列之外的 10 格（图上写 0 的）
     * 与内部 12 格都不查。</p>
     */
    public static final int REQUIRED_CELLS = 58;

    /** 长方体的表面格数（= 80 − 内部 12）。成型时这 68 格里的机器方块会被换成不渲染的部件格。 */
    public static final int HULL_CELLS = 68;

    /** 控制器在图案里的位置：第 2 层（y=1）、最前排（j=4）、<b>最右列（i=3）</b>（ZF57 用户新图纸）。 */
    public static final int CTRL_Y = 1;
    public static final int CTRL_J = 4;
    public static final int CTRL_I = 3;

    /**
     * <b>参考图纸</b>（ZF55 起<b>不再是逐格判定依据</b>，判定见 {@link #inspect}）。
     *
     * <p>它仍然是"给人看的那个东西"的<b>唯一权威</b>：四语言工具提示里的数字摆放图
     * 由 {@code build/zftools/_zf52_verify.py} 逐格对着它核；而它自己又由
     * {@code build/zftools/_zf57_verify.py} 对着<b>用户原话逐字</b>核。而且有一条硬不变式
     * （{@code _zf55_verify.py} 会验）：<b>凡是判定要查的格，图纸里都必须有方块</b>
     * ——否则"照图纸搭"的人会激活不了。图例（ZF57 起改用<b>用户自己的编号</b>）：
     * <pre>
     *   1 = 耐热金属块        2 = 一般金属块
     *   3 = 加热装置          4 = 高炉
     *   5 = 接线块（成型后变成接线口）
     *   6 = 散热装置          7 = 合金炉主控
     *   0 / . = 空气（内部空腔 + 敞口顶面）
     * </pre>
     *
     * <p>内部字符仍是 {@code M/H/R/W/B/S/C/.}（{@link #kindAt} 认的就是这些），
     * 数字只是工具提示里的写法。</p>
     */
    private static final String[][] LAYERS = {
            // 第 1 层：一整块底 + 中间 3×2 的加热装置
            {
                    "MMMM",
                    "MHHM",
                    "MHHM",
                    "MHHM",
                    "MMMM",
            },
            // 第 2 层：两角接线块 + 高炉夹两侧 + 最前排【散热装置 · 耐热 · 耐热 · 主控】
            // ⚠ ZF57：主控在这一排的**最后一格**（i=3）—— 用户新图纸的口径。
            //   ZF49 那版我把它读成了最左列（i=0）⇒ 整台机器在世界里是**镜像**的，
            //   逐格判定当然全错（这多半就是用户前三轮"激活不了"的根因，见 §12.16）。
            {
                    "WRRW",
                    "B..B",
                    "B..B",
                    "B..B",
                    "SRRC",
            },
            // 第 3 层：耐热金属块围一圈（这一版没有炼药锅/漏斗了）
            {
                    "RRRR",
                    "R..R",
                    "R..R",
                    "R..R",
                    "RRRR",
            },
            // 第 4 层（顶）：**5 排**都是【空 · 耐热 · 耐热 · 空】。
            // ⚠ ZF58：用户补全了第 5 排（ZF57 时他只写了 4 排，我按"空"补的，他这次明确 5 排都要）。
            // ⚠ ZF55 起这一层**整层不在判定里**，写在这儿只是"参考搭建"。
            {
                    ".RR.",
                    ".RR.",
                    ".RR.",
                    ".RR.",
                    ".RR.",
            },
    };

    /** 一格应当是什么（参考图纸用，ZF55 起不参与判定）。 */
    public enum Kind {
        COMMON, HEATER, HEAT_RESISTANT, WIRING, BLAST_FURNACE, CONTROLLER, HOPPER, CAULDRON, HEAT_SINK, AIR
    }

    private AlloySmelterStructure() {
    }

    /** 图案里 (y, j, i) 这一格要求什么。越界返回 {@code null}。 */
    public static Kind kindAt(int y, int j, int i) {
        if (y < 0 || y >= HEIGHT || j < 0 || j >= DEPTH || i < 0 || i >= WIDTH) {
            return null;
        }
        switch (LAYERS[y][j].charAt(i)) {
            case 'M': return Kind.COMMON;
            case 'H': return Kind.HEATER;
            case 'R': return Kind.HEAT_RESISTANT;
            case 'W': return Kind.WIRING;
            case 'B': return Kind.BLAST_FURNACE;
            case 'C': return Kind.CONTROLLER;
            case 'P': return Kind.HOPPER;
            case 'K': return Kind.CAULDRON;
            case 'S': return Kind.HEAT_SINK;
            default: return Kind.AIR;
        }
    }

    /** 这一格要求的方块（{@link Kind#AIR} 返回 {@code Blocks.AIR}）。 */
    public static Block blockFor(Kind kind) {
        switch (kind) {
            case COMMON: return ModBlocks.COMMON_METAL_BLOCK.get();
            case HEATER: return ModBlocks.HEATER.get();
            case HEAT_RESISTANT: return ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get();
            case WIRING: return ModBlocks.WIRING_BLOCK.get();
            case BLAST_FURNACE: return Blocks.BLAST_FURNACE;
            case CONTROLLER: return ModBlocks.ALLOY_SMELTER.get();
            case HOPPER: return Blocks.HOPPER;
            case CAULDRON: return Blocks.CAULDRON;
            case HEAT_SINK: return ModBlocks.HEAT_SINK.get();
            default: return Blocks.AIR;
        }
    }

    /**
     * 图案格 → 世界坐标。
     *
     * @param facing 机器正面朝向（= 控制器方块的 {@code FACING}，也就是"朝着玩家"那一面）
     */
    public static BlockPos offset(BlockPos controller, Direction facing, int y, int j, int i) {
        return controller
                .relative(facing.getOpposite(), CTRL_J - j)      // 往机器背后走
                .relative(facing.getClockWise(), i - CTRL_I)     // 从正面看，i 增大 = 右手边
                .above(y - CTRL_Y);
    }

    /** 结构里所有的位置（80 格，不管内外）。 */
    public static List<BlockPos> positions(BlockPos controller, Direction facing) {
        List<BlockPos> out = new ArrayList<>(CELLS);
        for (int y = 0; y < HEIGHT; y++) {
            for (int j = 0; j < DEPTH; j++) {
                for (int i = 0; i < WIDTH; i++) {
                    out.add(offset(controller, facing, y, j, i));
                }
            }
        }
        return out;
    }

    /**
     * <b>判定要查的格</b>（58 格）：底面整张 + 第 1~3 层的外圈 + <b>顶面图纸画了方块的那 10 格</b>。
     *
     * <p>顶面为什么要查（ZF59 用户拍板「等第四层摆完再成型」）：不查的话，"底面 + 三格墙"一围满
     * 就自动成型，而玩家照图纸是**从下往上搭**的 ⇒ 第 4 层还没摆就已经成型，那几块只能靠
     * {@code absorbNewHullBlocks()} 事后吸收。现在顶面那两列进判定，"成型"＝"图纸 4 层全摆完"。</p>
     *
     * <p>顶面其余 10 格（图纸写 0 的）与内部 12 格仍然不查。顶面的要求**直接从图纸读**
     * （{@link #kindAt} 不是空气就要），这样改图纸不用改这里。</p>
     */
    public static boolean isRequired(int y, int j, int i) {
        if (y < 0 || y >= HEIGHT || j < 0 || j >= DEPTH || i < 0 || i >= WIDTH) {
            return false;
        }
        if (y == 0) {
            return true;                                    // 底面整张
        }
        if (y >= HEIGHT - 1) {
            return kindAt(y, j, i) != Kind.AIR;             // 顶面：只查"图纸画了方块"的格
        }
        return j == 0 || j == DEPTH - 1 || i == 0 || i == WIDTH - 1;
    }

    /**
     * <b>长方体的表面格</b>（68 格 = 80 − 内部 12）。顶面在表内，只是不参与判定。
     *
     * <p>成型时这张表里的机器方块会被换成不渲染的部件格：不换的话，玩家摆的那些方块
     * 会和控制器那格画的 OBJ 长方体<b>贴脸 z-fighting</b>。</p>
     */
    public static boolean isHull(int y, int j, int i) {
        if (y < 0 || y >= HEIGHT || j < 0 || j >= DEPTH || i < 0 || i >= WIDTH) {
            return false;
        }
        return y == 0 || y == HEIGHT - 1 || j == 0 || j == DEPTH - 1 || i == 0 || i == WIDTH - 1;
    }

    /**
     * 这一格算不算"机器方块"（ZF55 的<b>唯一</b>方块要求）。
     *
     * <p>刻意放宽到"本模组那几个装饰金属块 + 图纸里出现的功能方块 + 铁块"：
     * 沉浸那种多方块也是"壳用什么料都行，围起来就行"。玩家拿哪一种搭都能成型，
     * 不会再因为"第 3 排第 2 格我放的是耐热金属块而图纸写的是高炉"而激活不了。</p>
     *
     * <p>{@code alloy_smelter_port} / {@code alloy_smelter_part} 必须在表里：
     * 成型后外壳整个被换成这两种方块，每秒一次的结构复查要能把它们认成"壳还在"。</p>
     */
    public static boolean isCasing(BlockState state) {
        return state.is(ModBlocks.COMMON_METAL_BLOCK.get())
                || state.is(ModBlocks.ADVANCED_METAL_BLOCK.get())
                || state.is(ModBlocks.STABLE_METAL_BLOCK.get())
                || state.is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get())
                || state.is(ModBlocks.HEATER.get())
                || state.is(ModBlocks.HEAT_SINK.get())
                || state.is(ModBlocks.WIRING_BLOCK.get())
                || state.is(ModBlocks.ALLOY_SMELTER.get())
                || state.is(ModBlocks.ALLOY_SMELTER_PORT.get())
                || state.is(ModBlocks.ALLOY_SMELTER_PART.get())
                || state.is(Blocks.IRON_BLOCK)
                || state.is(Blocks.BLAST_FURNACE)
                || state.is(Blocks.HOPPER)
                || state.is(Blocks.CAULDRON);
    }

    /** 这一格算不算"接线块/接线口"（唯一的进电口，成型后变接线口）。 */
    public static boolean isWiring(BlockState state) {
        return state.is(ModBlocks.WIRING_BLOCK.get()) || state.is(ModBlocks.ALLOY_SMELTER_PORT.get());
    }

    /**
     * 一次结构检查的结果。
     *
     * @param holes     要查的格上的缺口（最多 {@code limit} 条，{@code limit <= 0} 表示"不用收集明细"）
     * @param holeCount 缺口的**总处数**（不受 {@code limit} 影响 —— 判定必须靠它）
     * @param wiring    外壳 68 格上的接线块/接线口数量（0 = 没地方进电）
     */
    public record Report(List<Problem> holes, int holeCount, int wiring) {

        /**
         * 能不能成型：要查的格没缺口，且至少有一个接线块。
         *
         * <p>⚠ 这里<b>绝不能</b>写成 {@code holes.isEmpty()}：不收集明细时（{@code limit <= 0}，
         * 也就是每秒一次的结构复查和自动激活走的那条路）{@code holes} 永远是空的 ——
         * ZF55 第一版就是这么写的，探针当场抓到"旁边挖了个洞还照样成型"，
         * 而且成型之后永远不会失效。</p>
         */
        public boolean ok() {
            return this.holeCount == 0 && this.wiring > 0;
        }
    }

    /**
     * 一处缺口。
     *
     * @param y     层（0 起）
     * @param j     排（0 起）
     * @param i     列（0 起）
     * @param found 实际是什么方块（只报"这里缺一块"没法排查，ZF53 起会把实际方块也打出来）
     */
    public record Problem(int y, int j, int i, Block found) {
    }

    /**
     * 检查结构（ZF55 的判定本体）。
     *
     * <p>走 80 格，但<b>只看两种格</b>：{@link #isRequired}（58 格，必须是机器方块）
     * 与 {@link #isHull} 上的接线块（顶面也算，接线块放哪儿都能进电）。
     * 内部 12 格<b>完全不看</b>。</p>
     *
     * <p><b>刻意不上报中文</b>（Audit 的 E 项是文本级检查）：这里只给结构化结果，
     * 文案由界面/聊天栏用 lang 键拼（和电力高炉同一个做法）。</p>
     *
     * @param limit 最多收集几处缺口（{@code <= 0} = 一处都不收集，只看 {@link Report#ok()}）
     */
    public static Report inspect(Level level, BlockPos controller, Direction facing, int limit) {
        List<Problem> holes = new ArrayList<>();
        int holeCount = 0;
        int wiring = 0;
        for (int y = 0; y < HEIGHT; y++) {
            for (int j = 0; j < DEPTH; j++) {
                for (int i = 0; i < WIDTH; i++) {
                    boolean required = isRequired(y, j, i);
                    if (!required && !isHull(y, j, i)) {
                        continue;               // ⚠ ZF55：内部 12 格**完全不检查**
                    }
                    BlockState have = level.getBlockState(offset(controller, facing, y, j, i));
                    if (isWiring(have)) {
                        wiring++;               // 接线块：算进电口，不算缺口
                    } else if (required && !isCasing(have)) {
                        holeCount++;
                        if (limit > 0 && holes.size() < limit) {
                            holes.add(new Problem(y, j, i, have.getBlock()));
                        }
                    }
                }
            }
        }
        return new Report(holes, holeCount, wiring);
    }

    /** 只看"成不成型"、不要细节（每秒一次的复查与自动激活用，省一次 List 分配）。 */
    public static boolean shellComplete(Level level, BlockPos controller, Direction facing) {
        return inspect(level, controller, facing, 0).ok();
    }
}
