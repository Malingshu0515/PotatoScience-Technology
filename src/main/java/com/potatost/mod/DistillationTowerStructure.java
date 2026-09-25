package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 分馏塔结构定义（0.11 ZF78）：**4×4×7** 的多方块结构。
 *
 * <p><b>图纸（用户原话，逐层照抄）</b>：一般金属块 = 1、耐热金属块 = 2、加热装置 = 3。
 *
 * <pre>
 * 第 1 层： [1][ ][ ][1]      第 2 层：同第 1 层（只有四角）
 *          [ ][ ][ ][ ]
 *          [ ][ ][ ][ ]
 *          [1][ ][ ][1]
 *
 * 第 3 层： [1][2][2][1]      第 4 层： [2][2][2][2]
 *          [2][3][3][2]                [2][ ][ ][2]
 *          [2][3][3][2]                [2][ ][ ][2]
 *          [1][2][2][1]                [2][2][2][2]
 *
 * 第 5 层：同第 3 层        第 6 层：同第 4 层
 * 第 7 层： 4×4 全部是一般金属块
 * </pre>
 *
 * <p>⇒ 四根立柱（第 1、2 层的四个角）→ 中间"热段"（第 3~6 层：角=一般、边=耐热、
 * 第 3/5 层正中 2×2 是加热装置）→ 顶盖（第 7 层整块一般金属）。</p>
 *
 * <p><b>这张图纸是四向对称的</b>（每一层沿水平面旋转/镜像后都不变）⇒ 不需要朝向，
 * 也就不存在"玩家把塔转 90° 就认不出"的问题。 {@link #offset} 里没有 facing 参数就是这个原因。</p>
 *
 * <p><b>空腔照图纸判空气</b>（与电力高炉 {@code Kind.AIR} 同一口径）：图纸画着空的格子
 * 要求是空气 —— 往里面塞方块会让塔失效。这条是 ZF78 的默认判定，
 * 要放宽（"有东西也不算错"）只改 {@link #matches} 一处。</p>
 *
 * <p><b>谁在什么时候调它</b>：只有 {@link DistillationControllerBlockEntity} 会调
 * {@link #findTowers}（每 20 tick 一次、且必须先有相邻的操作器才扫），
 * 塔本身不转方块、不生成方块实体 —— 它就是一堆普通装饰方块摆出来的形状。</p>
 */
public final class DistillationTowerStructure {

    /** 结构里每一格"应该是什么"。 */
    public enum Kind {
        /** 一般金属块 */
        COMMON,
        /** 耐热金属块 */
        HEAT,
        /** 加热装置 */
        HEATER,
        /** 空气（空腔） */
        AIR
    }

    /** 水平边长 */
    public static final int SIZE = 4;
    /** 高度（层数） */
    public static final int HEIGHT = 7;
    /** 总格数 4×4×7 = 112 */
    public static final int CELLS = SIZE * SIZE * HEIGHT;

    // ---------- 检测窗口（用户原话「周围 32*32*10 格范围内」）----------

    /** 水平：控制器两侧各 16 格（窗口 x/z ∈ 控制器 -16 .. +15，共 32） */
    public static final int HALF = 16;
    /** 竖直：窗口共 10 层 */
    public static final int RANGE_V = 10;
    /**
     * 竖直窗口下沿（相对控制器）：控制器 -3 层。
     *
     * <p>取 -3 是为了让"和控制器站在同一层地面上"的塔（塔底 = 控制器那一层，
     * 塔顶 = +6）整个落在 ±10 层窗口内。</p>
     */
    public static final int Y_MIN = -3;
    /** 竖直窗口上沿（相对控制器）：控制器 +6 层（= Y_MIN + RANGE_V - 1） */
    public static final int Y_MAX = Y_MIN + RANGE_V - 1;

    /** 操作器最多认几座塔（用户原话「最多识别4个分馏塔」）。 */
    public static final int MAX_TOWERS = 4;

    /** {@code [y][z][x]} */
    private static final Kind[][][] PATTERN = buildPattern();

    /**
     * 校验顺序：先便宜的、最常见的失败点放前面。
     *
     * <p>第 1/2 层只有 4 个格子却要 3 个"空格"——随机位置几乎立刻失败；
     * 顶盖（第 7 层）16 格全实心，也很容易否掉。真正贵的第 3~6 层放最后。</p>
     */
    private static final int[] LAYER_ORDER = {0, 1, 6, 2, 3, 4, 5};

    private DistillationTowerStructure() {
    }

    private static Kind[][][] buildPattern() {
        Kind[][][] pattern = new Kind[HEIGHT][SIZE][SIZE];
        for (int y = 0; y < HEIGHT; y++) {
            for (int z = 0; z < SIZE; z++) {
                for (int x = 0; x < SIZE; x++) {
                    pattern[y][z][x] = kindOf(x, z, y);
                }
            }
        }
        return pattern;
    }

    /**
     * 图纸的解析式写法（与上面的 ASCII 图纸逐格等价）。
     *
     * @param x 0..3（水平第一轴）
     * @param z 0..3（水平第二轴）
     * @param y 0..6（层号，0 = 最底层）
     */
    public static Kind kindOf(int x, int z, int y) {
        boolean edgeX = x == 0 || x == SIZE - 1;
        boolean edgeZ = z == 0 || z == SIZE - 1;
        return switch (y) {
            // 第 1、2 层：只有四角
            case 0, 1 -> (edgeX && edgeZ) ? Kind.COMMON : Kind.AIR;
            // 第 3、5 层：角=一般金属块、边=耐热金属块、正中 2×2=加热装置
            case 2, 4 -> {
                if (edgeX && edgeZ) {
                    yield Kind.COMMON;
                }
                yield (edgeX || edgeZ) ? Kind.HEAT : Kind.HEATER;
            }
            // 第 4、6 层：一圈耐热金属块，中间空
            case 3, 5 -> (edgeX || edgeZ) ? Kind.HEAT : Kind.AIR;
            // 第 7 层（顶盖）：整块一般金属块
            default -> Kind.COMMON;
        };
    }

    public static Kind kindAt(int x, int z, int y) {
        return PATTERN[y][z][x];
    }

    /** 某一格的实际方块是否符合图纸要求。 */
    public static boolean matches(BlockState state, Kind kind) {
        return switch (kind) {
            case COMMON -> state.is(ModBlocks.COMMON_METAL_BLOCK.get());
            case HEAT -> state.is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get());
            case HEATER -> state.is(ModBlocks.HEATER.get());
            case AIR -> state.isAir();
        };
    }

    /** 图纸上某一格该放什么方块（给提示文案/探针共用；空气返回 {@code Blocks.AIR}）。 */
    public static net.minecraft.world.level.block.Block blockFor(Kind kind) {
        return switch (kind) {
            case COMMON -> ModBlocks.COMMON_METAL_BLOCK.get();
            case HEAT -> ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get();
            case HEATER -> ModBlocks.HEATER.get();
            case AIR -> net.minecraft.world.level.block.Blocks.AIR;
        };
    }

    /**
     * 以 {@code base} 作为**第 1 层的最小角**（x/z/y 都最小的那一格）校验一整座塔。
     *
     * @return 112 格全部符合返回 true
     */
    public static boolean isValidTower(Level level, BlockPos base) {
        for (int layer : LAYER_ORDER) {
            for (int z = 0; z < SIZE; z++) {
                for (int x = 0; x < SIZE; x++) {
                    Kind kind = PATTERN[layer][z][x];
                    if (!matches(level.getBlockState(base.offset(x, layer, z)), kind)) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    /**
     * 扫描控制器周围的窗口，返回所有**互不重叠**的塔底坐标。
     *
     * <p>锚点只遍历窗口里"整座塔放得下"的位置（水平 -16..+12、竖直 -3..0），
     * 所以不需要额外的越界判断。</p>
     *
     * <p><b>为什么要去重</b>：两座塔的 4×4×7 包围盒不允许相交 —— 否则一片方块可能被
     * 数成两座塔，操作器的塔数就会虚高。做法是"先到先得"：按 y→z→x 的固定顺序扫，
     * 已经收下的塔的包围盒再被命中就跳过。顺序固定 ⇒ 同一片结构每次扫出来的<b>数量一样</b>
     * （否则塔数会随扫描顺序抖动，界面数字一跳一跳）。</p>
     */
    public static List<BlockPos> findTowers(Level level, BlockPos controller) {
        List<BlockPos> found = new ArrayList<>();
        int maxDx = HALF - SIZE;          // +12
        int maxDy = Y_MAX - (HEIGHT - 1); // 0
        for (int dy = Y_MIN; dy <= maxDy; dy++) {
            for (int dz = -HALF; dz <= maxDx; dz++) {
                for (int dx = -HALF; dx <= maxDx; dx++) {
                    BlockPos base = controller.offset(dx, dy, dz);
                    if (!isValidTower(level, base)) {
                        continue;
                    }
                    if (overlapsAny(base, found)) {
                        continue;
                    }
                    found.add(base);
                }
            }
        }
        return found;
    }

    /** 塔数（= {@link #findTowers} 的大小）。 */
    public static int countTowers(Level level, BlockPos controller) {
        return findTowers(level, controller).size();
    }

    private static boolean overlapsAny(BlockPos base, List<BlockPos> found) {
        for (BlockPos other : found) {
            if (Math.abs(other.getX() - base.getX()) < SIZE
                    && Math.abs(other.getY() - base.getY()) < HEIGHT
                    && Math.abs(other.getZ() - base.getZ()) < SIZE) {
                return true;
            }
        }
        return false;
    }

    // ================= 诊断（0.11 ZF78，用户 2026-09-24 反馈后加的）=================

    /**
     * 一处候选：以 {@code base} 为第 1 层最小角时，112 格里错了 {@code wrong} 格，
     * 以及<b>第一处</b>不符的格子（{@code x}/{@code z} 是 0..3、{@code y} 是 0..6 的层号）。
     *
     * <p>{@code expected} 是图纸要求的种类、{@code found} 是实际读到的方块状态 ——
     * 两条都交给调用方拼文案（本类不许出现用户可见的中文，
     * 与 {@code ElectricBlastFurnaceStructure.Problem} 同一条规矩）。</p>
     */
    public record Diagnosis(BlockPos base, int wrong, int x, int z, int y, Kind expected, BlockState found) {
    }

    /**
     * 找「最像分馏塔」的那一处：错的格数最少者胜，并列时取<b>离控制器最近</b>的锚点。
     *
     * <p>用户 2026-09-24 反馈「看不出来哪不对」⇒ 右击控制器直接把**第一处不符的格子**报出来
     * （第几层第几排第几列 + 坐标 + 应该是什么 + 实际是什么），不用再截图来回问。</p>
     *
     * <p>⚠ 这是**提示**不是判定：判分用的是启发式，而且为了省算力，某个锚点一旦已经比当前
     * 最好的还差就提前收工（所以并列时的距离比较不是严格全局最优）。真正的判定永远只有
     * {@link #isValidTower} 一条。</p>
     *
     * @return 窗口内一个锚点都没有（几乎不可能）时返回 {@code null}
     */
    public static Diagnosis diagnose(Level level, BlockPos controller) {
        int maxDx = HALF - SIZE;
        int maxDy = Y_MAX - (HEIGHT - 1);
        Diagnosis best = null;
        int bestWrong = Integer.MAX_VALUE;
        int bestFirst = -1;
        double bestDist = Double.MAX_VALUE;
        for (int dy = Y_MIN; dy <= maxDy; dy++) {
            for (int dz = -HALF; dz <= maxDx; dz++) {
                for (int dx = -HALF; dx <= maxDx; dx++) {
                    BlockPos base = controller.offset(dx, dy, dz);
                    // ⚠ 跳过"包围盒里装着控制器自己"的锚点：控制器是个实心方块，而塔的每一格
                    //   要么是图纸方块、要么是空气 ⇒ 这种锚点**永远不可能是塔**。
                    //   第一版没跳，探针当场抓到：控制器自己那格 1 格不符 + 距离 0
                    //   ⇒ 把真正"只差一格"的那座塔挤掉了（候选退化）。
                    if (contains(base, controller)) {
                        continue;
                    }
                    int wrong = 0;
                    int firstX = -1;
                    int firstZ = -1;
                    int firstY = -1;
                    int firstIndex = -1;
                    Kind firstExpected = null;
                    BlockState firstFound = null;
                    for (int layer = 0; layer < HEIGHT && wrong < bestWrong; layer++) {
                        for (int z = 0; z < SIZE && wrong < bestWrong; z++) {
                            for (int x = 0; x < SIZE; x++) {
                                Kind kind = PATTERN[layer][z][x];
                                BlockState found = level.getBlockState(base.offset(x, layer, z));
                                if (!matches(found, kind)) {
                                    wrong++;
                                    if (firstX < 0) {
                                        firstX = x;
                                        firstZ = z;
                                        firstY = layer;
                                        firstIndex = (layer * SIZE + z) * SIZE + x;
                                        firstExpected = kind;
                                        firstFound = found;
                                    }
                                    if (wrong >= bestWrong) {
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    double dist = base.distSqr(controller);
                    // 判分：① 错的格数少者胜；② 并列时**第一处不符越靠后越像**
                    // （说明前面那些便宜层都对上了）；③ 还并列才比离控制器近。
                    boolean better = wrong < bestWrong
                            || (wrong == bestWrong && firstIndex > bestFirst)
                            || (wrong == bestWrong && firstIndex == bestFirst && dist < bestDist);
                    if (better) {
                        bestWrong = wrong;
                        bestFirst = firstIndex;
                        bestDist = dist;
                        best = new Diagnosis(base, wrong, firstX, firstZ, firstY, firstExpected, firstFound);
                    }
                }
            }
        }
        return best;
    }

    /** {@code pos} 是不是落在以 {@code base} 为第 1 层最小角的那 4×4×7 包围盒里。 */
    private static boolean contains(BlockPos base, BlockPos pos) {
        return pos.getX() >= base.getX() && pos.getX() < base.getX() + SIZE
                && pos.getY() >= base.getY() && pos.getY() < base.getY() + HEIGHT
                && pos.getZ() >= base.getZ() && pos.getZ() < base.getZ() + SIZE;
    }
}
