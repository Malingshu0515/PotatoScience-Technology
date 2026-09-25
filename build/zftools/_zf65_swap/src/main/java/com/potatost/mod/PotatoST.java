package com.potatost.mod;

import net.minecraft.core.Direction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import com.potatost.mod.sound.ModSounds;

/**
 * 主类（定版）：①注册所有 DeferredRegister ②登记方块能力。
 *
 * 维护规则（血的教训）：
 *  - 本文件是多线开发的汇合点，永远"加行"维护，绝不整份互覆盖；
 *  - 客户端 Screen 注册在 PotatoSTClient；矿石模块在 PotatoSTOres（这里调它 register）。
 *
 * 2026-09-13 重建说明：原文被外部因素从磁盘删除；本文件按当日 13:16 版全文重建，
 * 并包含流体登记（ModFluids.register）与 5~10 号方块能力登记（Jade 显示 FE 所必需）。
 */
@Mod(PotatoST.MODID)
public class PotatoST {

    public static final String MODID = "potato_s_t";

    public PotatoST(IEventBus modEventBus) {
        // ---- ① 基础注册 ----
        ModSounds.SOUND_EVENTS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModFluids.register(modEventBus);             // 恢复：流体（氧气/氢气）登记；曾被回滚删除（右键电解器崩溃的根因）
        SaltyRiverBiomeSource.register(modEventBus);
        ModBlocks.BLOCKS.register(modEventBus);
        ModBlocks.BLOCK_ENTITIES.register(modEventBus);
        ModItems.CREATIVE_MODE_TABS.register(modEventBus);
        ModMenus.MENU_TYPES.register(modEventBus);   // 泵/储罐菜单：少了它界面开不了
        PotatoSTOres.register(modEventBus);          // 矿石模块：方块+物品+创造页事件

        // ---- ② 方块能力 ----
        modEventBus.addListener(this::registerCapabilities);

        // ---- ③ 电力高炉装配：空手 Shift + 右键原版高炉（game 总线）----
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(BlastFurnaceAssembly.class);
    }

    private void registerCapabilities(RegisterCapabilitiesEvent event) {
        // ① 流体泵：收 FE（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.FLUID_PUMP_BE.get(),
                (pump, side) -> pump.getEnergyStorage());

        // ② 流体泵：内部缓冲罐（只从正面/背面暴露；正=抽入侧，背=输出侧）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.FLUID_PUMP_BE.get(),
                (pump, side) -> {
                    if (side == null) {
                        return pump.getFluidHandler();
                    }
                    Direction facing = pump.getBlockState().getValue(FluidPumpBlock.FACING);
                    return (side == facing || side == facing.getOpposite()) ? pump.getFluidHandler() : null;
                });

        // ③ 测试储罐：出流体（六面，供泵灌入、供你抽看）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.TEST_FLUID_TANK_BE.get(),
                (tank, side) -> tank.getFluidHandler());

        // ④ 创造模式线缆：无限 FE 源（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.CREATIVE_CABLE_BE.get(),
                (cable, side) -> cable.getEnergyStorage());

        // （可选）终端机——仅当存在 TerminalBlockEntity 时加
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.TERMINAL_BE.get(),
                (terminal, side) -> terminal.getEnergyStorage());

        // ⑤ 发电机：输出 FE（恢复：曾整段缺失；Jade 不显示 FE 的根因）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.GENERATOR_BE.get(),
                (generator, side) -> generator.getEnergyStorage());

        // ⑥ 锂电池：收/放 FE
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.LITHIUM_BATTERY_BE.get(),
                (battery, side) -> battery.getEnergyStorage(side));

        // ⑦ 电解器：收 FE
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.ELECTROLYZER_BE.get(),
                (electrolyzer, side) -> electrolyzer.getEnergyStorage());

        // ⑧ 电解器：三罐流体（水/氧气/氢气）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.ELECTROLYZER_BE.get(),
                (electrolyzer, side) -> electrolyzer.getFluidHandler());

        // ⑨ 电解器：物品槽
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.ELECTROLYZER_BE.get(),
                (electrolyzer, side) -> electrolyzer.getInventory());

        // ⑩ 晒盐机：收 FE（通电加速档）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.SALT_DRYER_BE.get(),
                (dryer, side) -> dryer.getEnergyStorage());

        // ⑪ 灌装机：收 FE（六面，被动接受相邻 OUTPUT 端子推送）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.FILLING_MACHINE_BE.get(),
                (machine, side) -> machine.getEnergyStorage());

        // ⑫ 灌装机：五个内部流体罐（六面，供管道/泵灌入气体）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.FILLING_MACHINE_BE.get(),
                (machine, side) -> machine.getFluidHandler());

        // ⑬ 灌装机：五个容器槽（自动化可插入高压气罐）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.FILLING_MACHINE_BE.get(),
                (machine, side) -> machine.getInventory());

        // ⑭ 微型粉碎机：收 FE（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.MICRO_CRUSHER_BE.get(),
                (crusher, side) -> crusher.getEnergyStorage());

        // ⑮ 微型粉碎机：1 输入 + 3 输出（自动化可插入待粉碎物、取出产物）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.MICRO_CRUSHER_BE.get(),
                (crusher, side) -> crusher.getInventory());

        // ⑯ 太阳能板：出 FE（只出不进，六面可抽；自身也会主动推给正下方）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.SOLAR_PANEL_BE.get(),
                (panel, side) -> panel.getEnergyStorage());

        // ⑰ 液压机：收 FE（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.HYDRAULIC_PRESS_BE.get(),
                (press, side) -> press.getEnergyStorage());

        // ⑱ 液压机：输入槽 + 输出槽（自动化可投锭、可取板）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.HYDRAULIC_PRESS_BE.get(),
                (press, side) -> press.getInventory());

        // ⑲ 盐分解构器：收 FE（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.SALT_DECOMPOSER_BE.get(),
                (machine, side) -> machine.getEnergyStorage());

        // ⑳ 盐分解构器：输入槽 + 3 个输出槽
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.SALT_DECOMPOSER_BE.get(),
                (machine, side) -> machine.getInventory());

        // ㉑ 低级发电机：出 FE（只出不进，六面可抽；自身也会主动推给紧邻 INPUT 端子）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.LOW_GENERATOR_BE.get(),
                (generator, side) -> generator.getEnergyStorage());

        // ㉒ 低级发电机：燃料输入槽（自动化可投煤）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.LOW_GENERATOR_BE.get(),
                (generator, side) -> generator.getInventory());

        // ㉓ 电力高炉：12 输入 + 32 输出（自动化可投料、可取产物）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.ELECTRIC_BLAST_FURNACE_BE.get(),
                (machine, side) -> machine.getInventory());

        // ㉔ 电力高炉：收 FE（六面）—— ⚠ ZF41 才补上，之前**根本没注册能量能力**，
        //     电缆接上去一点电都进不来（用户原话「原来接线块的地方也不传电」）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.ELECTRIC_BLAST_FURNACE_BE.get(),
                (machine, side) -> machine.getEnergyStorage());

        // ㉕ 电力高炉部件格：**只有原本是接线块的那两格**才是接电口，其余返回 null
        //     （用户定的规则：「多方块结构只有接线块的地方可以用端子传输电力」）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.ELECTRIC_BLAST_FURNACE_PART_BE.get(),
                (part, side) -> part.getEnergyStorage());

        // ㉖ 合金冶炼炉控制器（0.10 ZF49）：**不在这里暴露能量能力** ——
        //     用户规则「只有接线块的地方能传电」⇒ 电只从那两处接线口（㉘）进。
        //     控制器自己的 getEnergyStorage() 仍然由接线口在内部拿去用。

        // ㉗ 合金冶炼炉：5 输入 + 3 输出 + 2 消耗槽（自动化可投锭、可取产物）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.ALLOY_SMELTER_BE.get(),
                (machine, side) -> machine.getInventory());

        // ㉘ 合金冶炼炉接线口：**只有那两格能进电**（与电力高炉同一条规则）；
        //     结构没成型时返回 null ⇒ 没成型就不传电
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.ALLOY_SMELTER_PORT_BE.get(),
                (port, side) -> port.getEnergyStorage());
    }
}