package com.potatost.mod;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 实体注册（0.11 ZF114）—— 本工程**第一个自定义实体**：星轨坠召唤的那颗陨石。
 *
 * <p>为什么值得单开一个注册表：在这之前全工程只有方块实体（{@code BlockEntityType}），
 * 一个真正的 {@code Entity} 都没有过。星轨坠要"从 y=200 砸下来"，
 * 用方块实体做不到（方块实体不移动、也不会被客户端当实体渲染）。</p>
 *
 * <p><b>尺寸 1.6×1.6</b>：比一格略大一点，砸下来才有分量；渲染时按 {@code 1.6} 倍缩放同一块
 * 岩浆方块（见 {@code client/StarfallMeteorRenderer}），两个数要一起改。</p>
 *
 * <p><b>{@code noSave()}</b>：这颗陨石是"一次性的天灾"，存进存档没有意义 ——
 * 服务器重启后不该从半空继续掉（{@link StarfallRitualManager} 的倒计时也不会跨重启恢复）。</p>
 *
 * <p><b>{@code fireImmune()}</b>：它自己带着火往下砸，不该被自己的火点着。</p>
 *
 * <p><b>{@code updateInterval(1)}</b>：每 tick 同步位置 —— 下落是它的全部意义，
 * 用默认的 3 tick 会让客户端看到"一顿一顿"的轨迹。</p>
 *
 * <p>⚠ <b>本类必须在模组构造期被碰一下</b>（档案 §4.72）：见 {@code PotatoST} 构造器里
 * {@code ModEntities.ENTITY_TYPES.register(modEventBus)} 那一行。少了它，
 * 注册条目会拖到"第一次用到"才初始化，那时注册窗口已经关了。</p>
 */
public class ModEntities {

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, PotatoST.MODID);

    /** 星轨坠的陨石：{@code starfall_meteor}。 */
    public static final DeferredHolder<EntityType<?>, EntityType<StarfallMeteorEntity>> STARFALL_METEOR =
            ENTITY_TYPES.register("starfall_meteor", () -> EntityType.Builder
                    .of(StarfallMeteorEntity::new, MobCategory.MISC)
                    .sized(1.6F, 1.6F)
                    .clientTrackingRange(12)
                    .updateInterval(1)
                    .fireImmune()
                    .noSave()
                    .build("starfall_meteor"));

    private ModEntities() {
    }
}
