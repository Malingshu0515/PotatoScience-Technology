package com.potatost.mod;

import java.lang.reflect.Method;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

import com.potatost.mod.sound.ModSounds;

/**
 * ⚠⚠ <b>诊断工具（ZF36 临时文件，验证完必须删）</b>：验液压机的"运行中循环音效"这条链路。
 *
 * <p>为什么需要它：这条链路的坏法**一个都不报错**——
 * <ul>
 *   <li>音效没注册 / 注册名打错 ⇒ 游戏里静默无声（{@code SoundCheck.py} 只能查 JSON 那一侧）；</li>
 *   <li>{@code getTicker} 在客户端 {@code return null} ⇒ 客户端根本没有 ticker，
 *       循环音效的驱动代码永远不执行 ⇒ <b>注册、sounds.json、ogg 全对，就是没声音</b>。
 *       ZF36 真的差点带着这个 bug 交付（原实现就是客户端 return null）；</li>
 *   <li>{@code getUpdateTag} 没带上 {@code status} ⇒ 客户端永远看不到"运行中"（微型粉碎机踩过）；</li>
 *   <li>{@code getUpdatePacket} 忘了覆写 ⇒ 服务端变了状态也不发包。</li>
 * </ul>
 * 所以这里不看代码，只<b>量行为</b>。</p>
 *
 * <p><b>用法</b>：临时放进 {@code com.potatost.mod}、在 {@code PotatoST} 构造器里
 * {@code PressSoundCheck.register()}，然后 {@code gradlew runServer}；
 * 日志出现 {@code [SOUNDCHECK]} 若干行后自动关服。<b>验证完连同注册行一起删掉。</b></p>
 */
public final class PressSoundCheck {

    private static final String TAG = "[SOUNDCHECK] ";
    private static boolean registered;

    private PressSoundCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(PressSoundCheck.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败（不影响正式功能）：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event);
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed = 1;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0 ? "音效链路各环节全部成立" : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    private static int run(ServerStartedEvent event) {
        int failed = 0;

        // ① 音效事件真的在注册表里
        ResourceLocation soundId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "hydraulic_press_running");
        failed += check("SOUND_EVENT 注册表含 " + soundId,
                BuiltInRegistries.SOUND_EVENT.containsKey(soundId));

        // ② 音效事件与方块实体常量指向同一个 location（防"注册了 A、代码引用 B"）
        failed += check("ModSounds.HYDRAULIC_PRESS_RUNNING 的 location 就是 " + soundId,
                ModSounds.HYDRAULIC_PRESS_RUNNING.get().getLocation().equals(soundId));

        BlockState state = ModBlocks.HYDRAULIC_PRESS.get().defaultBlockState();
        BlockPos pos = BlockPos.ZERO;

        // ③ 客户端也会拿到 ticker。
        //    做法：**故意传 null 当 Level**。旧实现第一句就是 `if (level.isClientSide) return null;`，
        //    传 null 会 NPE；新实现根本不看这个参数，只会走 createTickerHelper。
        //    ⇒ 返回非 null = "客户端 return null 那个分支已经没了"，这正是循环音效能不能被驱动的开关。
        BlockEntityTicker<?> ticker = null;
        String tickerErr = "";
        try {
            // ModBlocks.HYDRAULIC_PRESS 的静态类型是 Block，getTicker 在 EntityBlock 接口上，所以要转一下
            ticker = ((net.minecraft.world.level.block.EntityBlock) ModBlocks.HYDRAULIC_PRESS.get())
                    .getTicker((net.minecraft.world.level.Level) null, state, ModBlocks.HYDRAULIC_PRESS_BE.get());
        } catch (Throwable t) {
            tickerErr = "（抛 " + t.getClass().getSimpleName() + " ⇒ level 参数仍在被解引用）";
        }
        failed += check("getTicker(null, ...) 返回非 null ⇒ 不再区分客户端/服务端" + tickerErr,
                ticker != null);

        // ④ 方块更新包必须带上 status
        HydraulicPressBlockEntity be = new HydraulicPressBlockEntity(pos, state);
        CompoundTag loaded = new CompoundTag();
        loaded.putInt("status", HydraulicPressBlockEntity.STATUS_RUNNING);
        be.loadAdditional(loaded, event.getServer().registryAccess());
        failed += check("loadAdditional 读回 status=RUNNING ⇒ isRunning() 为真", be.isRunning());

        CompoundTag out = be.getUpdateTag(event.getServer().registryAccess());
        failed += check("getUpdateTag 里带 status 且 = RUNNING（客户端靠它决定响不响）",
                out.contains("status") && out.getInt("status") == HydraulicPressBlockEntity.STATUS_RUNNING);

        // ⑤ 非运行状态不该误报
        HydraulicPressBlockEntity idle = new HydraulicPressBlockEntity(pos, state);
        CompoundTag idleTag = new CompoundTag();
        idleTag.putInt("status", HydraulicPressBlockEntity.STATUS_EMPTY);
        idle.loadAdditional(idleTag, event.getServer().registryAccess());
        failed += check("status=EMPTY 时 isRunning() 为假（反向断言）", !idle.isRunning());

        // ⑥ 两个发包方法必须是**本类覆写**的，不能靠继承（靠继承 = 不发包 = 客户端永远不知道）
        failed += check("getUpdateTag 由 HydraulicPressBlockEntity 自己声明",
                declares("getUpdateTag"));
        failed += check("getUpdatePacket 由 HydraulicPressBlockEntity 自己声明",
                declares("getUpdatePacket"));

        return failed;
    }

    private static boolean declares(String method) {
        try {
            Method m = HydraulicPressBlockEntity.class.getMethod(method, net.minecraft.core.HolderLookup.Provider.class);
            return m.getDeclaringClass() == HydraulicPressBlockEntity.class;
        } catch (NoSuchMethodException e) {
            try {
                Method m = HydraulicPressBlockEntity.class.getMethod(method);
                return m.getDeclaringClass() == HydraulicPressBlockEntity.class;
            } catch (NoSuchMethodException e2) {
                return false;
            }
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
