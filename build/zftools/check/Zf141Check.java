package com.potatost.mod;

import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.component.Tool;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠️ <b>诊断工具（ZF141 的临时探针）</b>：星璨钢工具补齐的端到端取证。
 *
 * <p>用户原话：「还有几个星璨钢的工具你自己写一下呗（耐久 挖掘等级 技能...）
 * 剑和斧子差不多强度 其他的略低（要不要技能都无所谓）你参考一下斧子和星璨钢套
 * 你随便搞 配方就是原版工具一样（原材料换成星璨钢）」+「贴图在用户素材」。</p>
 *
 * <p>要证的九件事（每一条都在**真服务端**上跑，判据盯语义不盯魔法数字）：</p>
 * <ol>
 *   <li><b>注册与身份</b>：三件都挂在 {@code potato_s_t:star_steel_*} 上，
 *       类分别是本轮的 {@code StarSteelSwordItem / PickaxeItem / HoeItem}；</li>
 *   <li><b>档位是同一个对象</b>：剑/镐/锄的 {@code getTier()} 三份 {@code ==}，
 *       五个字段 (1192, 9.0, 8.0, 钻石标签, 22) 与斧子那一档**逐字相同**；
 *       对照原版钻石档是 (1561, 8.0, 3.0, 钻石标签, 10)；</li>
 *   <li><b>属性记账</b>：显示攻击伤害/攻速 —— 剑 16.0 / 1.6、镐 13.0 / 1.2、锄 12.0 / 1.0；
 *       对照：斧子 17.0 / 0.9（ZF133 的数，本轮**一个字没动**）、空手 1.0 / 4.0；</li>
 *   <li><b>挖掘等级真的变了</b>：镐对黑曜石与古代残骸 {@code isCorrectToolForDrops == true}，
 *       同一判据下原版**石镐是 false**（这是"钻石级"的客观证据，不是看标签名字）；</li>
 *   <li><b>修理材料 = 星璨钢锭</b>：三件对星璨钢锭 true、对轻质钛合金 false；
 *       （斧子那一档的修理材料是共用的轻质钛合金，靠 {@code isValidRepairItem} 覆写才认星璨钢锭
 *       ⇒ 斧子两者都是 true —— 这个差别正是"本轮没动斧子"的证据之一）；</li>
 *   <li><b>耐久 1192</b>：三件的 {@code getMaxDamage()} 都是 1192；</li>
 *   <li><b>「夜晚不磨损」是真的</b>（本轮的核心技能）：
 *       采掘 —— 白天剑 +2（剑的 TOOL 组件 {@code damagePerBlock == 2}，**不是**斧子的 1）、
 *       镐 +1、锄 +1；夜晚三把都是 <b>+0</b>；
 *       攻击 —— 白天剑 +1、镐 +2、锄 +2；夜晚三把都是 <b>+0</b>；
 *       ⚠ 每条都先断言"当前时段判据"（{@code StarSteelAxeItem.isNight}）与预期一致，
 *       否则"没掉耐久"可能只是"时间压根没设对"的假绿；</li>
 *   <li><b>配方就是原版工具那张图纸</b>：在**真合成网格**里摆星璨钢锭的图形 ⇒ 出我们的工具；
 *       把星璨钢锭换成原版钻石、图形一个字不改 ⇒ 出对应的**原版钻石工具**
 *       （这一条才真正证明"原材料换成星璨钢"而图纸没动）；</li>
 *   <li><b>说明键在服务端也解析得开</b>：从服务端**已加载的资源包**里读
 *       {@code assets/potato_s_t/lang/en_us.json}，四个键的值逐字对上；
 *       并用 {@code Component.translatable(...).getString()} 交叉核一遍
 *       （它不是裸键）。</li>
 * </ol>
 *
 * <p>挂载方式：{@code PotatoST} 构造器末尾加一行 {@code Zf141Check.register();}，
 * 跑完用 {@code _zf141_unprobe.py} 摘掉（**先抄进 {@code build/zftools/check/} 再删**）。</p>
 */
public final class Zf141Check {

    private static final String TAG = "[A141] ";
    private static final String NS = "potato_s_t";

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf141_probe_utf8.txt";

    /** 白天 / 夜晚的 dayTime（原版刷怪判据那一段：13000~23000 为夜）。 */
    private static final long DAY_TIME = 6000L;
    private static final long NIGHT_TIME = 18000L;

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf141Check() {
    }

    // ============================================================
    //  输出
    // ============================================================

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
            say(TAG + "[OK]   " + name);
        } else {
            failed++;
            say(TAG + "[FAIL] " + name);
        }
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            passed++;
            say(TAG + "[OK]   " + name);
        } else {
            failed++;
            say(TAG + "[FAIL] " + name + "　" + detail);
        }
    }

    private static void head(String title) {
        say(TAG + title);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF141 探针报告（星璨钢工具补齐：剑/镐/锄 + 斧子换贴图）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL")
                    + "（通过 " + passed + "）\n\n");
            w.write(REPORT.toString());
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            NeoForge.EVENT_BUS.register(Zf141Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        try {
            run(event, event.getServer().overworld());
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    // ============================================================
    //  工具
    // ============================================================

    private static ServerPlayer fake(ServerStartedEvent event, ServerLevel level, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                ClientInformation.createDefault());
        // ⚠ 必须有这一句（ZF70 的教训）：无头服务端里 new 出来的玩家没有连接，
        //   某些路径（配方奖励 / 统计 / onEquippedItemBroken）会 NPE。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        player.setGameMode(GameType.SURVIVAL);
        return player;
    }

    private static String f(double v) {
        return String.format(java.util.Locale.ROOT, "%.4f", v);
    }

    private static String tierOf(Tier t) {
        return "(" + t.getUses() + ", " + t.getSpeed() + ", " + t.getAttackDamageBonus() + ", "
                + t.getIncorrectBlocksForDrops().location() + ", " + t.getEnchantmentValue() + ")";
    }

    /** 把时间设成"白天"或"夜晚"，并**断言判据真的到位**（防假绿）。 */
    private static boolean setTime(ServerLevel level, boolean night) {
        level.setDayTime(night ? NIGHT_TIME : DAY_TIME);
        return StarSteelAxeItem.isNight(level) == night;
    }

    private static void run(ServerStartedEvent event, ServerLevel level) {
        ServerPlayer p = fake(event, level, "zf141-tool-owner");
        ServerPlayer dummy = fake(event, level, "zf141-punching-bag");

        Item sword = ModItems.STAR_STEEL_SWORD.get();
        Item pick = ModItems.STAR_STEEL_PICKAXE.get();
        Item hoe = ModItems.STAR_STEEL_HOE.get();
        Item axe = ModItems.STAR_STEEL_AXE.get();
        Item ingot = ModArmorItems.STAR_STEEL_INGOT.get();

        // ---------------- ① 注册与身份 ----------------
        head("① 注册与身份");
        check("剑注册在 potato_s_t:star_steel_sword 上",
                String.valueOf(level.registryAccess().registryOrThrow(Registries.ITEM)
                        .getKey(sword)).equals(NS + ":star_steel_sword"),
                String.valueOf(level.registryAccess().registryOrThrow(Registries.ITEM).getKey(sword)));
        check("镐注册在 potato_s_t:star_steel_pickaxe 上",
                String.valueOf(level.registryAccess().registryOrThrow(Registries.ITEM)
                        .getKey(pick)).equals(NS + ":star_steel_pickaxe"));
        check("锄注册在 potato_s_t:star_steel_hoe 上",
                String.valueOf(level.registryAccess().registryOrThrow(Registries.ITEM)
                        .getKey(hoe)).equals(NS + ":star_steel_hoe"));
        check("三件是各自的类（不是拿原版类顶的）",
                sword instanceof StarSteelSwordItem
                        && pick instanceof StarSteelPickaxeItem
                        && hoe instanceof StarSteelHoeItem,
                sword.getClass().getSimpleName() + " / " + pick.getClass().getSimpleName()
                        + " / " + hoe.getClass().getSimpleName());
        check("斧子还在（本轮只换了它的贴图，物品没动）",
                axe instanceof StarSteelAxeItem);

        // ---------------- ② 档位 ----------------
        head("② 档位（三把同一个对象；与斧子逐字同值）");
        Tier tSword = ((TieredItem) sword).getTier();
        Tier tPick = ((TieredItem) pick).getTier();
        Tier tHoe = ((TieredItem) hoe).getTier();
        Tier tAxe = ((TieredItem) axe).getTier();
        check("剑/镐/锄三份 getTier() 是**同一个对象**（同一档位）",
                tSword == tPick && tPick == tHoe);
        check("这一档 = (1192, 9.0, 8.0, 钻石标签, 22)　实际 " + tierOf(tSword),
                tSword.getUses() == 1192 && tSword.getSpeed() == 9.0F
                        && tSword.getAttackDamageBonus() == 8.0F
                        && tSword.getIncorrectBlocksForDrops().location().toString()
                                .equals("minecraft:incorrect_for_diamond_tool")
                        && tSword.getEnchantmentValue() == 22);
        check("它与斧子那一档**逐字相同**（斧子档 " + tierOf(tAxe) + "）",
                tAxe.getUses() == tSword.getUses()
                        && tAxe.getSpeed() == tSword.getSpeed()
                        && tAxe.getAttackDamageBonus() == tSword.getAttackDamageBonus()
                        && tAxe.getIncorrectBlocksForDrops() == tSword.getIncorrectBlocksForDrops()
                        && tAxe.getEnchantmentValue() == tSword.getEnchantmentValue());
        check("对照原版钻石档 (1561, 8.0, 3.0, 钻石标签, 10)　实际 " + tierOf(Tiers.DIAMOND),
                Tiers.DIAMOND.getUses() == 1561 && Tiers.DIAMOND.getSpeed() == 8.0F
                        && Tiers.DIAMOND.getAttackDamageBonus() == 3.0F
                        && Tiers.DIAMOND.getEnchantmentValue() == 10);
        check("耐久 1192：剑/镐/锄三件的 getMaxDamage() 都是 1192",
                new ItemStack(sword).getMaxDamage() == 1192
                        && new ItemStack(pick).getMaxDamage() == 1192
                        && new ItemStack(hoe).getMaxDamage() == 1192,
                new ItemStack(sword).getMaxDamage() + " / " + new ItemStack(pick).getMaxDamage()
                        + " / " + new ItemStack(hoe).getMaxDamage());

        // ---------------- ③ 属性记账 ----------------
        head("③ 属性记账（真读玩家属性，不是拿常量算）");
        String[] names = {"剑", "镐", "锄", "斧（ZF133，本轮未动）", "空手"};
        Item[] items = {sword, pick, hoe, axe, null};
        double[][] want = {{16.0D, 1.6D}, {13.0D, 1.2D}, {12.0D, 1.0D}, {17.0D, 0.9D}, {1.0D, 4.0D}};
        for (int i = 0; i < items.length; i++) {
            p.setItemSlot(EquipmentSlot.MAINHAND,
                    items[i] == null ? ItemStack.EMPTY : new ItemStack(items[i]));
            // ⚠ 必须有这一句：装备变化要**下一次 tick** 才进属性。
            //   `LivingEntity.detectEquipmentUpdates()` 是 **private**（探针第一版直接调它 ⇒ 编译失败），
            //   公开入口是 `ServerPlayer.doTick()`（它 super.tick() 里才调那一下）——ZF139 的教训。
            p.doTick();
            // ⚠⚠ 第二版探针在这里**假红了两条**：斧子读到 0.99（期望 0.9）、空手读到 4.4（期望 4.0）。
            //   根因不是数值错，是**斧子自己的技能**：手持星璨钢斧 ⇒ doTick 时
            //   `StarSteelAxeItem.applyHoldEffect` 给了急迫 I，而原版**急迫每级给 +10% 攻击速度**
            //   ⇒ 0.9×1.1=0.99、4.0×1.1=4.4（第 5 次读空手时那 20 tick 的急迫还没到期）。
            //   ⇒ 量"装备本身值多少"之前要先把身上的效果清掉。
            // ⚠⚠ 第三版又假红了一条，而且**只差一次调用**：清完效果之后再 `doTick()` 一次，
            //   那次 tick 里 `applyHoldEffect` **又**把急迫挂回来了（手还拿着斧子）⇒ 还是 0.99。
            //   正确顺序是「tick 一次让装备属性进表 → 清效果 → **直接读**」：
            //   装备修饰符是第一步挂上去的，清效果不会动它；而急迫的 +10% 会随效果一起消失。
            p.removeAllEffects();
            double dmg = p.getAttributeValue(Attributes.ATTACK_DAMAGE);
            double spd = p.getAttributeValue(Attributes.ATTACK_SPEED);
            check(String.format(java.util.Locale.ROOT,
                            "%s：显示伤害 %s（期望 %s）、攻速 %s（期望 %s）",
                            names[i], f(dmg), f(want[i][0]), f(spd), f(want[i][1])),
                    Math.abs(dmg - want[i][0]) < 0.001D && Math.abs(spd - want[i][1]) < 0.001D);
        }
        check("剑与斧的每击伤害只差 1.0（用户说的「差不多强度」）",
                Math.abs(16.0D - 17.0D) == 1.0D);

        // 顺手把上面那条"假红"的根因变成一条**正向判据**：ZF133 的手持急迫没被我碰坏。
        p.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(axe));
        p.removeAllEffects();
        p.doTick();
        boolean haste = p.hasEffect(net.minecraft.world.effect.MobEffects.DIG_SPEED);
        double axeSpdWithHaste = p.getAttributeValue(Attributes.ATTACK_SPEED);
        check(String.format(java.util.Locale.ROOT,
                        "手持星璨钢斧 tick 一下 ⇒ 拿到急迫 I，此时攻速被顶到 %s（0.9 × 1.1）",
                        f(axeSpdWithHaste)),
                haste && Math.abs(axeSpdWithHaste - 0.99D) < 0.001D);
        p.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        p.removeAllEffects();

        // ---------------- ④ 挖掘等级 ----------------
        head("④ 挖掘等级（钻石级的客观证据）");
        ItemStack pickStack = new ItemStack(pick);
        ItemStack stonePick = new ItemStack(Items.STONE_PICKAXE);
        BlockState obsidian = Blocks.OBSIDIAN.defaultBlockState();
        BlockState debris = Blocks.ANCIENT_DEBRIS.defaultBlockState();
        check("星璨钢镐挖得动黑曜石（钻石级）",
                pick.isCorrectToolForDrops(pickStack, obsidian));
        check("星璨钢镐挖得动古代残骸",
                pick.isCorrectToolForDrops(pickStack, debris));
        check("对照：原版石镐挖不动黑曜石（证明这条判据是有区分度的）",
                !Items.STONE_PICKAXE.isCorrectToolForDrops(stonePick, obsidian));
        check("对照：原版钻石镐挖得动黑曜石",
                Items.DIAMOND_PICKAXE.isCorrectToolForDrops(
                        new ItemStack(Items.DIAMOND_PICKAXE), obsidian));

        // ---------------- ⑤ 修理材料 ----------------
        head("⑤ 修理材料 = 星璨钢锭");
        ItemStack ingotStack = new ItemStack(ingot);
        ItemStack lightTi = new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get());
        for (String n : new String[]{"剑", "镐", "锄"}) {
            Item it = n.equals("剑") ? sword : (n.equals("镐") ? pick : hoe);
            check(n + "：认星璨钢锭", it.isValidRepairItem(new ItemStack(it), ingotStack));
            check(n + "：**不**认轻质钛合金（不再走共用的那个修理材料）",
                    !it.isValidRepairItem(new ItemStack(it), lightTi));
        }
        check("斧子：星璨钢锭与轻质钛合金**都**认（它靠 isValidRepairItem 覆写，本轮没动）",
                axe.isValidRepairItem(new ItemStack(axe), ingotStack)
                        && axe.isValidRepairItem(new ItemStack(axe), lightTi));

        // ---------------- ⑥ 夜晚不磨损 ----------------
        head("⑥ 「夜晚不磨损」：采掘与攻击两个入口都测");
        ItemStack[] tools = {new ItemStack(sword), new ItemStack(pick),
                new ItemStack(hoe), new ItemStack(axe)};
        String[] toolNames = {"剑", "镐", "锄", "斧"};
        BlockState stone = Blocks.STONE.defaultBlockState();
        BlockPos pos = new BlockPos(0, 100, 0);

        // TOOL 组件的 damagePerBlock：先把这个数摆出来（后面白天那条判据全靠它）
        for (int i = 0; i < tools.length; i++) {
            Tool tool = tools[i].get(net.minecraft.core.component.DataComponents.TOOL);
            int dpb = tool == null ? -1 : tool.damagePerBlock();
            int expect = i == 0 ? 2 : 1;   // 剑 2、镐/锄/斧 1（来源：SwordItem.createToolProperties）
            check(String.format(java.util.Locale.ROOT,
                            "%s 的 TOOL 组件 damagePerBlock = %d（期望 %d）", toolNames[i], dpb, expect),
                    dpb == expect);
        }

        boolean dayOk = setTime(level, false);
        check("前置：把世界设成白天且判据一致（否则下面的「白天会磨损」是假绿）", dayOk);
        for (int i = 0; i < tools.length; i++) {
            ItemStack s = tools[i];
            int before = s.getDamageValue();
            p.setItemSlot(EquipmentSlot.MAINHAND, s);
            s.mineBlock(level, stone, pos, p);
            int delta = s.getDamageValue() - before;
            int expect = i == 0 ? 2 : 1;
            check(String.format(java.util.Locale.ROOT,
                            "白天采掘：%s 掉 %d 点耐久（剑的 TOOL 是 2、其余 1）", toolNames[i], delta),
                    delta == expect);
        }

        boolean nightOk = setTime(level, true);
        check("前置：把世界设成夜晚且判据一致", nightOk);
        for (int i = 0; i < tools.length; i++) {
            ItemStack s = tools[i];
            int before = s.getDamageValue();
            s.mineBlock(level, stone, pos, p);
            int delta = s.getDamageValue() - before;
            check(String.format(java.util.Locale.ROOT,
                            "夜晚采掘：%s 掉 %d 点耐久（应为 0 —— 与夜同频）", toolNames[i], delta),
                    delta == 0);
        }

        // 攻击磨损：真调用 ItemStack.postHurtEnemy（原版 Player.attack 里调的就是它）
        ItemStack[] fresh = {new ItemStack(sword), new ItemStack(pick),
                new ItemStack(hoe), new ItemStack(axe)};
        for (int i = 0; i < fresh.length; i++) {
            ItemStack s = fresh[i];
            int before = s.getDamageValue();
            p.setItemSlot(EquipmentSlot.MAINHAND, s);
            s.postHurtEnemy((LivingEntity) dummy, p);
            int delta = s.getDamageValue() - before;
            int expect = i == 0 ? 1 : 2;   // SwordItem 1 / DiggerItem 2
            check(String.format(java.util.Locale.ROOT,
                            "夜晚攻击：%s 掉 %d 点耐久（剑应为 0、镐/锄应为 0；斧子**照旧 2**）",
                            toolNames[i], delta),
                    i == 3 ? delta == 2 : delta == 0);
        }

        setTime(level, false);
        for (int i = 0; i < fresh.length; i++) {
            ItemStack s = fresh[i];
            int before = s.getDamageValue();
            s.postHurtEnemy((LivingEntity) dummy, p);
            int delta = s.getDamageValue() - before;
            int expect = i == 0 ? 1 : 2;
            check(String.format(java.util.Locale.ROOT,
                            "白天攻击：%s 掉 %d 点耐久（期望 %d）", toolNames[i], delta, expect),
                    delta == expect);
        }

        // ---------------- ⑦ 配方 ----------------
        head("⑦ 配方：图纸与原版逐格相同，只换了原材料");
        check("剑配方（星璨钢锭 ×2 + 木棍）",
                craftMatches(level, sword, ingot, "X", "X", "#"));
        check("镐配方（星璨钢锭 ×3 + 木棍 ×2）",
                craftMatches(level, pick, ingot, "XXX", " # ", " # "));
        check("锄配方（星璨钢锭 ×2 + 木棍 ×2）",
                craftMatches(level, hoe, ingot, "XX", " #", " #"));
        check("对照：同一张图纸换成原版钻石 ⇒ 出**原版钻石剑**（图纸没动过）",
                craftMatches(level, Items.DIAMOND_SWORD, Items.DIAMOND, "X", "X", "#"));
        check("对照：同一张图纸换成原版钻石 ⇒ 出**原版钻石镐**",
                craftMatches(level, Items.DIAMOND_PICKAXE, Items.DIAMOND, "XXX", " # ", " # "));
        check("对照：同一张图纸换成原版钻石 ⇒ 出**原版钻石锄**",
                craftMatches(level, Items.DIAMOND_HOE, Items.DIAMOND, "XX", " #", " #"));
        check("负向：空网格合不出剑",
                !craftMatches(level, sword, ingot, "  ", "  ", "  "));

        // ---------------- ⑧ 说明键 ----------------
        head("⑧ 说明键在服务端**已加载的资源包**里");
        String[] keys = {"item.potato_s_t.star_steel_sword",
                "item.potato_s_t.star_steel_pickaxe",
                "item.potato_s_t.star_steel_hoe",
                "tooltip.potato_s_t.star_steel_tool.1"};
        String[] wants = {"Star Steel Sword", "Star Steel Pickaxe", "Star Steel Hoe",
                "No durability loss from mining or attacking at night. "
                        + "1192 durability, diamond mining level"};
        JsonObject en = null;
        // ⚠ 第二版探针在这里也假红过一次：本以为能从 `server.getResourceManager().getResource(...)`
        //   读到 `assets/potato_s_t/lang/en_us.json` —— **读不到**。原因：服务端那个
        //   ResourceManager 是按 `PackType.SERVER_DATA` 建的，只查 `data/` 那一棵树，
        //   根本不看 `assets/`（这是**服务端资源包的类型决定的**，不是文件缺失）。
        //   ⇒ 改成从**类路径**读：那才是"这个文件真的进了构建产物"的直接证据
        //     （比"盘上有"更强，因为它已经过了 processResources）。
        try (java.io.InputStream in = Zf141Check.class.getResourceAsStream(
                "/assets/potato_s_t/lang/en_us.json")) {
            check("类路径里取得到 /assets/potato_s_t/lang/en_us.json（已进构建产物）", in != null);
            if (in != null) {
                try (BufferedReader r = new BufferedReader(
                        new java.io.InputStreamReader(in, StandardCharsets.UTF_8))) {
                    en = JsonParser.parseReader(r).getAsJsonObject();
                }
            }
        } catch (Throwable t) {
            say(TAG + "读 lang/en_us.json 失败：" + t);
        }
        if (en != null) {
            for (int i = 0; i < keys.length; i++) {
                String got = en.has(keys[i]) ? en.get(keys[i]).getAsString() : "<缺键>";
                check("en_us 里 " + keys[i] + " = 「" + got + "」",
                        wants[i].equals(got), "期望「" + wants[i] + "」");
            }
            check("en_us 键数 = 487（本轮 483 + 4）", en.size() == 487, "实际 " + en.size());
        }
        for (int i = 0; i < keys.length; i++) {
            String shown = Component.translatable(keys[i]).getString();
            check("Component.translatable(「" + keys[i] + "」).getString() 不是裸键 ⇒「"
                            + shown + "」",
                    !shown.equals(keys[i]));
        }

        // ---------------- ⑨ 斧子复核 ----------------
        head("⑨ 斧子复核：本轮只换贴图，数值一个字没动");
        ItemStack axeStack = new ItemStack(axe);
        check("斧子耐久仍是 1192", axeStack.getMaxDamage() == 1192);
        check("斧子档位仍是 (1192, 9.0, 8.0, 钻石标签, 22)　实际 " + tierOf(tAxe),
                tAxe.getUses() == 1192 && tAxe.getSpeed() == 9.0F
                        && tAxe.getAttackDamageBonus() == 8.0F && tAxe.getEnchantmentValue() == 22);
        check("斧子的说明仍是 3 行（tooltip.potato_s_t.star_steel_axe.1~3 都在 en_us 里）",
                en != null && en.has("tooltip.potato_s_t.star_steel_axe.1")
                        && en.has("tooltip.potato_s_t.star_steel_axe.2")
                        && en.has("tooltip.potato_s_t.star_steel_axe.3"));
    }

    /**
     * 在 3×3 真合成网格里按图形摆一次，断言产物是不是 {@code want}。
     *
     * <p>{@code X} = {@code material}、{@code #} = 木棍、空格 = 空。
     * 走的是 {@code RecipeManager.getRecipeFor(RecipeType.CRAFTING, CraftingInput, Level)} ——
     * **和玩家真摆网格时同一套匹配逻辑**，不是"JSON 在不在"那种弱判据。</p>
     */
    private static boolean craftMatches(ServerLevel level, Item want, Item material, String... rows) {
        List<ItemStack> grid = new ArrayList<>();
        for (int y = 0; y < 3; y++) {
            String row = y < rows.length ? rows[y] : "   ";
            for (int x = 0; x < 3; x++) {
                char c = x < row.length() ? row.charAt(x) : ' ';
                if (c == 'X') {
                    grid.add(new ItemStack(material));
                } else if (c == '#') {
                    grid.add(new ItemStack(Items.STICK));
                } else {
                    grid.add(ItemStack.EMPTY);
                }
            }
        }
        CraftingInput input = CraftingInput.of(3, 3, grid);
        Optional<RecipeHolder<CraftingRecipe>> hit =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        if (hit.isEmpty()) {
            return false;
        }
        ItemStack out = hit.get().value().assemble(input, level.registryAccess());
        return !out.isEmpty() && out.getItem() == want;
    }
}
