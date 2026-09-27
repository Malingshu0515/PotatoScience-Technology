package com.potatost.mod;

import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import vazkii.patchouli.api.PatchouliAPI;

/**
 * 教程手册（0.12 ZF148）—— 帕秋莉（Patchouli）联动。
 *
 * <p>用户原话：「你看看能不能联动帕秋莉手册或者自己做个书 教程向的 开局给一个
 * 或者一本书+一个铁锭合成」。拍板结果：**联动帕秋莉** + **开局送一本** +
 * **书 + 铁锭可再合成**。</p>
 *
 * <p><b>书在哪</b>：{@code data/potato_s_t/patchouli_books/guide/book.json}
 * ＋ {@code assets/potato_s_t/patchouli_books/guide/en_us/{categories,entries}/…}。
 * 1.20 起帕秋莉要求 {@code use_resource_pack: true}：**书定义留在 data/、内容搬进 assets/**，
 * 正文按语言目录找，找不到就回退 {@code en_us}（{@code BookContentsBuilder.loadLocalizedJson}
 * 先试当前语言、再回退基路径 —— 已从 jar 字节码核实）。</p>
 *
 * <p><b>为什么正文一句中文都没写进 JSON</b>：`book.json` 开了 {@code i18n: true}，
 * 于是分类名、条目名与**每页正文**都先去语言文件里查键 —— 键叫
 * {@code potato_s_t.guide.entry.<分类>.<条目>.p<n>}，五份 lang 里各有一条。
 * 这样文案与全仓的「键数活体数字」口径合流，改文案不必碰数据结构。</p>
 *
 * <p><b>物品形态</b>：用帕秋莉自己注册的 {@code patchouli:guide_book}，
 * 靠数据组件 {@code patchouli:book = potato_s_t:guide} 区分是哪本书（
 * {@code ItemModBook.getBook} 只读这个组件，没有组件就是一本废书）。
 * 所以本类**不注册任何物品**，配方产物也是带组件的那件原版物品
 * （见 {@code data/potato_s_t/recipe/guide_book.json}）。</p>
 *
 * <p><b>开局送一本</b>：登录时给一次，标记记在玩家的持久化数据里
 * （{@code ServerPlayer.getPersistentData()}，随存档走，不随会话走）。
 * 老存档里已经玩过的玩家在这条上线后**也会补一本** —— 标记一开始是空的。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class GuideBook {

    /** 本书的 id，必须与 {@code data/potato_s_t/patchouli_books/<name>/} 的目录名一致。 */
    public static final ResourceLocation BOOK_ID =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "guide");

    /** 「已经送过」的标记键（玩家持久化数据里）。 */
    private static final String GIVEN_TAG = "potato_s_t_guide_given";

    private GuideBook() {
    }

    /**
     * 第一次登录时送一本手册。
     *
     * <p>⚠ 拿不到书堆就**不打标记**直接返回：这样在书数据还没加载出来的极端情况下，
     * 下次登录还会再试一次，不会把这次机会永久吞掉（与 ZF146 那条「状态别写死」同族）。</p>
     */
    @SubscribeEvent
    public static void onPlayerLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (player.getPersistentData().getBoolean(GIVEN_TAG)) {
            return;
        }
        ItemStack book = PatchouliAPI.get().getBookStack(BOOK_ID);
        if (book.isEmpty()) {
            return;
        }
        player.getPersistentData().putBoolean(GIVEN_TAG, true);
        // 背包塞不下就掉在脚下，别静悄悄把书吞了
        if (!player.getInventory().add(book)) {
            player.drop(book, false);
        }
        player.displayClientMessage(
                Component.translatable("message.potato_s_t.guide_book.received"), false);
    }
}
