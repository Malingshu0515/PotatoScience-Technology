package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 电力高炉的结构定义（0.10 ZF39）：3 层 × 3×3。
 *
 * <p><b>坐标约定（档案 §12.1，已定）：</b>把<b>高炉那一格</b>记作 {@code (i=1, j=0)}；
 * {@code j} 沿<b>背离高炉正面</b>的方向递增（高炉的 {@code FACING} 指向玩家，结构往玩家背后长），
 * {@code i∈{0,1,2}} 是每行里的左右序，{@code y=0/1/2} 是第一/二/三层。</p>
 *
 * <pre>
 * y=2  j=0 [栏杆 一般 栏杆]  j=1 [一般 活版门 一般]  j=2 [栏杆 一般 栏杆]
 * y=1  j=0 [栏杆 一般 栏杆]  j=1 [接线块  空  接线块] j=2 [栏杆 一般 栏杆]
 * y=0  j=0 [一般 高炉 一般]  j=1 [一般 加热装置 一般] j=2 [一般 一般 一般]
 * </pre>
 *
 * <p>⚠ {@code j} 的递增方向必须与 OBJ 模型烘焙时用的 {@code R} 一致，
 * 也就是「局部 +X ↦ {@code facing.getCounterClockWise()}」（见 §12.6 与
 * {@code build\zftools\\MakeBlastFurnaceModel.py}）—— 对不上的话模型会转 90° 错位。
 * 这里用同一个 {@link Direction#getCounterClockWise()}，所以两边天然一致。</p>
 */
public final class ElectricBlastFurnaceStructure {

    /** 结构里每一格"应该是什么"。 */
    public enum Kind {
        /** 一般金属块 */
        COMMON,
        /** 加热装置 */
        HEATER,
        /** 接线块 */
        WIRING,
        /** 铁栏杆（只认方块种类，不校验栏杆的 n/s/e/w 连接状态） */
        BARS,
        /** 铁活版门（不校验 facing / half / open —— 玩家随手一开就装配失败太脆了） */
        TRAPDOOR,
        /** 控制器自身：原版高炉 */
        CONTROLLER,
        /** 空气 */
        AIR
    }

    public static final int SIZE = 3;
    public static final int HEIGHT = 3;
    public static final int CELLS = SIZE * SIZE * HEIGHT;

    /** {@code [y][j][i]} */
    private static final Kind[][][] PATTERN = {
            // y = 0（第一层）
            {
                    {Kind.COMMON, Kind.CONTROLLER, Kind.COMMON},
                    {Kind.COMMON, Kind.HEATER, Kind.COMMON},
                    {Kind.COMMON, Kind.COMMON, Kind.COMMON},
            },
            // y = 1（第二层）
            {
                    {Kind.BARS, Kind.COMMON, Kind.BARS},
                    {Kind.WIRING, Kind.AIR, Kind.WIRING},
                    {Kind.BARS, Kind.COMMON, Kind.BARS},
            },
            // y = 2（第三层）
            {
                    {Kind.BARS, Kind.COMMON, Kind.BARS},
                    {Kind.COMMON, Kind.TRAPDOOR, Kind.COMMON},
                    {Kind.BARS, Kind.COMMON, Kind.BARS},
            },
    };

    private ElectricBlastFurnaceStructure() {
    }

    public static Kind kindAt(int i, int j, int y) {
        return PATTERN[y][j][i];
    }

    /** 从控制器位置 + 朝向推出第 {@code (i,j,y)} 格的世界坐标。 */
    public static BlockPos offset(BlockPos controller, Direction facing, int i, int j, int y) {
        Direction back = facing.getOpposite();
        Direction right = facing.getCounterClockWise();
        return controller.relative(back, j).relative(right, i - 1).above(y);
    }

    /** 全部 27 格的世界坐标（第 0 个就是控制器自己）。 */
    public static List<BlockPos> positions(BlockPos controller, Direction facing) {
        List<BlockPos> list = new ArrayList<>(CELLS);
        for (int y = 0; y < HEIGHT; y++) {
            for (int j = 0; j < SIZE; j++) {
                for (int i = 0; i < SIZE; i++) {
                    list.add(offset(controller, facing, i, j, y));
                }
            }
        }
        return list;
    }

    /** 某一格的实际方块是否符合结构要求。 */
    public static boolean matches(BlockState state, Kind kind) {
        return switch (kind) {
            case COMMON -> state.is(ModBlocks.COMMON_METAL_BLOCK.get());
            case HEATER -> state.is(ModBlocks.HEATER.get());
            case WIRING -> state.is(ModBlocks.WIRING_BLOCK.get());
            case BARS -> state.is(Blocks.IRON_BARS);
            case TRAPDOOR -> state.is(Blocks.IRON_TRAPDOOR);
            // ⚠ ZF100：锚点那格**两种方块都认**。
            //   ① 原版高炉 —— 老路：围着原版高炉搭好壳、空手 Shift 右键那台高炉（ZF39 起就有）；
            //   ② 电力高炉自己 —— 新路：配方造出来的主控摆下去，围着它搭壳，空手 Shift 右键主控。
            //   只认①的话，ElectricBlastFurnaceBlock#useWithoutItem 里那条"裸控制器成型"的路
            //   永远走不通（那格的判定必然失败）⇒ 配方产物会是个**摆下去没用的方块**。
            case CONTROLLER -> state.is(Blocks.BLAST_FURNACE)
                    || state.is(ModBlocks.ELECTRIC_BLAST_FURNACE.get());
            case AIR -> state.isAir();
        };
    }

    /**
     * 结构里第一处不符的位置。
     *
     * <p><b>为什么不直接返回一句中文</b>：Audit 的 E 项禁止 Java 里出现用户可见的硬编码中文
     * （文本一律走 lang）。所以这里只回传 <b>结构化的事实</b>，
     * 由调用方用 {@code Component.translatable(...)} 拼给玩家看。</p>
     *
     * @param i        左右序（0..2）
     * @param j        排号（0 = 高炉那排）
     * @param y        层号（0..2）
     * @param expected 这一格应该是什么方块（{@code AIR} 表示该空着）
     */
    public record Problem(int i, int j, int y, net.minecraft.world.level.block.Block expected) {
    }

    /**
     * 校验整个结构。
     *
     * @return 全部符合返回 {@code null}；否则返回第一处不符的位置与期望方块
     */
    public static Problem validate(Level level, BlockPos controller, Direction facing) {
        for (int y = 0; y < HEIGHT; y++) {
            for (int j = 0; j < SIZE; j++) {
                for (int i = 0; i < SIZE; i++) {
                    BlockPos p = offset(controller, facing, i, j, y);
                    Kind kind = PATTERN[y][j][i];
                    if (!matches(level.getBlockState(p), kind)) {
                        return new Problem(i, j, y, blockFor(kind));
                    }
                }
            }
        }
        return null;
    }

    /** 某一类格子对应的方块（{@code AIR} 表示该空着）。给反馈文案与探针共用。 */
    public static net.minecraft.world.level.block.Block blockFor(Kind kind) {
        return switch (kind) {
            case COMMON -> ModBlocks.COMMON_METAL_BLOCK.get();
            case HEATER -> ModBlocks.HEATER.get();
            case WIRING -> ModBlocks.WIRING_BLOCK.get();
            case BARS -> Blocks.IRON_BARS;
            case TRAPDOOR -> Blocks.IRON_TRAPDOOR;
            case CONTROLLER -> Blocks.BLAST_FURNACE;
            case AIR -> Blocks.AIR;
        };
    }
}
