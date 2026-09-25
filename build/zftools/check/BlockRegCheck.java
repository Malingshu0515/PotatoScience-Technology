package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF34 临时文件，验证完必须删）</b>：验 6 个装饰方块真的"完整可用"。
 *
 * <p>为什么需要它：这几个方块最可能的坏法**都不报错、不崩溃**——
 * <ul>
 *   <li>注册漏了一个 ⇒ 创造页里没有 / 放不出来；</li>
 *   <li>忘了登记 {@code minecraft:mineable/pickaxe} 或 {@code minecraft:needs_stone_tool}
 *       ⇒ 方块看得见、挖得动，但<b>挖下去什么都不掉</b>（最容易漏、最难发现）；</li>
 *   <li>掉落表路径写错 ⇒ 同上，静默不掉落。</li>
 * </ul>
 * 所以这里不看代码，直接<b>量行为</b>：拿钻石镐 / 木镐 / 空手各挖一次，看掉落。</p>
 *
 * <p><b>用法</b>：临时放进 {@code com.potatost.mod}、在 {@code PotatoST} 构造器里
 * {@code BlockRegCheck.register()}，然后 {@code gradlew runServer}；
 * 日志出现 {@code [BLOCKCHECK]} 若干行后自动关服。<b>验证完连同注册行一起删掉。</b></p>
 */
public final class BlockRegCheck {

    private static final String TAG = "[BLOCKCHECK] ";
    private static final String[] IDS = {
            "common_metal_block", "advanced_metal_block", "stable_metal_block",
            "heat_resistant_metal_block", "heater", "heat_sink", "wiring_block"
    };

    private static boolean registered;

    private BlockRegCheck() {
    }

    /** 挂 game 总线（{@code ServerStartedEvent} 是 game 事件，挂 mod 总线会静默失败 —— 档案 §4.20）。 */
    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(BlockRegCheck.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败（不影响正式功能）：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event.getServer().overworld());
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed = 1;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0
                    ? IDS.length + " 个方块全部完整可用"
                    : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    private static int run(ServerLevel level) {
        int failed = 0;
        BlockPos pos = BlockPos.ZERO;
        ItemStack diamond = new ItemStack(Items.DIAMOND_PICKAXE);
        ItemStack wood = new ItemStack(Items.WOODEN_PICKAXE);

        System.out.println(TAG + "开始验 6 个装饰方块");

        for (String id : IDS) {
            ResourceLocation rl = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, id);
            System.out.println(TAG + "---- " + rl + " ----");

            // ① 方块注册
            if (!BuiltInRegistries.BLOCK.containsKey(rl)) {
                failed += bad("方块已在注册表");
                continue;
            }
            Block block = BuiltInRegistries.BLOCK.get(rl);
            failed += ok("方块已在注册表：" + block.getClass().getSimpleName());
            BlockState state = block.defaultBlockState();

            // ② 物品注册（BlockItem）
            failed += check("物品已在注册表（BlockItem）",
                    BuiltInRegistries.ITEM.containsKey(rl)
                            && BuiltInRegistries.ITEM.get(rl) instanceof net.minecraft.world.item.BlockItem);

            // ③ 源码意图：必须用正确工具挖
            failed += check("requiresCorrectToolForDrops = true", state.requiresCorrectToolForDrops());

            // ④⑤ 两张原版标签 —— 漏了就是"能挖但不掉落"
            failed += check("在 #minecraft:mineable/pickaxe 里", state.is(BlockTags.MINEABLE_WITH_PICKAXE));
            failed += check("在 #minecraft:needs_stone_tool 里", state.is(BlockTags.NEEDS_STONE_TOOL));

            // ⑥ 掉落表能否查到自己。
            // ⚠ 这一条**只验掉落表路径对不对**，不验工具等级 —— Block.getDrops(...) 是纯掉落表通道，
            //   它压根不看 requiresCorrectToolForDrops（第一版探针就是在这里想当然，见下方 ⑦）。
            List<ItemStack> got = Block.getDrops(state, level, pos, null, null, diamond);
            boolean selfDrop = got.size() == 1
                    && got.get(0).getCount() == 1
                    && got.get(0).getItem() == block.asItem();
            failed += check("掉落表能查到自己（钻石镐，实际 " + describe(got) + "）", selfDrop);

            // ⑦ 工具等级：用**和游戏完全相同的那条判据**（反汇编 Player.hasCorrectToolForDrops）：
            //      !state.requiresCorrectToolForDrops() || inventory.getSelected().isCorrectToolForDrops(state)
            //    这才是 ServerPlayerGameMode.destroyBlock 里那道门：
            //      destroyBlock → BlockState.canHarvestBlock → IBlockExtension.canHarvestBlock
            //        → EventHooks.doPlayerHarvestCheck → Player.hasCorrectToolForDrops
            //    门不过 ⇒ playerDestroy 不会被调用 ⇒ 方块照样消失但**什么都不掉**。
            failed += check("钻石镐算正确工具（会掉落）", hasCorrectTool(state, diamond));
            failed += check("木镐不算（needs_stone_tool 生效 ⇒ 挖了不掉）", !hasCorrectTool(state, wood));
            failed += check("空手不算（挖了不掉）", !hasCorrectTool(state, ItemStack.EMPTY));
        }
        return failed;
    }

    /** 复刻 {@code Player.hasCorrectToolForDrops(BlockState)} 的判据（探针里没有 Player 可用）。 */
    private static boolean hasCorrectTool(BlockState state, ItemStack tool) {
        return !state.requiresCorrectToolForDrops() || tool.isCorrectToolForDrops(state);
    }

    private static String describe(List<ItemStack> stacks) {
        if (stacks.isEmpty()) {
            return "空";
        }
        StringBuilder sb = new StringBuilder();
        for (ItemStack s : stacks) {
            if (sb.length() > 0) {
                sb.append(" + ");
            }
            sb.append(s.getCount()).append("×").append(BuiltInRegistries.ITEM.getKey(s.getItem()));
        }
        return sb.toString();
    }

    private static int ok(String name) {
        System.out.println(TAG + "  [OK]   " + name);
        return 0;
    }

    private static int bad(String name) {
        System.out.println(TAG + "  [FAIL] " + name);
        return 1;
    }

    private static int check(String name, boolean pass) {
        return pass ? ok(name) : bad(name);
    }
}
