package com.potatost.mod;

import javax.annotation.ParametersAreNonnullByDefault;

import com.potatost.mod.client.ElectrolyzerRenderer;
import com.potatost.mod.client.ElectrolyzerScreen;
import com.potatost.mod.client.ElectricBlastFurnaceScreen;
import com.potatost.mod.client.FillingMachineScreen;
import com.potatost.mod.client.FluidPumpScreen;
import com.potatost.mod.client.GeneratorItemExtensions;
import com.potatost.mod.client.GeneratorRenderer;
import com.potatost.mod.client.HydraulicPressScreen;
import com.potatost.mod.client.LithiumBatteryRenderer;
import com.potatost.mod.client.LowGeneratorScreen;
import com.potatost.mod.client.MicroCrusherScreen;
import com.potatost.mod.client.SaltDecomposerScreen;
import com.potatost.mod.client.SaltDryerScreen;
import com.potatost.mod.client.StarfallHudLayer;
import com.potatost.mod.client.StarfallMeteorRenderer;
import com.potatost.mod.client.TerminalRenderer;
import com.potatost.mod.client.TestFluidTankScreen;

import net.minecraft.MethodsReturnNonnullByDefault;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;

/**
 * 客户端专用注册：
 *  - 泵界面 / 测试储罐界面的 Screen 工厂。
 * 仅客户端加载（value = Dist.CLIENT）。
 *
 * 2026-09-13 重建说明：按 13:11 备份全文重建，含后来两轮修复：
 *  - 电解器/晒盐机 Screen 登记；
 *  - 发电机/锂电池/电解器/接线端子 渲染器登记；
 *  - 发电机物品图标挂钩；
 *  - RegisterClientExtensionsEvent 的正确包路径（client.extensions.common）。
 *
 * <p><b>0.11 ZF85</b>：8 种流体的贴图注册从 {@code ModFluids} 的
 * {@code initializeClient(...)} 匿名覆盖搬到这里（那个方法在 NeoForge 21.1 已"弃用并标记为移除"，
 * IDE 会当成报错）。现在统一走 {@link RegisterClientExtensionsEvent}。
 * 两个类级注解（{@code @ParametersAreNonnullByDefault} + {@code @MethodsReturnNonnullByDefault}）
 * 是为了让"重写非空契约的方法"不再触发 IDE 的空值注解提醒 —— MC/NeoForge 自己的代码也是这么标的。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID, value = Dist.CLIENT)
@ParametersAreNonnullByDefault
@MethodsReturnNonnullByDefault
public class PotatoSTClient {

    @SubscribeEvent
    public static void onRegisterMenuScreens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.FLUID_PUMP_MENU.get(), FluidPumpScreen::new);
        event.register(ModMenus.TEST_FLUID_TANK_MENU.get(), TestFluidTankScreen::new);
        // 恢复：电解器 / 晒盐机 界面登记（回滚丢失；日志点名 Failed to create screen for menu type）
        event.register(ModMenus.ELECTROLYZER_MENU.get(), ElectrolyzerScreen::new);
        event.register(ModMenus.SALT_DRYER_MENU.get(), SaltDryerScreen::new);
        event.register(ModMenus.FILLING_MACHINE_MENU.get(), FillingMachineScreen::new);
        event.register(ModMenus.MICRO_CRUSHER_MENU.get(), MicroCrusherScreen::new);   // 0.10 微型粉碎机
        event.register(ModMenus.HYDRAULIC_PRESS_MENU.get(), HydraulicPressScreen::new);   // 0.10 ZF30 液压机
        event.register(ModMenus.SALT_DECOMPOSER_MENU.get(), SaltDecomposerScreen::new);   // 0.10 ZF32 盐分解构器
        event.register(ModMenus.LOW_GENERATOR_MENU.get(), LowGeneratorScreen::new);   // 0.10 ZF38 低级发电机
        event.register(ModMenus.ELECTRIC_BLAST_FURNACE_MENU.get(), ElectricBlastFurnaceScreen::new);   // 0.10 ZF39 电力高炉
        event.register(ModMenus.ALLOY_SMELTER_MENU.get(), com.potatost.mod.client.AlloySmelterScreen::new);   // 0.10 ZF49 合金冶炼炉
        event.register(ModMenus.DISTILLATION_OPERATOR_MENU.get(),
                com.potatost.mod.client.DistillationOperatorScreen::new);   // 0.11 ZF78 分馏塔操作器
        event.register(ModMenus.FLUID_EXCHANGER_MENU.get(),
                com.potatost.mod.client.FluidExchangerScreen::new);   // 0.11 ZF82 容器换流器
        event.register(ModMenus.HYDRODESULFURIZATION_CHAMBER_MENU.get(),
                com.potatost.mod.client.HydrodesulfurizationChamberScreen::new);   // 0.11 ZF96 加氢脱硫反应仓
        event.register(ModMenus.AIR_SEPARATOR_MENU.get(),
                com.potatost.mod.client.AirSeparatorScreen::new);   // 0.11 ZF97 空气分离器
        event.register(ModMenus.AMMONIA_SYNTHESIS_CHAMBER_MENU.get(),
                com.potatost.mod.client.AmmoniaSynthesisChamberScreen::new);   // 0.11 ZF97 氨气组成室
        event.register(ModMenus.COMBUSTION_CHAMBER_MENU.get(),
                com.potatost.mod.client.CombustionChamberScreen::new);   // 0.11 ZF100 燃烧反应室
        event.register(ModMenus.ACIDIC_REACTION_CHAMBER_MENU.get(),
                com.potatost.mod.client.AcidicReactionChamberScreen::new);   // 0.11 ZF101 酸性反应室
        event.register(ModMenus.OIL_PUMP_MENU.get(),
                com.potatost.mod.client.OilPumpScreen::new);   // 0.11 ZF109 采油机
        event.register(ModMenus.LITHIUM_BATTERY_PLANT_MENU.get(),
                com.potatost.mod.client.LithiumBatteryPlantScreen::new);   // 0.11 ZF112 锂电池构造间
    }

    /** 恢复：方块实体渲染器登记（发电机 / 锂电池 / 电解器 / 接线端子） */
    @SubscribeEvent
    public static void onRegisterRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(ModBlocks.GENERATOR_BE.get(), GeneratorRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.LITHIUM_BATTERY_BE.get(), LithiumBatteryRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.ELECTROLYZER_BE.get(), ElectrolyzerRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.TERMINAL_BE.get(), TerminalRenderer::new);      // 恢复：接线端子连线渲染
        // 0.11 ZF114 星轨坠：本工程**第一个实体渲染器**（一颗旋转的岩浆火球）
        event.registerEntityRenderer(ModEntities.STARFALL_METEOR.get(), StarfallMeteorRenderer::new);
    }

    /**
     * 星轨坠的倒计时 HUD（0.11 ZF114）：挂在**快捷栏那一层之上**。
     *
     * <p>⚠ {@code VanillaGuiLayers} 在 **NeoForge** 的包里
     * （{@code net.neoforged.neoforge.client.gui.VanillaGuiLayers}）—— 原版 jar 里
     * <b>没有</b>这个类，别按 {@code net.minecraft.client.gui} 去找（用 javap 核过）。</p>
     */
    @SubscribeEvent
    public static void onRegisterGuiLayers(RegisterGuiLayersEvent event) {
        event.registerAbove(VanillaGuiLayers.HOTBAR, StarfallHudLayer.ID, new StarfallHudLayer());
    }

    /** 恢复：发电机物品的 3D 图标（GeneratorItemRenderer + GeneratorItemExtensions）*/
    @SubscribeEvent
    public static void onRegisterClientExtensions(RegisterClientExtensionsEvent event) {
        event.registerItem(new GeneratorItemExtensions(), ModBlocks.GENERATOR_ITEM.get());
        registerFluidTextures(event);
        // 星仪图之章（0.11 ZF122）：把天空盒渲染器叫醒 —— 它自己在 init() 里往 **game 总线**
        // 挂 RenderLevelStageEvent（那个事件不是 IModBusEvent，见 SkyboxRenderer 的类注释）。
        com.potatost.mod.client.SkyboxRenderer.init();
    }

    /**
     * 8 种流体的贴图注册（0.11 ZF85 从 {@code ModFluids} 搬来）。
     *
     * <p>贴图路径规则和以前**一模一样**：{@code block/<流体名>_still} 与 {@code block/<流体名>_flow}
     * （三种气体 + 原油 + 四种分馏产物，名字就是注册名）。搬家的唯一原因是
     * {@code FluidType#initializeClient} 在 NeoForge 21.1 已弃用待删。</p>
     *
     * <p><b>0.11 ZF97</b>：再挂两种气体（氮气 / 氨气）⇒ 一共 **10 种**流体；
     * 新贴图是程序生成的占位（{@code _zf97_textures.py}），路径规则不变。</p>
     */
    private static void registerFluidTextures(RegisterClientExtensionsEvent event) {
        event.registerFluidType(textures("oxygen"), ModFluids.OXYGEN_TYPE.get());
        event.registerFluidType(textures("hydrogen"), ModFluids.HYDROGEN_TYPE.get());
        event.registerFluidType(textures("chlorine"), ModFluids.CHLORINE_TYPE.get());
        event.registerFluidType(textures("crude_oil"), ModFluids.CRUDE_OIL_TYPE.get());
        event.registerFluidType(textures("diesel"), ModFluids.DIESEL_TYPE.get());
        event.registerFluidType(textures("naphtha"), ModFluids.NAPHTHA_TYPE.get());
        event.registerFluidType(textures("gasoline"), ModFluids.GASOLINE_TYPE.get());
        event.registerFluidType(textures("lpg"), ModFluids.LPG_TYPE.get());
        // 0.11 ZF97：两台新机器带来的两种气体（空气分离器出氮气、氨气组成室出氨气）
        event.registerFluidType(textures("nitrogen"), ModFluids.NITROGEN_TYPE.get());
        event.registerFluidType(textures("ammonia"), ModFluids.AMMONIA_TYPE.get());
        // 0.11 ZF100：燃烧反应室输出的二氧化碳（⇒ 一共 11 种流体 / 6 种气体有贴图）
        event.registerFluidType(textures("carbon_dioxide"), ModFluids.CARBON_DIOXIDE_TYPE.get());
        // 0.11 ZF101：酸性反应室的三种酸（**是液体不是气体**）⇒ 一共 14 种流体
        event.registerFluidType(textures("carbonic_acid"), ModFluids.CARBONIC_ACID_TYPE.get());
        event.registerFluidType(textures("nitric_acid"), ModFluids.NITRIC_ACID_TYPE.get());
        event.registerFluidType(textures("sulfuric_acid"), ModFluids.SULFURIC_ACID_TYPE.get());
        // 0.11 ZF102：酸性反应室新加的第 4 个产物（盐酸）⇒ 一共 15 种流体
        event.registerFluidType(textures("hydrochloric_acid"), ModFluids.HYDROCHLORIC_ACID_TYPE.get());
    }

    /** 一种流体的"静止 + 流动"两张贴图，路径按注册名拼。 */
    private static IClientFluidTypeExtensions textures(String name) {
        return new IClientFluidTypeExtensions() {
            @Override
            public ResourceLocation getStillTexture() {
                return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "block/" + name + "_still");
            }

            @Override
            public ResourceLocation getFlowingTexture() {
                return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "block/" + name + "_flow");
            }
        };
    }
}