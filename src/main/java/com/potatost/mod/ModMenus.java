package com.potatost.mod;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public class ModMenus {

    public static final DeferredRegister<MenuType<?>> MENU_TYPES =
            DeferredRegister.create(Registries.MENU, PotatoST.MODID);

    /** 电解器菜单：MenuSupplier + FeatureFlagSet（1.21.1 构造器要求） */
    public static final DeferredHolder<MenuType<?>, MenuType<ElectrolyzerMenu>> ELECTROLYZER_MENU =
            MENU_TYPES.register("electrolyzer",
                    () -> new MenuType<>(ElectrolyzerMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 晒盐机菜单 */
    public static final DeferredHolder<MenuType<?>, MenuType<SaltDryerMenu>> SALT_DRYER_MENU =
            MENU_TYPES.register("salt_dryer",
                    () -> new MenuType<>(SaltDryerMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 流体泵菜单 */
    public static final DeferredHolder<MenuType<?>, MenuType<FluidPumpMenu>> FLUID_PUMP_MENU =
            MENU_TYPES.register("fluid_pump",
                    () -> new MenuType<>(FluidPumpMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 灌装机菜单（0.03）*/
    public static final DeferredHolder<MenuType<?>, MenuType<FillingMachineMenu>> FILLING_MACHINE_MENU =
            MENU_TYPES.register("filling_machine",
                    () -> new MenuType<>(FillingMachineMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 微型粉碎机菜单（0.10）*/
    public static final DeferredHolder<MenuType<?>, MenuType<MicroCrusherMenu>> MICRO_CRUSHER_MENU =
            MENU_TYPES.register("micro_crusher",
                    () -> new MenuType<>(MicroCrusherMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 液压机菜单（0.10 ZF30）*/
    public static final DeferredHolder<MenuType<?>, MenuType<HydraulicPressMenu>> HYDRAULIC_PRESS_MENU =
            MENU_TYPES.register("hydraulic_press",
                    () -> new MenuType<>(HydraulicPressMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 盐分解构器菜单（0.10 ZF32）*/
    public static final DeferredHolder<MenuType<?>, MenuType<SaltDecomposerMenu>> SALT_DECOMPOSER_MENU =
            MENU_TYPES.register("salt_decomposer",
                    () -> new MenuType<>(SaltDecomposerMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 低级发电机菜单（0.10 ZF38）*/
    public static final DeferredHolder<MenuType<?>, MenuType<LowGeneratorMenu>> LOW_GENERATOR_MENU =
            MENU_TYPES.register("low_generator",
                    () -> new MenuType<>(LowGeneratorMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 电力高炉菜单（0.10 ZF39）*/
    public static final DeferredHolder<MenuType<?>, MenuType<ElectricBlastFurnaceMenu>> ELECTRIC_BLAST_FURNACE_MENU =
            MENU_TYPES.register("electric_blast_furnace",
                    () -> new MenuType<>(ElectricBlastFurnaceMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 合金冶炼炉菜单（0.10 ZF49）*/
    public static final DeferredHolder<MenuType<?>, MenuType<AlloySmelterMenu>> ALLOY_SMELTER_MENU =
            MENU_TYPES.register("alloy_smelter",
                    () -> new MenuType<>(AlloySmelterMenu::new, FeatureFlags.DEFAULT_FLAGS));
    public static final DeferredHolder<MenuType<?>, MenuType<TestFluidTankMenu>> TEST_FLUID_TANK_MENU =
            MENU_TYPES.register("test_fluid_tank", () -> new MenuType<>(TestFluidTankMenu::new, FeatureFlags.DEFAULT_FLAGS));
    /** 分馏塔操作器菜单（0.11 ZF78）*/
    public static final DeferredHolder<MenuType<?>, MenuType<DistillationOperatorMenu>> DISTILLATION_OPERATOR_MENU =
            MENU_TYPES.register("distillation_operator",
                    () -> new MenuType<>(DistillationOperatorMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 容器换流器菜单（0.11 ZF82）*/
    public static final DeferredHolder<MenuType<?>, MenuType<FluidExchangerMenu>> FLUID_EXCHANGER_MENU =
            MENU_TYPES.register("fluid_exchanger",
                    () -> new MenuType<>(FluidExchangerMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 加氢脱硫反应仓菜单（0.11 ZF96）*/
    public static final DeferredHolder<MenuType<?>, MenuType<HydrodesulfurizationChamberMenu>>
            HYDRODESULFURIZATION_CHAMBER_MENU =
            MENU_TYPES.register("hydrodesulfurization_chamber",
                    () -> new MenuType<>(HydrodesulfurizationChamberMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 空气分离器菜单（0.11 ZF97）—— 一个机器槽都没有，只有两个储罐 + 一盏灯 */
    public static final DeferredHolder<MenuType<?>, MenuType<AirSeparatorMenu>> AIR_SEPARATOR_MENU =
            MENU_TYPES.register("air_separator",
                    () -> new MenuType<>(AirSeparatorMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 氨气组成室菜单（0.11 ZF97）*/
    public static final DeferredHolder<MenuType<?>, MenuType<AmmoniaSynthesisChamberMenu>>
            AMMONIA_SYNTHESIS_CHAMBER_MENU =
            MENU_TYPES.register("ammonia_synthesis_chamber",
                    () -> new MenuType<>(AmmoniaSynthesisChamberMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 燃烧反应室菜单（0.11 ZF100）—— 燃料槽 + 副产物槽 + 三个罐（罐由界面部件画） */
    public static final DeferredHolder<MenuType<?>, MenuType<CombustionChamberMenu>>
            COMBUSTION_CHAMBER_MENU =
            MENU_TYPES.register("combustion_chamber",
                    () -> new MenuType<>(CombustionChamberMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 酸性反应室菜单（0.11 ZF101）—— 硫槽 + 输出槽 + 七个罐（罐由界面部件画）*/
    public static final DeferredHolder<MenuType<?>, MenuType<AcidicReactionChamberMenu>>
            ACIDIC_REACTION_CHAMBER_MENU =
            MENU_TYPES.register("acidic_reaction_chamber",
                    () -> new MenuType<>(AcidicReactionChamberMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 采油机菜单（0.11 ZF109）—— 一个横躺的 25B 大油罐 + 一盏状态灯，没有槽位 */
    public static final DeferredHolder<MenuType<?>, MenuType<OilPumpMenu>> OIL_PUMP_MENU =
            MENU_TYPES.register("oil_pump",
                    () -> new MenuType<>(OilPumpMenu::new, FeatureFlags.DEFAULT_FLAGS));

    /** 锂电池构造间菜单（0.11 ZF112）—— 4 输入 + 1 输出 + 硫酸罐 */
    public static final DeferredHolder<MenuType<?>, MenuType<LithiumBatteryPlantMenu>>
            LITHIUM_BATTERY_PLANT_MENU =
            MENU_TYPES.register("lithium_battery_plant",
                    () -> new MenuType<>(LithiumBatteryPlantMenu::new, FeatureFlags.DEFAULT_FLAGS));

}