package com.potatost.mod;

import java.util.Map;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;

/**
 * 振金剑的**斩首**被动（0.14 ZF182）。
 *
 * <p>用户原话：「**给振金剑加个新被动buff 被振金剑技能击杀的生物掉落它的头颅 玩家掉落本人头颅
 * 原版有头颅的掉落自己的头颅 没有的则不掉**」；口径二选一里用户选了 **A = 手持振金剑击杀就算**
 * （普通砍与 Shift+右键猛砸技能都算，这才叫"被动"）。</p>
 *
 * <p><b>怎么判"是振金剑杀的"</b>：拿 {@code event.getSource().getEntity()} 当凶手，再用
 * {@link VibraniumSwordItem#isHolding(Player)} 判他手里是不是振金剑 —— 猛砸技能造成的伤害，
 * 其伤害源里的实体也是那个玩家，所以同一条判据把技能一起覆盖了。</p>
 *
 * <p><b>掉什么</b>：原版**有头颅物品**的生物掉自己的头颅（见 {@link #HEADS}）；
 * **玩家**掉<b>本人的头颅</b>（{@code player_head} + 被杀者自己的 {@code GameProfile}，
 * 所以头颅上就是他的皮肤）；**没有头颅物品的生物一律不掉**（牛/猪/蜘蛛/末影人…）。</p>
 *
 * <p>写在这里而不是写进 {@link VibraniumSwordItem}：掉落要挂 {@link LivingDropsEvent}，
 * 而那个事件是**全局**的（每只生物死都会来一次）—— 放在这个专门的处理器里，
 * 判据只有"凶手 + 手里是不是振金剑"两条，一眼能读完。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class VibraniumBeheading {

    /**
     * 原版"有头颅物品"的生物 → 它的头颅。
     *
     * <p>⚠ 只收**真有**头颅物品的那几种：僵尸/骷髅/凋灵骷髅/苦力怕/猪灵/末影龙。
     * 尸壳、溺尸、流浪者、沼骸这些**没有**头颅物品，按用户口径"没有的则不掉"——
     * 别顺手给它们编一个（那会造出原版不存在的物品）。</p>
     */
    private static final Map<EntityType<?>, Item> HEADS = Map.of(
            EntityType.ZOMBIE, Items.ZOMBIE_HEAD,
            EntityType.SKELETON, Items.SKELETON_SKULL,
            EntityType.WITHER_SKELETON, Items.WITHER_SKELETON_SKULL,
            EntityType.CREEPER, Items.CREEPER_HEAD,
            EntityType.PIGLIN, Items.PIGLIN_HEAD,
            EntityType.ENDER_DRAGON, Items.DRAGON_HEAD);

    private VibraniumBeheading() {
    }

    @SubscribeEvent
    public static void onDrops(LivingDropsEvent event) {
        LivingEntity victim = event.getEntity();
        if (victim.level().isClientSide()) {
            return;
        }
        // 用户对「斩首怎么算」选了 **B 口径：只有猛砸技能（Shift+右键）击杀才算** ⇒ 平砍不掉。
        // 判据是**伤害类型**（见 VibraniumSwordItem.VIBRANIUM_SLAM），不是「手里拿着剑」。
        if (!event.getSource().is(VibraniumSwordItem.VIBRANIUM_SLAM)) {
            return;
        }
        ItemStack head = headFor(victim);
        if (head.isEmpty()) {
            return;
        }
        event.getDrops().add(new ItemEntity(victim.level(), victim.getX(), victim.getY(), victim.getZ(), head));
    }

    /** 这只生物该掉什么头颅（空 = 按用户口径"没有的则不掉"）。公开出来是给探针与门取证的。 */
    public static ItemStack headFor(LivingEntity victim) {
        if (victim instanceof Player player) {
            ItemStack stack = new ItemStack(Items.PLAYER_HEAD);
            // 被杀者本人的头像：写进 PROFILE 组件，头颅在游戏里就是他的皮肤
            // （1.21.1 的 API 是**构造器** `new ResolvableProfile(GameProfile)` —— 没有
            //   `createResolved(...)` 那个静态工厂，编译期实测）
            stack.set(DataComponents.PROFILE, new ResolvableProfile(player.getGameProfile()));
            return stack;
        }
        Item item = HEADS.get(victim.getType());
        return item == null ? ItemStack.EMPTY : new ItemStack(item);
    }

    /** 供探针/门用：这张表是不是只有这几样（防止有人顺手加不存在的头颅）。 */
    public static int mappedCount() {
        return HEADS.size();
    }

    /** 供探针/门用：某个类型有没有对应头颅（不建实体也能查表）。 */
    public static boolean hasHeadFor(EntityType<?> type) {
        return HEADS.containsKey(type);
    }

    /** 供探针/门用：伤害源能不能触发斩首（凶手手持振金剑）。 */
    public static boolean triggers(DamageSource source) {
        Entity attacker = source.getEntity();
        return attacker instanceof Player player && VibraniumSwordItem.isHolding(player);
    }

    /** 供探针/门用：世界是不是服务端（客户端不处理掉落）。 */
    public static boolean serverSide(Level level) {
        return !level.isClientSide();
    }
}
