package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 大型柴油发电机的结构定义（0.11 ZF125）：<b>3 宽 × 5 深 × 2 层 = 30 格，一格都不能少</b>。
 *
 * <p><b>用户原话（图纸逐格照抄）</b>：</p>
 * <pre>
 * 第一层  【耐热金属块】【流体泵】【耐热金属块】
 *        【耐热金属块】【低级发电机】【耐热金属块】
 *        【耐热金属块】【燃烧反应室】【耐热金属块】
 *        【耐热金属块】【低级发电机】【耐热金属块】
 *        【耐热金属块】【柴油发电机控制器】【耐热金属块】
 * 第二层  【一般金属块】【耐热金属块】【一般金属块】
 *        【铜块】【铜格栅】【铜块】
 *        【铜块】【铜格栅】【铜块】
 *        【铜块】【铜格栅】【铜块】
 *        【一般金属块】【接线块】【一般金属块】
 * （铜无论氧化/涂蜡程度都可以）
 * </pre>
 *
 * <p><b>三件必须说清楚的事</b>：</p>
 * <ol>
 *   <li><b>行的方向</b>：用户写的第一排是<b>最后一排</b>（离玩家最远），写在第 5 排的
 *       <b>柴油发电机控制器</b>是<b>最前排</b> —— 与合金冶炼炉那条图纸同一条读法
 *       （见 {@link AlloySmelterStructure} 里 {@code j} 的定义）。「以柴油发电机控制器为正方向」
 *       ⇒ 控制器的 {@code FACING} 就是机器的正面，机器朝它<b>背后</b>铺 5 排。</li>
 *   <li><b>左右不用管</b>：每一排都是<b>回文</b>（{@code RPR} / {@code OKO} / {@code MWM}…），
 *       所以 i 轴朝哪边、镜像不镜像都不影响判定 —— 这一条是刻意核过的（合金炉当年就栽在镜像上）。</li>
 *   <li><b>铜格栅是原版方块</b>：{@code minecraft:copper_grate} 在 MC 1.21.1 <b>本来就有</b>
 *       （8 个氧化/涂蜡变体齐全，见 {@link #COPPER_GRATES}），本模组不需要自己加方块。</li>
 * </ol>
 *
 * <p><b>判定</b>：30 格<b>逐格硬判</b>（与分馏塔 {@link DistillationTowerStructure} 同一条口径），
 * 不做"是机器方块就算"的放宽 —— 用户把每一格都写清楚了，放宽反而会让他搭错也能成型。
 * 四处"任意变体"是唯一的放宽：铜块 8 种、铜格栅 8 种、接线块/接线口互通、
 * 以及那三台机器方块<b>只看方块种类、不看朝向</b>。</p>
 *
 * <p><b>成型时只有一格会被换掉</b>：控制器正上方那一格【接线块】→
 * {@code diesel_generator_port}（贴图与接线块完全一样、挖掉掉回接线块，与合金炉的接线口同一套做法）。
 * 其余 29 格<b>一个字节都不动</b> —— 里面那台流体泵 / 两台低级发电机 / 一台燃烧反应室
 * 都是玩家自己的机器，成型后照样能用（用户没说要"吸收"，本轮不发明这个规则）。</p>
 */
public final class DieselGeneratorStructure {

    /** 水平宽（图案里的 i，0..2） */
    public static final int WIDTH = 3;
    /** 水平深（图案里的 j，0 = 最后一排，4 = 控制器那一排） */
    public static final int DEPTH = 5;
    /** 层数（0 = 第一层/最底层，1 = 第二层） */
    public static final int HEIGHT = 2;
    /** 30 格 */
    public static final int CELLS = WIDTH * DEPTH * HEIGHT;

    /** 控制器在第 1 层（最底）、最前排、正中间。 */
    public static final int CTRL_Y = 0;
    public static final int CTRL_J = 4;
    public static final int CTRL_I = 1;

    /**
     * 图纸。字符表：
     * <pre>
     *   R = 耐热金属块      M = 一般金属块      P = 流体泵
     *   G = 低级发电机      B = 燃烧反应室      C = 柴油发电机控制器
     *   W = 接线块（成型后那一格变接线口）
     *   O = 铜块（8 种氧化/涂蜡变体任意）      K = 铜格栅（8 种任意）
     * </pre>
     * 没有空气格 —— 这是一台<b>实心</b>的 3×5×2 机器。
     */
    private static final String[][] LAYERS = {
            // 第 1 层（底）：两侧整排耐热金属块，中列从后往前 = 流体泵 / 低级发电机 / 燃烧反应室 / 低级发电机 / 控制器
            {
                    "RPR",
                    "RGR",
                    "RBR",
                    "RGR",
                    "RCR",
            },
            // 第 2 层（顶）：最后一排与最前排是一般金属块，中间三排是铜块夹铜格栅，控制器正上方是接线块
            {
                    "MRM",
                    "OKO",
                    "OKO",
                    "OKO",
                    "MWM",
            },
    };

    /** 图案里一格要求什么。 */
    public enum Kind {
        /** 耐热金属块 */
        HEAT,
        /** 一般金属块 */
        COMMON,
        /** 流体泵 */
        PUMP,
        /** 低级发电机 */
        GENERATOR,
        /** 燃烧反应室 */
        CHAMBER,
        /** 柴油发电机控制器（就是控制器自己那一格） */
        CONTROLLER,
        /** 接线块（成型后变接线口） */
        WIRING,
        /** 铜块（任意氧化/涂蜡变体） */
        COPPER,
        /** 铜格栅（任意氧化/涂蜡变体） */
        GRATE
    }

    /**
     * 铜块 8 变体（用户原话「铜无论氧化/涂蜡程度都可以」）。
     *
     * <p>⚠ 用 {@code Set.of} 而不是列表：判定是"在不在里面"，30 格 × 每秒一次，
     * 没必要每次走一遍数组。字段名逐个对着
     * {@code net.minecraft.world.level.block.Blocks} 核过（ZF125 反编译源码在案）。</p>
     */
    private static final Set<Block> COPPER_BLOCKS = Set.of(
            Blocks.COPPER_BLOCK,
            Blocks.EXPOSED_COPPER,
            Blocks.WEATHERED_COPPER,
            Blocks.OXIDIZED_COPPER,
            Blocks.WAXED_COPPER_BLOCK,
            Blocks.WAXED_EXPOSED_COPPER,
            Blocks.WAXED_WEATHERED_COPPER,
            Blocks.WAXED_OXIDIZED_COPPER);

    /** 铜格栅 8 变体（同上）。 */
    private static final Set<Block> COPPER_GRATES = Set.of(
            Blocks.COPPER_GRATE,
            Blocks.EXPOSED_COPPER_GRATE,
            Blocks.WEATHERED_COPPER_GRATE,
            Blocks.OXIDIZED_COPPER_GRATE,
            Blocks.WAXED_COPPER_GRATE,
            Blocks.WAXED_EXPOSED_COPPER_GRATE,
            Blocks.WAXED_WEATHERED_COPPER_GRATE,
            Blocks.WAXED_OXIDIZED_COPPER_GRATE);

    private DieselGeneratorStructure() {
    }

    /** 图案里 (y, j, i) 这一格要求什么（越界返回 {@code null}）。 */
    public static Kind kindAt(int y, int j, int i) {
        if (y < 0 || y >= HEIGHT || j < 0 || j >= DEPTH || i < 0 || i >= WIDTH) {
            return null;
        }
        switch (LAYERS[y][j].charAt(i)) {
            case 'R': return Kind.HEAT;
            case 'M': return Kind.COMMON;
            case 'P': return Kind.PUMP;
            case 'G': return Kind.GENERATOR;
            case 'B': return Kind.CHAMBER;
            case 'C': return Kind.CONTROLLER;
            case 'W': return Kind.WIRING;
            case 'O': return Kind.COPPER;
            case 'K': return Kind.GRATE;
            default: return null;
        }
    }

    /** 这一格该放什么方块（给提示文案、探针搭结构、外加图纸核对共用）。 */
    public static Block blockFor(Kind kind) {
        switch (kind) {
            case HEAT: return ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get();
            case COMMON: return ModBlocks.COMMON_METAL_BLOCK.get();
            case PUMP: return ModBlocks.FLUID_PUMP.get();
            case GENERATOR: return ModBlocks.LOW_GENERATOR.get();
            case CHAMBER: return ModBlocks.COMBUSTION_CHAMBER.get();
            case CONTROLLER: return ModBlocks.DIESEL_GENERATOR.get();
            case WIRING: return ModBlocks.WIRING_BLOCK.get();
            case COPPER: return Blocks.COPPER_BLOCK;
            case GRATE: return Blocks.COPPER_GRATE;
            default: return Blocks.AIR;
        }
    }

    /** 这一格的实际方块符不符合图纸要求（这是判定的<b>唯一</b>一条判据）。 */
    public static boolean matches(BlockState state, Kind kind) {
        if (state == null || kind == null) {
            return false;
        }
        switch (kind) {
            case COPPER: return COPPER_BLOCKS.contains(state.getBlock());
            case GRATE: return COPPER_GRATES.contains(state.getBlock());
            case WIRING: return isWiring(state);
            default: return state.is(blockFor(kind));
        }
    }

    /** 算不算"接线块那一格"：接线块本体，或成型后被换上的接线口。 */
    public static boolean isWiring(BlockState state) {
        return state.is(ModBlocks.WIRING_BLOCK.get()) || isPort(state);
    }

    /** 算不算接线口（成型时换上去的那个不渲染方块）。 */
    public static boolean isPort(BlockState state) {
        return state.is(ModBlocks.DIESEL_GENERATOR_PORT.get());
    }

    /**
     * 图案格 → 世界坐标。
     *
     * @param facing 机器正面朝向（= 控制器方块的 {@code FACING}，"朝着玩家"那一面）
     */
    public static BlockPos offset(BlockPos controller, Direction facing, int y, int j, int i) {
        return controller
                .relative(facing.getOpposite(), CTRL_J - j)      // 往机器背后走
                .relative(facing.getClockWise(), i - CTRL_I)     // 从正面看，i 增大 = 右手边（本图纸左右对称）
                .above(y - CTRL_Y);
    }

    /** 30 格的世界坐标（从后往前、从下往上）。 */
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
     * 接线口那一格 = 控制器<b>正上方</b>。
     *
     * <p>图纸里【接线块】就在控制器头顶（第 2 层 · 最前排 · 正中间），全工程只此一格
     * ⇒ 不搞"扫一圈找接线块"，就一个 {@code above()}。这条同时也是接线口
     * {@link DieselGeneratorPortBlockEntity} 找主控的方式（它直接看脚下那一格）。</p>
     */
    public static BlockPos portPos(BlockPos controller) {
        return controller.above();
    }

    /**
     * 一处缺口。
     *
     * @param y     层（0 起）
     * @param j     排（0 起，0 = 最后一排）
     * @param i     列（0 起）
     * @param found 实际是什么方块（只报"这里缺一块"没法排查）
     */
    public record Problem(int y, int j, int i, Block found) {
    }

    /**
     * 一次结构检查的结果。
     *
     * @param holes     缺口明细（最多 {@code limit} 条）
     * @param holeCount 缺口<b>总处数</b>（不受 {@code limit} 影响 —— 判定必须靠它）
     */
    public record Report(List<Problem> holes, int holeCount) {

        /** 30 格全对才算成型（⚠ 绝不能写成 {@code holes.isEmpty()}，见合金炉 §4.56 那一课）。 */
        public boolean ok() {
            return this.holeCount == 0;
        }
    }

    /**
     * 检查结构。
     *
     * <p><b>刻意不上报中文</b>（Audit 的 E 项是文本级检查）：这里只给结构化结果，
     * 文案由方块/界面用 lang 键拼。</p>
     *
     * @param limit 最多收集几处缺口（{@code <= 0} = 一处都不收集，只看 {@link Report#ok()}）
     */
    public static Report inspect(Level level, BlockPos controller, Direction facing, int limit) {
        List<Problem> holes = new ArrayList<>();
        int holeCount = 0;
        for (int y = 0; y < HEIGHT; y++) {
            for (int j = 0; j < DEPTH; j++) {
                for (int i = 0; i < WIDTH; i++) {
                    Kind kind = kindAt(y, j, i);
                    if (kind == null) {
                        continue;
                    }
                    BlockState have = level.getBlockState(offset(controller, facing, y, j, i));
                    if (!matches(have, kind)) {
                        holeCount++;
                        if (limit > 0 && holes.size() < limit) {
                            holes.add(new Problem(y, j, i, have.getBlock()));
                        }
                    }
                }
            }
        }
        return new Report(holes, holeCount);
    }

    /** 只看"成不成型"、不要细节（每半秒一次的复查用，省一次 List 分配）。 */
    public static boolean complete(Level level, BlockPos controller, Direction facing) {
        return inspect(level, controller, facing, 0).ok();
    }
}
