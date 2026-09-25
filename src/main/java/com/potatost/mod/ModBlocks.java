package com.potatost.mod;

import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.minecraft.core.component.DataComponents;

public class ModBlocks {

    public static final DeferredRegister.Blocks BLOCKS =
            DeferredRegister.createBlocks(PotatoST.MODID);

    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, PotatoST.MODID);

    // ===== 原油液体方块（0.11 ZF73，本工程第一个 LiquidBlock）=====
    /**
     * 原油方块。**必须存在**，两个理由：
     *   ① 油田湖里总得有东西可放（{@code minecraft:lake} 特征放的就是这个方块状态）；
     *   ② **流体泵只认液体方块实例**（{@code FluidPumpBlockEntity} 里的 {@code instanceof LiquidBlock}）
     *      —— 不做成方块，泵和管道永远抽不到原油。
     *
     * <p>属性逐条照抄原版 {@code Blocks.WATER}（只把 {@code MapColor.WATER} 换成黑色），
     * 贴图走 {@code blockstates/crude_oil.json} + {@code models/block/crude_oil.json}（只有 particle）。</p>
     *
     * <p>⚠ <b>不给它注册 BlockItem</b>：原油只能被油桶舀（用户规则），不能像水桶那样拿在手里放。
     * ⚠ {@code ModFluids.CRUDE_OIL.get()} 写在 lambda 里（注册表事件触发时才求值），
     * 绝不能在静态初始化期调用（会 "Trying to access unbound value"）。</p>
     */
    public static final DeferredBlock<LiquidBlock> CRUDE_OIL = BLOCKS.register("crude_oil",
            () -> new LiquidBlock(ModFluids.CRUDE_OIL.get(), BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .replaceable()
                    .noCollission()
                    .strength(100.0F)
                    .pushReaction(PushReaction.DESTROY)
                    .noLootTable()
                    .liquid()
                    .sound(SoundType.EMPTY)));

    // ===== 接线端子 =====
    public static final DeferredBlock<Block> TERMINAL = BLOCKS.register("terminal",
            () -> new TerminalBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    public static final DeferredHolder<Item, BlockItem> TERMINAL_ITEM =
            ModItems.ITEMS.register("terminal",
                    () -> new BlockItem(TERMINAL.get(), new Item.Properties()));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<TerminalBlockEntity>> TERMINAL_BE =
            BLOCK_ENTITIES.register("terminal",
                    () -> BlockEntityType.Builder.of(TerminalBlockEntity::new, TERMINAL.get()).build(null));

    // ===== 动力能源捕获器 =====
    public static final DeferredBlock<Block> POWER_CAPTURER = BLOCKS.register("power_capturer",
            () -> new PowerCapturerBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)));

    /** 捕获器物品：Shift 显示动力获取说明，否则显示提示行 */
    public static final DeferredHolder<Item, BlockItem> POWER_CAPTURER_ITEM =
            ModItems.ITEMS.register("power_capturer",
                    () -> new BlockItem(POWER_CAPTURER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.power_capturer"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<PowerCapturerBlockEntity>> POWER_CAPTURER_BE =
            BLOCK_ENTITIES.register("power_capturer",
                    () -> BlockEntityType.Builder.of(PowerCapturerBlockEntity::new, POWER_CAPTURER.get()).build(null));

    // ===== 发电机（BER 动画模型） =====
    public static final DeferredBlock<Block> GENERATOR = BLOCKS.register("generator",
            () -> new GeneratorBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 发电机物品：Shift 显示动力说明，否则显示提示行 */
    public static final DeferredHolder<Item, BlockItem> GENERATOR_ITEM =
            ModItems.ITEMS.register("generator",
                    () -> new BlockItem(GENERATOR.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.generator"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<GeneratorBlockEntity>> GENERATOR_BE =
            BLOCK_ENTITIES.register("generator",
                    () -> BlockEntityType.Builder.of(GeneratorBlockEntity::new, GENERATOR.get()).build(null));

    // ===== 锂电池（多方块储能） =====
    public static final DeferredBlock<Block> LITHIUM_BATTERY = BLOCKS.register("lithium_battery",
            () -> new LithiumBatteryBlock(BlockBehaviour.Properties.of()
                    .strength(3.0F)
                    .sound(SoundType.METAL)));

    /** 锂电池物品：Shift 显示多方块规则与快捷放置说明，否则显示提示行 */
    public static final DeferredHolder<Item, BlockItem> LITHIUM_BATTERY_ITEM =
            ModItems.ITEMS.register("lithium_battery",
                    () -> new BlockItem(LITHIUM_BATTERY.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.lithium_battery"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<LithiumBatteryBlockEntity>> LITHIUM_BATTERY_BE =
            BLOCK_ENTITIES.register("lithium_battery",
                    () -> BlockEntityType.Builder.of(LithiumBatteryBlockEntity::new, LITHIUM_BATTERY.get()).build(null));
    // ===== 晒盐机 =====
    public static final DeferredBlock<Block> SALT_DRYER = BLOCKS.register("salt_dryer",
            () -> new SaltDryerBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 晒盐机物品：Shift 显示运作条件与产能说明 */
    public static final DeferredHolder<Item, BlockItem> SALT_DRYER_ITEM =
            ModItems.ITEMS.register("salt_dryer",
                    () -> new BlockItem(SALT_DRYER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.salt_dryer"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<SaltDryerBlockEntity>> SALT_DRYER_BE =
            BLOCK_ENTITIES.register("salt_dryer",
                    () -> BlockEntityType.Builder.of(SaltDryerBlockEntity::new, SALT_DRYER.get()).build(null));
    // ===== 电解器 =====
    public static final DeferredBlock<Block> ELECTROLYZER = BLOCKS.register("electrolyzer",
            () -> new ElectrolyzerBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 电解器物品：Shift 显示配方说明，否则显示提示行（按统一悬停规范） */
    public static final DeferredHolder<Item, BlockItem> ELECTROLYZER_ITEM =
            ModItems.ITEMS.register("electrolyzer",
                    () -> new BlockItem(ELECTROLYZER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.electrolyzer"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ElectrolyzerBlockEntity>> ELECTROLYZER_BE =
            BLOCK_ENTITIES.register("electrolyzer",
                    () -> BlockEntityType.Builder.of(ElectrolyzerBlockEntity::new, ELECTROLYZER.get()).build(null));

    // ===== 流体管道（纯导体：自身不搬运，由流体泵驱动） =====
    public static final DeferredBlock<Block> FLUID_PIPE = BLOCKS.register("fluid_pipe",
            () -> new FluidPipeBlock(BlockBehaviour.Properties.of()
                    .strength(1.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    public static final DeferredHolder<Item, BlockItem> FLUID_PIPE_ITEM =
            ModItems.ITEMS.register("fluid_pipe",
                    () -> new BlockItem(FLUID_PIPE.get(), new Item.Properties()));

    // ===== 流体泵 =====
    public static final DeferredBlock<Block> FLUID_PUMP = BLOCKS.register("fluid_pump",
            () -> new FluidPumpBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 流体泵物品：Shift 显示说明 */
    public static final DeferredHolder<Item, BlockItem> FLUID_PUMP_ITEM =
            ModItems.ITEMS.register("fluid_pump",
                    () -> new BlockItem(FLUID_PUMP.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.fluid_pump"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<FluidPumpBlockEntity>> FLUID_PUMP_BE =
            BLOCK_ENTITIES.register("fluid_pump",
                    () -> BlockEntityType.Builder.of(FluidPumpBlockEntity::new, FLUID_PUMP.get()).build(null));

    // ===== 测试流体储罐 =====
    public static final DeferredBlock<Block> TEST_FLUID_TANK = BLOCKS.register("test_fluid_tank",
            () -> new TestFluidTankBlock(BlockBehaviour.Properties.of()
                    .strength(1.5F)
                    .sound(SoundType.GLASS)
                    .noOcclusion()));

    public static final DeferredHolder<Item, BlockItem> TEST_FLUID_TANK_ITEM =
            ModItems.ITEMS.register("test_fluid_tank",
                    () -> new BlockItem(TEST_FLUID_TANK.get(), new Item.Properties()));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<TestFluidTankBlockEntity>> TEST_FLUID_TANK_BE =
            BLOCK_ENTITIES.register("test_fluid_tank",
                    () -> BlockEntityType.Builder.of(TestFluidTankBlockEntity::new, TEST_FLUID_TANK.get()).build(null));
    // ===== 创造模式线缆 =====
    public static final DeferredBlock<Block> CREATIVE_CABLE = BLOCKS.register("creative_cable",
            () -> new CreativeCableBlock(BlockBehaviour.Properties.of()
                    .strength(1.5F)
                    .sound(SoundType.METAL)));   // ★ 删掉了 .noOcclusion()
    public static final DeferredHolder<Item, BlockItem> CREATIVE_CABLE_ITEM =
            ModItems.ITEMS.register("creative_cable",
                    () -> new BlockItem(CREATIVE_CABLE.get(),
                            new Item.Properties().component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true)));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CreativeCableBlockEntity>> CREATIVE_CABLE_BE =
            BLOCK_ENTITIES.register("creative_cable",
                    () -> BlockEntityType.Builder.of(CreativeCableBlockEntity::new, CREATIVE_CABLE.get()).build(null));

    // ===== 灌装机（0.03）=====
    public static final DeferredBlock<Block> FILLING_MACHINE = BLOCKS.register("filling_machine",
            () -> new FillingMachineBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 灌装机物品：Shift 显示说明 */
    public static final DeferredHolder<Item, BlockItem> FILLING_MACHINE_ITEM =
            ModItems.ITEMS.register("filling_machine",
                    () -> new BlockItem(FILLING_MACHINE.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.filling_machine"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<FillingMachineBlockEntity>> FILLING_MACHINE_BE =
            BLOCK_ENTITIES.register("filling_machine",
                    () -> BlockEntityType.Builder.of(FillingMachineBlockEntity::new, FILLING_MACHINE.get()).build(null));

    // ===== 微型粉碎机（0.10）=====
    public static final DeferredBlock<Block> MICRO_CRUSHER = BLOCKS.register("micro_crusher",
            () -> new MicroCrusherBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)));

    /** 微型粉碎机物品：Shift 显示粉碎配方一览，否则显示提示行 */
    public static final DeferredHolder<Item, BlockItem> MICRO_CRUSHER_ITEM =
            ModItems.ITEMS.register("micro_crusher",
                    () -> new BlockItem(MICRO_CRUSHER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.micro_crusher"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<MicroCrusherBlockEntity>> MICRO_CRUSHER_BE =
            BLOCK_ENTITIES.register("micro_crusher",
                    () -> BlockEntityType.Builder.of(MicroCrusherBlockEntity::new, MICRO_CRUSHER.get()).build(null));

    // ===== 太阳能板（0.10 ZF22）=====
    /**
     * 太阳能板：只有 1 像素厚（模型单元素 [0,0,0]→[16,1,16]），所以
     * {@code noOcclusion()} 是必要的 —— 否则贴在它旁边/下面的方块会被当成"被挡住"而少渲染一面。
     */
    public static final DeferredBlock<Block> SOLAR_PANEL = BLOCKS.register("solar_panel",
            () -> new SolarPanelBlock(BlockBehaviour.Properties.of()
                    .strength(2.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 太阳能板物品：Shift 显示发电规则一览（和其它机器一致的做法） */
    public static final DeferredHolder<Item, BlockItem> SOLAR_PANEL_ITEM =
            ModItems.ITEMS.register("solar_panel",
                    () -> new BlockItem(SOLAR_PANEL.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.solar_panel"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<SolarPanelBlockEntity>> SOLAR_PANEL_BE =
            BLOCK_ENTITIES.register("solar_panel",
                    () -> BlockEntityType.Builder.of(SolarPanelBlockEntity::new, SOLAR_PANEL.get()).build(null));

    // ===== 液压机（0.10 ZF30）=====
    /** 液压机：把矿物锭锻压成板材（400 FE/t × 3s = 一块板 24000 FE）。 */
    public static final DeferredBlock<Block> HYDRAULIC_PRESS = BLOCKS.register("hydraulic_press",
            () -> new HydraulicPressBlock(BlockBehaviour.Properties.of()
                    .strength(3.5F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 液压机物品：Shift 显示工作规则一览 */
    public static final DeferredHolder<Item, BlockItem> HYDRAULIC_PRESS_ITEM =
            ModItems.ITEMS.register("hydraulic_press",
                    () -> new BlockItem(HYDRAULIC_PRESS.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hydraulic_press"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<HydraulicPressBlockEntity>> HYDRAULIC_PRESS_BE =
            BLOCK_ENTITIES.register("hydraulic_press",
                    () -> BlockEntityType.Builder.of(HydraulicPressBlockEntity::new, HYDRAULIC_PRESS.get()).build(null));

    // ===== 盐分解构器（0.10 ZF32）=====
    /** 盐分解构器：烧海盐出氯化钠（另有 60% 返还海盐、5% 出随机粗矿）。 */
    public static final DeferredBlock<Block> SALT_DECOMPOSER = BLOCKS.register("salt_decomposer",
            () -> new SaltDecomposerBlock(BlockBehaviour.Properties.of()
                    .strength(3.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 盐分解构器物品：Shift 显示配方与概率一览 */
    public static final DeferredHolder<Item, BlockItem> SALT_DECOMPOSER_ITEM =
            ModItems.ITEMS.register("salt_decomposer",
                    () -> new BlockItem(SALT_DECOMPOSER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.salt_decomposer"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<SaltDecomposerBlockEntity>> SALT_DECOMPOSER_BE =
            BLOCK_ENTITIES.register("salt_decomposer",
                    () -> BlockEntityType.Builder.of(SaltDecomposerBlockEntity::new, SALT_DECOMPOSER.get()).build(null));

    // ===== 装饰金属块与装置（0.10 ZF34）=====
    // 用户原话：「就是普通装饰 后面用于组合多方快结构的机器」
    // ⇒ 这 6 个都是**普通完整方块**：没有方块实体、没有功能、暂时也没有配方，
    //   以后接多方块结构时再决定要不要升级成机器。
    //
    // 性质对齐原版铁块：strength(5.0F, 6.0F) + 金属音效 + 必须用镐挖且至少石镐。
    // ⚠ requiresCorrectToolForDrops() 必须配合两张**原版标签**才成立：
    //   data/minecraft/tags/block/mineable/pickaxe.json   —— 决定"镐算不算正确工具"
    //   data/minecraft/tags/block/needs_stone_tool.json   —— 决定"木镐够不够"
    //   少登记任何一张，症状都是"方块能看见、能挖、但挖下去什么都不掉"（不是崩溃，很难察觉）。

    private static Block decorativeMetalBlock() {
        return new Block(BlockBehaviour.Properties.of()
                .strength(5.0F, 6.0F)
                .sound(SoundType.METAL)
                .requiresCorrectToolForDrops());
    }

    /** 一般金属块 */
    public static final DeferredBlock<Block> COMMON_METAL_BLOCK =
            BLOCKS.register("common_metal_block", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> COMMON_METAL_BLOCK_ITEM =
            ModItems.ITEMS.register("common_metal_block",
                    () -> new BlockItem(COMMON_METAL_BLOCK.get(), new Item.Properties()));

    /** 高级金属块 */
    public static final DeferredBlock<Block> ADVANCED_METAL_BLOCK =
            BLOCKS.register("advanced_metal_block", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> ADVANCED_METAL_BLOCK_ITEM =
            ModItems.ITEMS.register("advanced_metal_block",
                    () -> new BlockItem(ADVANCED_METAL_BLOCK.get(), new Item.Properties()));

    /** 稳定金属块 */
    public static final DeferredBlock<Block> STABLE_METAL_BLOCK =
            BLOCKS.register("stable_metal_block", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> STABLE_METAL_BLOCK_ITEM =
            ModItems.ITEMS.register("stable_metal_block",
                    () -> new BlockItem(STABLE_METAL_BLOCK.get(), new Item.Properties()));

    /** 耐热金属块 */
    public static final DeferredBlock<Block> HEAT_RESISTANT_METAL_BLOCK =
            BLOCKS.register("heat_resistant_metal_block", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> HEAT_RESISTANT_METAL_BLOCK_ITEM =
            ModItems.ITEMS.register("heat_resistant_metal_block",
                    () -> new BlockItem(HEAT_RESISTANT_METAL_BLOCK.get(), new Item.Properties()));

    /** 加热装置 */
    public static final DeferredBlock<Block> HEATER =
            BLOCKS.register("heater", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> HEATER_ITEM =
            ModItems.ITEMS.register("heater",
                    () -> new BlockItem(HEATER.get(), new Item.Properties()));

    /** 散热装置 */
    public static final DeferredBlock<Block> HEAT_SINK =
            BLOCKS.register("heat_sink", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> HEAT_SINK_ITEM =
            ModItems.ITEMS.register("heat_sink",
                    () -> new BlockItem(HEAT_SINK.get(), new Item.Properties()));

    /** 接线块（0.10 ZF35）—— 与上面 6 个同类：装饰方块，以后用于组合多方块结构 */
    public static final DeferredBlock<Block> WIRING_BLOCK =
            BLOCKS.register("wiring_block", () -> decorativeMetalBlock());

    public static final DeferredHolder<Item, BlockItem> WIRING_BLOCK_ITEM =
            ModItems.ITEMS.register("wiring_block",
                    () -> new BlockItem(WIRING_BLOCK.get(), new Item.Properties()));

    // ===== 低级发电机（0.10 ZF38）=====
    /** 低级发电机：烧煤炭 / 木炭发电（45s、100 FE/t、储能 1000 FE）。 */
    public static final DeferredBlock<Block> LOW_GENERATOR = BLOCKS.register("low_generator",
            () -> new LowGeneratorBlock(BlockBehaviour.Properties.of()
                    .strength(3.0F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    /** 低级发电机物品：Shift 显示燃料与发电参数 */
    public static final DeferredHolder<Item, BlockItem> LOW_GENERATOR_ITEM =
            ModItems.ITEMS.register("low_generator",
                    () -> new BlockItem(LOW_GENERATOR.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.low_generator"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<LowGeneratorBlockEntity>> LOW_GENERATOR_BE =
            BLOCK_ENTITIES.register("low_generator",
                    () -> BlockEntityType.Builder.of(LowGeneratorBlockEntity::new, LOW_GENERATOR.get()).build(null));

    // ===== 电力高炉（0.10 ZF39）=====
    /** 电力高炉控制器：装配后占据原版高炉那一格，整块 3×3×3 的 OBJ 模型挂在它身上。 */
    public static final DeferredBlock<Block> ELECTRIC_BLAST_FURNACE = BLOCKS.register("electric_blast_furnace",
            () -> new ElectricBlastFurnaceBlock(BlockBehaviour.Properties.of()
                    .strength(3.5F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    public static final DeferredHolder<Item, BlockItem> ELECTRIC_BLAST_FURNACE_ITEM =
            ModItems.ITEMS.register("electric_blast_furnace",
                    () -> new BlockItem(ELECTRIC_BLAST_FURNACE.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.electric_blast_furnace"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ElectricBlastFurnaceBlockEntity>>
            ELECTRIC_BLAST_FURNACE_BE = BLOCK_ENTITIES.register("electric_blast_furnace",
            () -> BlockEntityType.Builder.of(ElectricBlastFurnaceBlockEntity::new,
                    ELECTRIC_BLAST_FURNACE.get()).build(null));

    /** 电力高炉的部件格（25 格）：不渲染、不可单独留存，破坏任意一格 = 整体拆解。 */
    public static final DeferredBlock<Block> ELECTRIC_BLAST_FURNACE_PART =
            BLOCKS.register("electric_blast_furnace_part",
                    () -> new ElectricBlastFurnacePartBlock(BlockBehaviour.Properties.of()
                            .strength(3.5F)
                            .sound(SoundType.METAL)
                            .noOcclusion()
                            .noLootTable()));

    /**
     * 部件格的方块实体（0.10 ZF41）：存在的唯一理由是**当接电口** ——
     * 能力只能挂在方块实体上，而"只有接线块的位置能传电"这条规则需要逐格判定。
     */
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ElectricBlastFurnacePartBlockEntity>>
            ELECTRIC_BLAST_FURNACE_PART_BE = BLOCK_ENTITIES.register("electric_blast_furnace_part",
            () -> BlockEntityType.Builder.of(ElectricBlastFurnacePartBlockEntity::new,
                    ELECTRIC_BLAST_FURNACE_PART.get()).build(null));

    // ===== 合金冶炼炉（0.10 ZF49）=====
    /**
     * 控制器：用户图纸里【标靶】那一格换成它（用户答复「新加一个控制器方块」）。
     * 结构 4 层 × 5 排 × 4 列 = 80 格，见 {@link AlloySmelterStructure}。
     */
    public static final DeferredBlock<Block> ALLOY_SMELTER = BLOCKS.register("alloy_smelter",
            () -> new AlloySmelterBlock(BlockBehaviour.Properties.of()
                    .strength(3.5F)
                    .sound(SoundType.METAL)
                    .noOcclusion()));

    public static final DeferredHolder<Item, BlockItem> ALLOY_SMELTER_ITEM =
            ModItems.ITEMS.register("alloy_smelter",
                    () -> new BlockItem(ALLOY_SMELTER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            AlloySmelterBlock.appendTooltip(stack, context, tooltipComponents, tooltipFlag);
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<AlloySmelterBlockEntity>>
            ALLOY_SMELTER_BE = BLOCK_ENTITIES.register("alloy_smelter",
            () -> BlockEntityType.Builder.of(AlloySmelterBlockEntity::new, ALLOY_SMELTER.get()).build(null));

    /**
     * 接线口：成型时替换掉图案里那两格【接线块】。**没有物品形态**（挖它掉的是接线块），
     * 贴图与接线块一样，所以玩家看不出被换过 —— 但它是唯一能进电的地方。
     */
    public static final DeferredBlock<Block> ALLOY_SMELTER_PORT = BLOCKS.register("alloy_smelter_port",
            () -> new AlloySmelterPortBlock(BlockBehaviour.Properties.of()
                    .strength(5.0F, 6.0F)
                    .sound(SoundType.METAL)
                    .requiresCorrectToolForDrops()
                    .noLootTable()));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<AlloySmelterPortBlockEntity>>
            ALLOY_SMELTER_PORT_BE = BLOCK_ENTITIES.register("alloy_smelter_port",
            () -> BlockEntityType.Builder.of(AlloySmelterPortBlockEntity::new,
                    ALLOY_SMELTER_PORT.get()).build(null));

    /**
     * 部件格（ZF54）：成型时替换掉结构里 77 格，**不渲染** ——
     * 整台机器由控制器那格挂的 OBJ 长方体负责画。没有物品形态、不掉落。
     */
    public static final DeferredBlock<Block> ALLOY_SMELTER_PART = BLOCKS.register("alloy_smelter_part",
            () -> new AlloySmelterPartBlock(BlockBehaviour.Properties.of()
                    .strength(3.5F)
                    .sound(SoundType.METAL)
                    .noOcclusion()
                    .noLootTable()));

    // ===== 分馏塔三件套（0.11 ZF78）=====

    /**
     * 分馏塔控制器：用户原话「检测周围 32*32*10 格范围内的所有符合的[分馏塔]结构
     * （控制器只负责发送检测的分馏塔数量给操作器）」。
     *
     * <p><b>它没有 GUI</b>：右击没反应是设计如此（能数的东西全在操作器的界面上）。
     * 塔的结构定义（4×4×7：一般金属块 / 耐热金属块 / 加热装置）在
     * {@link DistillationTowerStructure}。</p>
     */
    public static final DeferredBlock<Block> DISTILLATION_CONTROLLER =
            BLOCKS.register("distillation_controller", () -> new DistillationControllerBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 分馏塔控制器物品：Shift 显示结构图纸 */
    public static final DeferredHolder<Item, BlockItem> DISTILLATION_CONTROLLER_ITEM =
            ModItems.ITEMS.register("distillation_controller",
                    () -> new BlockItem(DISTILLATION_CONTROLLER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.distillation_controller"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DistillationControllerBlockEntity>>
            DISTILLATION_CONTROLLER_BE = BLOCK_ENTITIES.register("distillation_controller",
            () -> BlockEntityType.Builder.of(DistillationControllerBlockEntity::new,
                    DISTILLATION_CONTROLLER.get()).build(null));

    /**
     * 分馏塔操作器：用户原话「放置在一个[分馏塔控制器]旁边，右键打开 gui
     * （类似于电力高炉的大 UI）」。
     *
     * <p>真正干活的那台：5 个罐（石油 + 4 种产品）、能量缓冲、1 个沥青槽位、
     * 红石信号一给就开炼。</p>
     */
    public static final DeferredBlock<Block> DISTILLATION_OPERATOR =
            BLOCKS.register("distillation_operator", () -> new DistillationOperatorBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 分馏塔操作器物品：Shift 显示分馏参数 */
    public static final DeferredHolder<Item, BlockItem> DISTILLATION_OPERATOR_ITEM =
            ModItems.ITEMS.register("distillation_operator",
                    () -> new BlockItem(DISTILLATION_OPERATOR.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.distillation_operator"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DistillationOperatorBlockEntity>>
            DISTILLATION_OPERATOR_BE = BLOCK_ENTITIES.register("distillation_operator",
            () -> BlockEntityType.Builder.of(DistillationOperatorBlockEntity::new,
                    DISTILLATION_OPERATOR.get()).build(null));

    // ===== 柏油块（0.11 ZF79）=====

    /**
     * 柏油块：用户原话「**12个沥青 可以在液压机压成一个柏油块**（纯建筑方块 先用煤炭块材质）」。
     *
     * <p>所以它是一个<b>纯装饰方块</b>：没有方块实体、没有功能、也不进任何机器。
     * 配方在 {@link PressRecipes}（12 个沥青 → 1 个），**不是合成台配方**。</p>
     *
     * <p>性质照原版煤炭块（用户指定用它当占位）：{@code strength 5.0/6.0} + 石头音效 +
     * {@code requiresCorrectToolForDrops()} —— 后者必须配合
     * {@code data/minecraft/tags/block/mineable/pickaxe.json} 登记才成立（§4.25）：
     * 漏登记的症状是"能看见、能挖、但挖下去什么都不掉"。煤炭块**不在** {@code needs_stone_tool} 里
     * （木镐就能挖），所以本方块也只进 pickaxe 那一张。</p>
     *
     * <p>贴图先借**原版煤炭块**那张（拷进本工程命名空间，见 {@code _zf79_assets.py} 与贴图清单）。</p>
     */
    public static final DeferredBlock<Block> ASPHALT_BLOCK = BLOCKS.register("asphalt_block",
            () -> new Block(BlockBehaviour.Properties.of()
                    .strength(5.0F, 6.0F)
                    .sound(SoundType.STONE)
                    .requiresCorrectToolForDrops()));

    public static final DeferredHolder<Item, BlockItem> ASPHALT_BLOCK_ITEM =
            ModItems.ITEMS.register("asphalt_block",
                    () -> new BlockItem(ASPHALT_BLOCK.get(), new Item.Properties()));

    // ===== 柴油 / 汽油 液体方块（0.11 ZF82）=====

    /**
     * 柴油方块：用户原话「新进 柴油桶 汽油桶（先用水桶贴图）**和原版水桶一致**
     * 可以倒出相应的流体返回空桶 并可以被空桶收回源头液体」。
     *
     * <p>「倒出」= 桶要能在地上放出一格源流体，所以流体**必须**有方块
     * （{@code BucketItem} 放置走的就是 {@code fluid.defaultFluidState().createLegacyBlock()}）；
     * 「空桶收回」= {@code LiquidBlock.pickupBlock} 返回 {@code fluid.getBucket()}，
     * 而那个值由 `ModFluids` 里的 {@code .bucket(...)} 决定。两件都落在这一对注册上。</p>
     *
     * <p>性质照原油方块（本工程唯一的液体方块先例）：strength 100 / 无碰撞 / 可替换 /
     * 推动即毁。**不给它注册 BlockItem** —— 液体方块不进物品栏（桶才是物品）。</p>
     */
    public static final DeferredBlock<LiquidBlock> DIESEL = BLOCKS.register("diesel",
            () -> new LiquidBlock(ModFluids.DIESEL.get(), BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_ORANGE)
                    .replaceable()
                    .noCollission()
                    .strength(100.0F)
                    .pushReaction(PushReaction.DESTROY)));

    /** 汽油方块：与柴油同一套理由，见上面那一节。 */
    public static final DeferredBlock<LiquidBlock> GASOLINE = BLOCKS.register("gasoline",
            () -> new LiquidBlock(ModFluids.GASOLINE.get(), BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_YELLOW)
                    .replaceable()
                    .noCollission()
                    .strength(100.0F)
                    .pushReaction(PushReaction.DESTROY)));

    // ===== 容器换流器（0.11 ZF82）=====

    /**
     * 容器换流器：用户原话「右键打开 GUI 左侧放装有液体的油桶/高压气罐 右边放空桶
     * （高压气罐必须接泵泵出）3s 后 消耗油罐内 1000mb 的液体 **把桶变成相应的流体桶**
     * （别的 mod 的流体也可以，前提是流体有对应桶的形式）流体泵也可以把液体泵出
     * 这个是直接消耗油罐的流体容量 然后泵出 有多少泵多少（取决于泵的速率）」。
     *
     * <p>没有朝向（对称占位贴图，与分馏塔操作器同款）：界面上左右两个槽位就是它的"正反面"。</p>
     */
    public static final DeferredBlock<Block> FLUID_EXCHANGER =
            BLOCKS.register("fluid_exchanger", () -> new FluidExchangerBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 容器换流器物品：Shift 显示用法 */
    public static final DeferredHolder<Item, BlockItem> FLUID_EXCHANGER_ITEM =
            ModItems.ITEMS.register("fluid_exchanger",
                    () -> new BlockItem(FLUID_EXCHANGER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.fluid_exchanger"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<FluidExchangerBlockEntity>>
            FLUID_EXCHANGER_BE = BLOCK_ENTITIES.register("fluid_exchanger",
            () -> BlockEntityType.Builder.of(FluidExchangerBlockEntity::new,
                    FLUID_EXCHANGER.get()).build(null));

    // ===== 加氢脱硫反应仓（0.11 ZF96）=====

    /**
     * 加氢脱硫反应仓：用户原话「加一个 加氢脱硫反应仓 GUI 一个氢气罐 左侧放沥青
     * 每16个沥青 消耗1000mB氢气 10s  产出一个 硫」。
     *
     * <p>没有朝向（对称占位贴图，与分馏塔操作器/容器换流器同款）：界面里"左侧沥青槽 +
     * 氢气罐"就是它的说明。合成配方见 {@code data/potato_s_t/recipe/hydrodesulfurization_chamber.json}。</p>
     *
     * <p><b>⚠ 它不吃电</b>（用户没给能耗数 ⇒ 本轮不耗电，与容器换流器 ZF82 同一条先例）：
     * 方块实体上<b>没有</b>能量能力，{@link PotatoST} 里也不给它登记 {@code EnergyStorage}。</p>
     */
    public static final DeferredBlock<Block> HYDRODESULFURIZATION_CHAMBER =
            BLOCKS.register("hydrodesulfurization_chamber", () -> new HydrodesulfurizationChamberBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 加氢脱硫反应仓物品：Shift 显示反应参数 */
    public static final DeferredHolder<Item, BlockItem> HYDRODESULFURIZATION_CHAMBER_ITEM =
            ModItems.ITEMS.register("hydrodesulfurization_chamber",
                    () -> new BlockItem(HYDRODESULFURIZATION_CHAMBER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.hydrodesulfurization_chamber"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<HydrodesulfurizationChamberBlockEntity>>
            HYDRODESULFURIZATION_CHAMBER_BE = BLOCK_ENTITIES.register("hydrodesulfurization_chamber",
            () -> BlockEntityType.Builder.of(HydrodesulfurizationChamberBlockEntity::new,
                    HYDRODESULFURIZATION_CHAMBER.get()).build(null));

    // ===== 空气分离器（0.11 ZF97）=====

    /**
     * 空气分离器：用户原话「空气分离器：gui只有两个储罐（不接受被灌入 只能泵出）
     * 一个工作指示灯 储能5000fe 耗能 200fe/t 30s产出 8mB 氮气 2mB氧气」。
     *
     * <p>没有朝向（对称占位贴图）；<b>没有物品槽</b>，所以物品栏能力也不登记。</p>
     */
    public static final DeferredBlock<Block> AIR_SEPARATOR =
            BLOCKS.register("air_separator", () -> new AirSeparatorBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 空气分离器物品：Shift 显示分离参数 */
    public static final DeferredHolder<Item, BlockItem> AIR_SEPARATOR_ITEM =
            ModItems.ITEMS.register("air_separator",
                    () -> new BlockItem(AIR_SEPARATOR.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.air_separator"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<AirSeparatorBlockEntity>>
            AIR_SEPARATOR_BE = BLOCK_ENTITIES.register("air_separator",
            () -> BlockEntityType.Builder.of(AirSeparatorBlockEntity::new,
                    AIR_SEPARATOR.get()).build(null));

    // ===== 氨气组成室（0.11 ZF97）=====

    /**
     * 氨气组成室：用户原话「氨气组成室 GUi左侧为原料储罐和一个放催化剂（铁粉）的槽位
     * （在槽位上文字标一下: [催化剂(铁粉)]）右侧则为输出 每t消耗1mB氮气 1mB氢气 200Fe/t
     * 产出1mB氨气 催化剂不消耗 原料储罐下方各有一个放高压气罐的槽位 … 泵只能泵入 氮气 氢气 泵出氨气」。
     */
    public static final DeferredBlock<Block> AMMONIA_SYNTHESIS_CHAMBER =
            BLOCKS.register("ammonia_synthesis_chamber", () -> new AmmoniaSynthesisChamberBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 氨气组成室物品：Shift 显示合成参数 */
    public static final DeferredHolder<Item, BlockItem> AMMONIA_SYNTHESIS_CHAMBER_ITEM =
            ModItems.ITEMS.register("ammonia_synthesis_chamber",
                    () -> new BlockItem(AMMONIA_SYNTHESIS_CHAMBER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.ammonia_synthesis_chamber"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<AmmoniaSynthesisChamberBlockEntity>>
            AMMONIA_SYNTHESIS_CHAMBER_BE = BLOCK_ENTITIES.register("ammonia_synthesis_chamber",
            () -> BlockEntityType.Builder.of(AmmoniaSynthesisChamberBlockEntity::new,
                    AMMONIA_SYNTHESIS_CHAMBER.get()).build(null));

    /**
     * 燃烧反应室（0.11 ZF100）。用户原话：「加一个燃烧反应室（配方；【】【高压气罐】【】，
     * 【散热装置】【铁板】【耐热金属块】，【电容】【加热装置】【打火石】） 一个二氧化碳罐10000mB（输出）
     * 一个氧气罐1200mb（为必须输入端） 一个其他产物罐 … 一个燃料槽 可以放入原版所有可以被熔炉识别的燃料
     * … 所有燃料反应后 燃烧反应室产出800点动力 可被 动力能源捕获器识别 其中柴油为1200点动力」。
     */
    public static final DeferredBlock<Block> COMBUSTION_CHAMBER =
            BLOCKS.register("combustion_chamber", () -> new CombustionChamberBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 燃烧反应室物品：Shift 显示反应参数 */
    public static final DeferredHolder<Item, BlockItem> COMBUSTION_CHAMBER_ITEM =
            ModItems.ITEMS.register("combustion_chamber",
                    () -> new BlockItem(COMBUSTION_CHAMBER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.combustion_chamber"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CombustionChamberBlockEntity>>
            COMBUSTION_CHAMBER_BE = BLOCK_ENTITIES.register("combustion_chamber",
            () -> BlockEntityType.Builder.of(CombustionChamberBlockEntity::new,
                    COMBUSTION_CHAMBER.get()).build(null));

    /**
     * 酸性反应室（0.11 ZF101）。用户原话：「加一个酸性反应室（配方【铜块】【稳定金属块】【加热装置】，
     * 【钛锭】【灌装机】【钛锭】，【红火把】【电解器】【拉杆】）… 三个选择按钮 … 耗能皆为500fe/t 储能12400fe」。
     */
    public static final DeferredBlock<Block> ACIDIC_REACTION_CHAMBER =
            BLOCKS.register("acidic_reaction_chamber", () -> new AcidicReactionChamberBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 酸性反应室物品：Shift 显示三个配方的输入输出 */
    public static final DeferredHolder<Item, BlockItem> ACIDIC_REACTION_CHAMBER_ITEM =
            ModItems.ITEMS.register("acidic_reaction_chamber",
                    () -> new BlockItem(ACIDIC_REACTION_CHAMBER.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.acidic_reaction_chamber"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<AcidicReactionChamberBlockEntity>>
            ACIDIC_REACTION_CHAMBER_BE = BLOCK_ENTITIES.register("acidic_reaction_chamber",
            () -> BlockEntityType.Builder.of(AcidicReactionChamberBlockEntity::new,
                    ACIDIC_REACTION_CHAMBER.get()).build(null));

    /**
     * 采油机（0.11 ZF109）。用户原话：「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】
     * 【耐热金属块】【硬质钛合金】，【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】）
     * 在海洋油田群系工作 gui为一个大罐子25B储量 … 下方必须有水源方块 检测下方连接的 含水锁链的数量
     * 耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s …」。
     *
     * <p>没有朝向（对称占位贴图）；<b>没有物品槽</b>，所以物品栏能力也不登记。</p>
     */
    public static final DeferredBlock<Block> OIL_PUMP =
            BLOCKS.register("oil_pump", () -> new OilPumpBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 采油机物品：Shift 显示开工条件与耗电公式 */
    public static final DeferredHolder<Item, BlockItem> OIL_PUMP_ITEM =
            ModItems.ITEMS.register("oil_pump",
                    () -> new BlockItem(OIL_PUMP.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
                                tooltipComponents.add(Component.translatable(
                                        "tooltip.potato_s_t.oil_pump"));
                            } else {
                                tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
                            }
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<OilPumpBlockEntity>>
            OIL_PUMP_BE = BLOCK_ENTITIES.register("oil_pump",
            () -> BlockEntityType.Builder.of(OilPumpBlockEntity::new,
                    OIL_PUMP.get()).build(null));
}