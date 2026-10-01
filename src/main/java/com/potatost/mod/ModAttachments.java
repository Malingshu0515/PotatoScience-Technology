package com.potatost.mod;

import com.mojang.serialization.Codec;

import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * 玩家附件（0.13 ZF156）—— 本工程**第一次**用 NeoForge 的 Attachment。
 *
 * <p><b>为什么手册那个"已给过"标记非搬过来不可</b>：0.12 的标记放在
 * {@code ServerPlayer.getPersistentData()} 里 —— 那个 Compound 在玩家**克隆**时会被丢掉。
 * 1.21.1 源码里"克隆"只有一处入口：{@code ServerPlayer.restoreFrom(ServerPlayer that, boolean keepEverything)}
 * （ServerPlayer.java:1437），而它只搬一个键：
 * <pre>
 * CompoundTag old = that.getPersistentData();
 * if (old.contains(PERSISTED_NBT_TAG))            // "PlayerPersisted"
 *     getPersistentData().put(PERSISTED_NBT_TAG, old.get(PERSISTED_NBT_TAG));
 * </pre>
 * 别的键一律不搬。谁走这条路？<b>换维度</b>与<b>死后重生</b>：
 * {@code ServerGamePacketListenerImpl:1669}（{@code CHANGED_DIMENSION}）与
 * {@code :1676}（{@code KILLED}）都调 {@code PlayerList.respawn(...)} → {@code restoreFrom(...)}
 * ⇒ 玩家**每下一次矿 / 每去一趟下界 / 每死一次**，那个标记就没了，
 * 下次进游戏又发一本（用户原话「potatoST手册每回进游戏都会给一本」）。
 * 真存档里也对得上：同一个玩家在 {@code 新的世界}（没死过）里带标记、
 * 在 {@code 新的世界 (1)}（有死亡记录 + 维度落点）里标记就没了。</p>
 *
 * <p><b>附件为什么活得下来</b>：restoreFrom 的倒数第四行是
 * {@code EventHooks.onPlayerClone(this, that, !keepEverything)}（ServerPlayer.java:1485），
 * NeoForge 的 {@code AttachmentInternals.onPlayerClone} 顺手把附件从旧玩家拷到新玩家
 * （AttachmentInternals.java:57-59）；死过一次的那种只拷"声明了 copyOnDeath 的"
 * （同文件 :53 的 {@code isDeath ? type -> type.copyOnDeath : type -> true}）——
 * 所以下面**必须**写 {@code .copyOnDeath()}，它是"死后重生也记得"的那把钥匙。
 * 附件随玩家存进 {@code neoforge:attachments}（Entity.java:1795-1797 / 1883），
 * 与本整合包里其它 mod 用的是同一条路（真实存档里就有这个根键）。</p>
 *
 * <p>⚠ 本类必须被模组构造期碰一下（档案 §4.72）：见 {@code PotatoST} 构造器里的
 * {@code ModAttachments.ATTACHMENT_TYPES.register(modEventBus)} 那一行。</p>
 */
public final class ModAttachments {

    public static final DeferredRegister<AttachmentType<?>> ATTACHMENT_TYPES =
            DeferredRegister.create(NeoForgeRegistries.Keys.ATTACHMENT_TYPES, PotatoST.MODID);

    /**
     * 「这本手册已经给过了」= true。默认 false（老玩家升级上来也没这个附件 ⇒ 会补发一本，
     * 这是刻意的：0.12 里靠持久化标记的老账在新机制下不作数时，宁可多发一本也不能不发）。
     *
     * <p>{@code serialize(Codec.BOOL)} ⇒ 写进玩家 NBT 的 {@code neoforge:attachments}；
     * {@code copyOnDeath()} ⇒ 死后重生也带走。</p>
     */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<Boolean>> GUIDE_GIVEN =
            ATTACHMENT_TYPES.register("guide_given", () -> AttachmentType.builder(() -> Boolean.FALSE)
                    .serialize(Codec.BOOL)
                    .copyOnDeath()
                    .build());

    private ModAttachments() {
    }

    /** 探针用：附件是不是真的挂在注册表上、能不能取到值（不依赖真玩家）。 */
    public static boolean isGiven(net.minecraft.world.entity.player.Player player) {
        return Boolean.TRUE.equals(player.getData(GUIDE_GIVEN.get()));
    }

    /** 探针与业务共用的一处写入口 */
    public static void markGiven(net.minecraft.world.entity.player.Player player) {
        player.setData(GUIDE_GIVEN.get(), Boolean.TRUE);
    }
}
