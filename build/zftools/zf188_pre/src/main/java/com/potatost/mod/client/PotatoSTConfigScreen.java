package com.potatost.mod.client;

import com.potatost.mod.PotatoST;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.gui.ConfigurationScreen;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;

/**
 * 把本模组的配置挂到**配置界面**上（0.14 ZF186）。
 *
 * <p><b>用户原话</b>：「联动一下配置界面（<b>做成不是必须依赖项</b>）使本mod可以接受配置」。</p>
 *
 * <h2>怎么做到「不是必须依赖项」</h2>
 * <p>用的是 <b>NeoForge 自带</b>的 {@link ConfigurationScreen}（模组列表里那个「配置」按钮，
 * 界面由 {@code ModConfigSpec} 自动生成）—— 所以：</p>
 * <ul>
 *   <li><b>一个依赖都没加</b>：{@code neoforge.mods.toml} 里 required/optional 一个字没动，
 *       没装任何配置界面模组也照样有界面（NeoForge 本体就带）；</li>
 *   <li>第三方配置界面模组（Configured / Cloth 之类读 {@code ModConfigSpec} 的）读的是**同一份规格**，
 *       装了也能用、不冲突；</li>
 *   <li>实在不想要界面，删掉 {@code config/potato_s_t-common.toml} 里的条目、直接改 TOML 也一样生效。</li>
 * </ul>
 *
 * <h2>两个坑（都踩过才知道）</h2>
 * <ol>
 *   <li><b>{@link ConfigurationScreen} 自己**不是** {@code IConfigScreenFactory}</b>
 *       （它是 {@code final class ... extends OptionsSubScreen}）⇒ 不能写 {@code ConfigurationScreen::new}
 *       当工厂用。工厂得是「接两个参数、返回一个 Screen」的 lambda：
 *       {@code (modContainer, parent) -> new ConfigurationScreen(modContainer, parent)}。</li>
 *   <li><b>这个类必须只在客户端加载</b>（{@code value = Dist.CLIENT}）。⚠ <b>不要写
 *       {@code bus = EventBusSubscriber.Bus.MOD}</b> —— 那个参数在 NeoForge 21.1.235 里
 *       <b>已标记为「过时待删」</b>（编译会出 {@code [removal]} 警告）；注解不写 bus 时，
 *       {@code FMLClientSetupEvent} 这种 {@code IModBusEvent} 照样落在 mod 总线上
 *       （同目录的 {@code PotatoSTClient} 就是这么干的：它那些 {@code RegisterMenuScreensEvent}
 *       一个 bus 参数都没写，界面一直好好的）。</li>
 *   <li>注册扩展点本身不挑时机（{@code ModContainer.registerExtensionPoint} 就是一句
 *       {@code Map.put}，javap 核过），所以放在客户端装配这一拍完全安全。</li>
 * </ol>
 */
@EventBusSubscriber(modid = PotatoST.MODID, value = Dist.CLIENT)
public final class PotatoSTConfigScreen {

    private PotatoSTConfigScreen() {
    }

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        ModList.get().getModContainerById(PotatoST.MODID).ifPresent(container ->
                container.registerExtensionPoint(IConfigScreenFactory.class,
                        (modContainer, parent) -> new ConfigurationScreen(modContainer, parent)));
    }
}
