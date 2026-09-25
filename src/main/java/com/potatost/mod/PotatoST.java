package com.potatost.mod;

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
        // ⚠ ZF105：这一行是**必须的**，别删 —— 它的唯一作用是"在构造期把 ModArmorItems 初始化掉"。
        //    那个类的静态字段直接调 ModItems.ITEMS.register(...)，而 DeferredRegister 只在
        //    RegisterEvent 之前收条目。少了这一行，它的静态初始化会拖到"开物品栏"那一刻
        //    （创造页里 output.accept(ModArmorItems.X.get())），注册窗口已关 ⇒
        //    IllegalStateException ⇒ ExceptionInInitializerError ⇒ 开物品栏必崩。
        //    2026-09-25 18:40:17 的客户端崩溃就是这么来的（崩溃报告 217/259/327 行）。
        //    PotatoSTOres 之所以没踩，正是因为下面那行 PotatoSTOres.register(...) 顺带碰了它。
        ModArmorItems.touch();
        // 盔甲材料（0.11 ZF103）：独立注册表，同样挂在模组总线上。
        // 位置（在 ITEMS 之前或之后）不影响行为 —— 两边的 DeferredHolder.get() 都发生在
        // 注册表填充时（RegistryEvent），不是在类初始化期（档案 §4.1 那条致命雷）。
        ModArmorMaterials.ARMOR_MATERIALS.register(modEventBus);
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

        // ② 流体泵：**不再暴露流体能力**（0.11 ZF98）
        //   用户原话「流体泵改一下 本身不能储存流体 只做传输」⇒ 泵里没有内部罐了，
        //   原先那条"正/背面暴露内部罐"的登记随之撤销：别的泵/管道不能再往泵里灌，
        //   泵也不能再当别人的源。泵现在只做"源网络 → 目标网络"的直连搬运。

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

        // ㉙ 分馏塔操作器（0.11 ZF78）：收 FE（六面）；上限是**动态的** 8096 × 塔数
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getEnergyStorage());

        // ㉚ 分馏塔操作器：5 个罐（石油 + 柴油/石脑油/汽油/液化石油气）
        //     ⚠ 灌入只有石油罐收，四个产品罐是出口 —— 逻辑在 getFluidHandler() 里
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getFluidHandler());

        // ㉛ 分馏塔操作器：沥青槽位（自动化可取；只收沥青）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getInventory());

        // ⚠ 分馏塔控制器（ZF78）**故意不登记任何能力**：它不存能量、不存流体、不存物品，
        //   唯一的工作是数塔并把数量推给相邻操作器（用户原话）。

        // ㉜ 容器换流器（0.11 ZF82）：**泵接口** —— 抽的是左槽那件容器里的流体，不是机器自己的罐
        //     （用户原话「流体泵也可以把液体泵出 这个是直接消耗油罐的流体容量 然后泵出」）。
        //     六面都给：泵接哪面都能抽（气体也走这条，因为"高压气罐必须接泵泵出"）。
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.FLUID_EXCHANGER_BE.get(),
                (exchanger, side) -> exchanger.getFluidHandler());

        // ㉝ 容器换流器：两个槽（自动化可放容器/空桶，也可取产物）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.FLUID_EXCHANGER_BE.get(),
                (exchanger, side) -> exchanger.getInventory());

        // ⚠ 容器换流器**没有能量能力**：用户没给这台机器的能耗数 ⇒ 本轮不耗电（见类注释与 ZF82 决策清单）。

        // ㉞ 加氢脱硫反应仓（0.11 ZF96）：沥青槽 + 硫输出槽
        //     ⚠ 沥青槽只收沥青（门禁在方块实体的 isItemValid 与菜单的 SlotItemHandler 两处，§4.51）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.HYDRODESULFURIZATION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getInventory());

        // ㉟ 加氢脱硫反应仓：氢气罐（六面，只收氢气；抽走任意方向都行，方便拆机前抽空）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.HYDRODESULFURIZATION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getFluidHandler());

        // ⚠ 加氢脱硫反应仓**没有能量能力**：用户只给了"16 沥青 + 1000 mB 氢气 + 10 秒"，
        //    没给能耗数 ⇒ 不自己发明（与容器换流器 ZF82 同一条先例）。

        // ㊱ 空气分离器（0.11 ZF97）：收 FE（六面，储能 5000、每 tick 200）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.AIR_SEPARATOR_BE.get(),
                (separator, side) -> separator.getEnergyStorage());

        // ㊲ 空气分离器：两个储罐 —— **只出不进**（用户原话「不接受被灌入 只能泵出」），
        //     方向语义写在逻辑里（fill 恒 0 / drain 按氮→氧），这里只是把口子接上
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.AIR_SEPARATOR_BE.get(),
                (separator, side) -> separator.getFluidHandler());

        // ⚠ 空气分离器**没有物品能力**：用户原话「gui只有两个储罐…一个工作指示灯」⇒ 没有槽位。

        // ㊳ 氨气组成室（0.11 ZF97）：收 FE（六面）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getEnergyStorage());

        // ㊴ 氨气组成室：三个罐 —— **只进氮/氢、只出氨**（用户原话「泵只能泵入 氮气 氢气 泵出氨气」），
        //     收料口的方向语义写在 getFluidHandler() 里
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getFluidHandler());

        // ㊵ 氨气组成室：4 个槽（催化剂 + 三个气罐槽；自动化可取可放）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getInventory());

        // ㊶ 燃烧反应室（0.11 ZF100）：燃料槽 + 副产物槽
        //     ⚠ 燃料槽只收"原版熔炉认的燃料"（+ 柴油/汽油桶），门禁在方块实体 isItemValid
        //       与菜单 SlotItemHandler 两处，§4.51
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.COMBUSTION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getInventory());

        // ㊷ 燃烧反应室：三个罐 —— **只进氧气、只出二氧化碳/水**（用户原话「一个二氧化碳罐10000mB（输出）
        //     一个氧气罐1200mb（为必须输入端）」），方向语义写在 getFluidHandler() 里
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.COMBUSTION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getFluidHandler());

        // ⚠ 燃烧反应室**没有能量能力**：用户没给能耗数 ⇒ 不耗电；它产出的是"动力"，
        //    由相邻的动力能源捕获器每 tick 采集（见 PowerCapturerBlockEntity）。

        // ㊸ 酸性反应室（0.11 ZF101）：收 FE（六面，储能 12400、每 tick 500）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.ACIDIC_REACTION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getEnergyStorage());

        // ㊹ 酸性反应室：七个罐 —— **只进四种原料、只出三种酸**（用户原话「二氧化碳储罐 氧气储罐
        //     氨气储罐 水储罐（各1000Mb）… 硝酸 硫酸 碳酸储罐各1000Mb」），方向语义在 getFluidHandler()
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.ACIDIC_REACTION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getFluidHandler());

        // ㊺ 酸性反应室：硫槽 + 输出槽（硫槽只收硫；输出槽只能取）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.ACIDIC_REACTION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getInventory());

        // ㊻ 采油机（0.11 ZF109）：收 FE（六面，储能 32768、耗电 8n²+80n 随结构变）
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.OIL_PUMP_BE.get(),
                (pump, side) -> pump.getEnergyStorage());

        // ㊼ 采油机：一个 25B 大油罐 —— **只出不进**（它自己产油，不是储油罐），
        //     所以接管道 / 流体泵能抽走、灌不进去（fill 恒 0，与空气分离器同一条规矩）
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.OIL_PUMP_BE.get(),
                (pump, side) -> pump.getFluidHandler());

        // ⚠ 采油机**没有物品能力**：用户只点名了"一个罐子和一盏灯" ⇒ 没有槽位。
    }
}