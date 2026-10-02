package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.BlastFurnaceBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandlerItem;

/**
 * ZF162 临时探针（0.13：删扳手 + 删电力高炉物品形态 + 灌装机放开槽位）。
 *
 * <p><b>三段的判据</b>：</p>
 * <ul>
 *   <li><b>A 注册表事实</b>：扳手物品与电力高炉物品在**服务端真注册表**里已是 air，
 *       而电力高炉**方块**还在；那条配方已从 {@code RecipeManager} 消失；
 *       进度仍能解析，且它的判据挂在我们自建的触发器上。</li>
 *   <li><b>B 装配 → 进度（端到端）</b>：真搭一个 3×3×3、真造一个 {@code PlayerInteractEvent.RightClickBlock}
 *       交给 {@link BlastFurnaceAssembly#onRightClickBlock}（不是绕过它直接调 form()）⇒
 *       结构成型、假玩家的「砌一座高炉」进度真的完成；成型前是未完成（负对照）。</li>
 *   <li><b>C 灌装机</b>：三道门（方块实体 / 手放 / Shift 快移）对任意物品都放行；
 *       灌装两条路都真跑（自家气罐 + **探针当场注册**的一件"别的 mod 的流体容器"）；
 *       四条负对照（不是容器 / 气罐拒液体 / 油桶拒气体 / 质量守恒）。</li>
 * </ul>
 *
 * <p>⚠ 那句关于别的 mod 的容器：探针用 {@code RegisterCapabilitiesEvent} 给
 * {@code minecraft:diamond} 当场挂了一个真 {@link IFluidHandlerItem}（4000 mB 虚拟罐），
 * 走的是**官方能力 API**，与任何第三方 mod 注册自己的容器是同一条路。
 * 另外全物品扫一遍"现在还有哪些物品能被这台机器灌氢"，把结果写进报告
 * —— 用户点名的 Mek 喷气背包到底走不走液体能力，用这一扫如实回答。</p>
 *
 * <p>⚠ 挂载方式：本类**不用** {@code @EventBusSubscriber}（那只能挂 game 总线，
 * 而能力注册必须挂 mod 总线）⇒ 由 {@code PotatoST} 构造期调 {@link #mount(IEventBus)}
 * 两行登记（跑完由卸载脚本把那一行删掉并核对字节）。</p>
 */
public final class Zf162Check {

    private static final String TAG = "[A162] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf162_probe_utf8.txt");

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    /** 探针自己注册的那件"别的 mod 的容器"：最后一次 EXECUTE 灌进去的东西（给质量守恒用）。 */
    private static FluidStack probeHeld = FluidStack.EMPTY;
    private static int probeFills = 0;

    private Zf162Check() {
    }

    /** 由 {@code PotatoST} 构造期调用：①能力（mod 总线）②开服后取证（game 总线）。 */
    public static void mount(IEventBus modEventBus) {
        modEventBus.addListener(Zf162Check::onRegisterCapabilities);
        NeoForge.EVENT_BUS.addListener(Zf162Check::onServerStarted);
    }

    // ================= 探针自己的"别的 mod 的流体容器" =================

    private static void onRegisterCapabilities(RegisterCapabilitiesEvent event) {
        event.registerItem(Capabilities.FluidHandler.ITEM,
                (stack, ctx) -> new ProbeHandler(stack), Items.DIAMOND);
    }

    /**
     * 4000 mB 的虚拟罐：内容物**存进物品的自定义名字**（`probe|<流体 id>|<mB>`），
     * 所以每 tick 新查一次能力也能接着上一次继续灌（像真容器那样），
     * 而且"灌完的物品"与灌之前**不同**（自定义名字变了）⇒ 正好能验
     * {@code tryFillForeignContainer} 里那道"结果与灌前逐字节相同就放弃"的闸门。
     */
    private static final class ProbeHandler implements IFluidHandlerItem {
        private final ItemStack container;
        private FluidStack held = FluidStack.EMPTY;
        private boolean dirtied = false;

        ProbeHandler(ItemStack container) {
            this.container = container;
            this.held = parse(container);
        }

        private static FluidStack parse(ItemStack stack) {
            net.minecraft.network.chat.Component name = stack.get(net.minecraft.core.component.DataComponents.CUSTOM_NAME);
            if (name == null) {
                return FluidStack.EMPTY;
            }
            String s = name.getString();
            if (!s.startsWith("probe|")) {
                return FluidStack.EMPTY;
            }
            String[] parts = s.split("\\|");
            if (parts.length != 3) {
                return FluidStack.EMPTY;
            }
            net.minecraft.world.level.material.Fluid fluid =
                    BuiltInRegistries.FLUID.get(ResourceLocation.parse(parts[1]));
            try {
                return new FluidStack(fluid, Integer.parseInt(parts[2]));
            } catch (NumberFormatException e) {
                return FluidStack.EMPTY;
            }
        }

        @Override
        public ItemStack getContainer() {
            if (!this.dirtied) {
                return this.container;
            }
            ItemStack out = this.container.copyWithCount(1);
            out.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,
                    net.minecraft.network.chat.Component.literal("probe|"
                            + BuiltInRegistries.FLUID.getKey(this.held.getFluid()) + "|" + this.held.getAmount()));
            return out;
        }

        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return this.held;
        }

        @Override
        public int getTankCapacity(int tank) {
            return 4000;
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return true;
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return 0;
            }
            int moved = Math.min(4000 - this.held.getAmount(), resource.getAmount());
            if (action.execute() && moved > 0) {
                this.held = resource.copyWithAmount(this.held.getAmount() + moved);
                this.dirtied = true;
                probeHeld = this.held.copy();
                probeFills++;
            }
            return moved;
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            return FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return FluidStack.EMPTY;
        }
    }

    // ================= 取证 =================

    private static void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        try {
            ServerLevel level = server.overworld();
            checkRegistryFacts(server);
            checkAssembly(level);
            checkFillingMachine(level);
        } catch (Throwable t) {
            fail("EXCEPTION", t.getClass().getName() + ": " + t.getMessage());
            for (StackTraceElement e : t.getStackTrace()) {
                if (e.getClassName().startsWith("com.potatost")) {
                    LINES.add("        at " + e);
                }
            }
        }
        writeReport();
        server.halt(false);
    }

    private static void checkRegistryFacts(MinecraftServer server) {
        LINES.add("== A 段：服务端注册表事实 ==");
        Item wrench = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("potato_s_t", "wrench"));
        check(wrench == Items.AIR, "A1 物品 potato_s_t:wrench 不在注册表里（= air）", wrench.toString());
        Item ebfItem = BuiltInRegistries.ITEM.get(
                ResourceLocation.fromNamespaceAndPath("potato_s_t", "electric_blast_furnace"));
        check(ebfItem == Items.AIR, "A2 物品 potato_s_t:electric_blast_furnace 不在注册表里（= air）",
                ebfItem.toString());
        var ebfBlock = BuiltInRegistries.BLOCK.get(
                ResourceLocation.fromNamespaceAndPath("potato_s_t", "electric_blast_furnace"));
        check(ebfBlock != Blocks.AIR, "A3 但方块 potato_s_t:electric_blast_furnace 仍在注册表里", ebfBlock.toString());
        boolean recipeGone = server.getRecipeManager()
                .byKey(ResourceLocation.fromNamespaceAndPath("potato_s_t", "electric_blast_furnace")).isEmpty();
        check(recipeGone, "A4 配方 potato_s_t:electric_blast_furnace 已从 RecipeManager 消失");
        var holder = server.getAdvancements()
                .get(ResourceLocation.fromNamespaceAndPath("potato_s_t", "blast_furnace"));
        check(holder != null, "A5 进度 potato_s_t:blast_furnace 仍能解析");
        if (holder != null) {
            var criterion = holder.value().criteria().get("got0");
            check(criterion != null && criterion.trigger() == EbfFormedTrigger.EBF_FORMED.get(),
                    "A6 它的判据挂在我们自建的触发器上",
                    criterion == null ? "没有 got0" : criterion.trigger().getClass().getSimpleName());
            var parent = holder.value().parent().orElse(null);
            check(parent != null && parent.equals(ResourceLocation.fromNamespaceAndPath("potato_s_t", "capacitor")),
                    "A7 父节点仍是 potato_s_t:capacitor");
        }
        var steel = server.getAdvancements().get(ResourceLocation.fromNamespaceAndPath("potato_s_t", "steel"));
        check(steel != null && steel.value().parent().orElse(null) != null
                        && steel.value().parent().orElse(null)
                        .equals(ResourceLocation.fromNamespaceAndPath("potato_s_t", "blast_furnace")),
                "A8 子进度 steel 的父节点仍指向 blast_furnace");
        for (String id : new String[]{"potato_s_t:filling_machine", "patchouli:guide_book", "minecraft:blast_furnace"}) {
            ResourceLocation rl = ResourceLocation.parse(id);
            check(BuiltInRegistries.ITEM.get(rl) != Items.AIR
                            || BuiltInRegistries.BLOCK.get(rl) != Blocks.AIR,
                    "A9 手册图标指向的 " + id + " 真实存在");
        }
    }

    /** 真搭结构 + 真造事件 ⇒ 走 {@link BlastFurnaceAssembly#onRightClickBlock} 全路。 */
    private static void checkAssembly(ServerLevel level) {
        LINES.add("== B 段：装配 → 进度（端到端） ==");
        BlockPos controller = level.getSharedSpawnPos().offset(6, 12, 6);
        Direction facing = Direction.NORTH;
        for (int y = 0; y < ElectricBlastFurnaceStructure.HEIGHT; y++) {
            for (int j = 0; j < ElectricBlastFurnaceStructure.SIZE; j++) {
                for (int i = 0; i < ElectricBlastFurnaceStructure.SIZE; i++) {
                    BlockPos p = ElectricBlastFurnaceStructure.offset(controller, facing, i, j, y);
                    level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                }
            }
        }
        // 先铺地板，免得结构悬空（只为可读性，装配本身不查下方）
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                level.setBlock(controller.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 3);
            }
        }
        for (int y = 0; y < ElectricBlastFurnaceStructure.HEIGHT; y++) {
            for (int j = 0; j < ElectricBlastFurnaceStructure.SIZE; j++) {
                for (int i = 0; i < ElectricBlastFurnaceStructure.SIZE; i++) {
                    var kind = ElectricBlastFurnaceStructure.kindAt(i, j, y);
                    BlockPos p = ElectricBlastFurnaceStructure.offset(controller, facing, i, j, y);
                    BlockState state = ElectricBlastFurnaceStructure.blockFor(kind).defaultBlockState();
                    if (kind == ElectricBlastFurnaceStructure.Kind.CONTROLLER) {
                        state = Blocks.BLAST_FURNACE.defaultBlockState().setValue(BlastFurnaceBlock.FACING, facing);
                    }
                    level.setBlock(p, state, 3);
                }
            }
        }
        check(ElectricBlastFurnaceStructure.validate(level, controller, facing) == null,
                "B1 探针搭的 27 格结构校验通过（validate == null）");

        // ⚠ 探针的坑（§4.170）：**NeoForge 不允许给假玩家发进度**
        //   （`PlayerAdvancements.award` 第 170 行：`if (this.player instanceof FakePlayer) return false;`）
        //   ⇒ 用 FakePlayerFactory 验"装配给进度"永远验不出来（实测：award() 直接返回 false）。
        //   这里造一个**不是 FakePlayer 的 ServerPlayer**（匿名子类，只把 displayClientMessage 变空操作），
        //   UUID 唯一 ⇒ 它的 PlayerAdvancements 绑的是它自己，走的就是真玩家登录那一刻的同一条路。
        ServerPlayer actor = new ServerPlayer(level.getServer(), level,
                new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), "zf162actor"),
                net.minecraft.server.level.ClientInformation.createDefault()) {
            @Override
            public void displayClientMessage(net.minecraft.network.chat.Component chatComponent, boolean actionBar) {
                // 探针：不真的发包（真玩家这里会收到一条"电力高炉已成型"）
            }
        };
        actor.setShiftKeyDown(true);
        actor.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        actor.getAdvancements().reload(level.getServer().getAdvancements());
        var advHolder = level.getServer().getAdvancements()
                .get(ResourceLocation.fromNamespaceAndPath("potato_s_t", "blast_furnace"));
        boolean doneBefore = advHolder == null
                || actor.getAdvancements().getOrStartProgress(advHolder).isDone();
        check(!doneBefore, "B2 成型之前：这个玩家的「砌一座高炉」是未完成（负对照）");
        LINES.add("   调试：判据键 = " + (advHolder == null ? "?" : advHolder.value().criteria().keySet())
                + " / 剩余判据 = " + (advHolder == null ? "?"
                : actor.getAdvancements().getOrStartProgress(advHolder).getRemainingCriteria()));

        PlayerInteractEvent.RightClickBlock ev = new PlayerInteractEvent.RightClickBlock(
                actor, InteractionHand.MAIN_HAND, controller,
                new BlockHitResult(Vec3.atCenterOf(controller), Direction.UP, controller, false));
        BlastFurnaceAssembly.onRightClickBlock(ev);

        check(level.getBlockState(controller).is(ModBlocks.ELECTRIC_BLAST_FURNACE.get()),
                "B3 控制器那一格已经变成 potato_s_t:electric_blast_furnace",
                level.getBlockState(controller).toString());
        int parts = 0;
        for (int y = 0; y < ElectricBlastFurnaceStructure.HEIGHT; y++) {
            for (int j = 0; j < ElectricBlastFurnaceStructure.SIZE; j++) {
                for (int i = 0; i < ElectricBlastFurnaceStructure.SIZE; i++) {
                    if (level.getBlockState(ElectricBlastFurnaceStructure.offset(controller, facing, i, j, y))
                            .is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
                        parts++;
                    }
                }
            }
        }
        check(parts == 25, "B4 另外 25 格都变成部件格", "实际 " + parts);
        boolean doneAfter = advHolder != null
                && actor.getAdvancements().getOrStartProgress(advHolder).isDone();
        if (!doneAfter && advHolder != null) {
            var pa = actor.getAdvancements();
            var prog = pa.getOrStartProgress(advHolder);
            var crit = advHolder.value().criteria().get("got0");
            LINES.add("   调试：pa=" + System.identityHashCode(pa)
                    + " actor.getAdvancements()=" + System.identityHashCode(actor.getAdvancements())
                    + " 判据.trigger=" + System.identityHashCode(crit.trigger())
                    + " EBF_FORMED.get()=" + System.identityHashCode(EbfFormedTrigger.EBF_FORMED.get())
                    + " 剩余=" + prog.getRemainingCriteria()
                    + " got0@" + System.identityHashCode(prog.getCriterion("got0")));
            EbfFormedTrigger.EBF_FORMED.get().trigger(actor);
            LINES.add("   调试：trigger() 之后 isDone=" + pa.getOrStartProgress(advHolder).isDone()
                    + " 剩余=" + pa.getOrStartProgress(advHolder).getRemainingCriteria());
            boolean awarded = pa.award(advHolder, "got0");
            LINES.add("   调试：PlayerAdvancements.award()=" + awarded
                    + " 之后 isDone=" + pa.getOrStartProgress(advHolder).isDone());
        }
        check(doneAfter, "B5 成型之后：这个玩家的「砌一座高炉」真的完成了（自建触发器被点亮）");
    }

    private static void checkFillingMachine(ServerLevel level) {
        LINES.add("== C 段：灌装机 ==");
        BlockPos pos = level.getSharedSpawnPos().offset(-6, 12, -6);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            fail("C0", "灌装机方块实体没造出来");
            return;
        }
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);

        // ---- 三道门 ----
        boolean beDoor = be.getInventory().isItemValid(0, new ItemStack(Items.DIAMOND));
        FillingMachineMenu menu = new FillingMachineMenu(0, fake.getInventory(), be);
        boolean menuDoor = menu.slots.get(0).mayPlace(new ItemStack(Items.DIAMOND));
        check(beDoor && menuDoor, "C1 方块实体与菜单手放两道门都收钻石",
                "be=" + beDoor + " menu=" + menuDoor);
        fake.getInventory().setItem(9, new ItemStack(Items.EMERALD));   // 背包第 0 格（物品栏 index 9）
        menu.quickMoveStack(fake, FillingMachineBlockEntity.SLOT_COUNT);  // 菜单 index 5 = 背包第 0 格
        boolean shifted = be.getInventory().getStackInSlot(0).is(Items.EMERALD);
        check(shifted, "C2 Shift 快移把绿宝石塞进了机器槽（第三道门也放行）",
                be.getInventory().getStackInSlot(0).toString());
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);
        fake.getInventory().setItem(9, ItemStack.EMPTY);

        // ---- 自家气罐（ZF73 的老路：判据一字没动）----
        be.getTank(0).fill(new FluidStack(ModFluids.HYDROGEN.get(), 5000), IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        int e0 = be.getEnergy();
        ItemStack tank = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        be.getInventory().setStackInSlot(0, tank);
        for (int t = 0; t < 20; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        ItemStack tankAfter = be.getInventory().getStackInSlot(0);
        FluidStack inTank = ((FluidContainerItem) tankAfter.getItem()).contents(tankAfter);
        int tankLeft = be.getTank(0).getFluidAmount();
        check(tankLeft == 4900 && inTank.getAmount() == 100
                        && inTank.getFluid() == ModFluids.HYDROGEN.get(),
                "C3 自家高压气罐：20 tick 灌进 100 mB 氢气（罐 5000→4900）",
                "罐=" + tankLeft + " 物品=" + inTank.getAmount() + " " + inTank.getFluid());
        check(e0 - be.getEnergy() == 20 * FillingMachineBlockEntity.ENERGY_PER_TANK,
                "C4 电费 20×60 = 1200 FE（按罐计，只在真灌的 tick 扣）",
                "扣了 " + (e0 - be.getEnergy()));

        // ---- 别的 mod 的容器（探针当场注册的能力）----
        // ⚠ 槽 i ↔ 罐 i：所以这里必须用**槽 0**（罐 0 里才是刚才那罐氢气）
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);
        int beforeAmount = be.getTank(0).getFluidAmount();
        int e1 = be.getEnergy();
        probeHeld = FluidStack.EMPTY;
        probeFills = 0;
        be.getInventory().setStackInSlot(0, new ItemStack(Items.DIAMOND));
        for (int t = 0; t < 10; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        ItemStack foreignAfter = be.getInventory().getStackInSlot(0);
        int moved = beforeAmount - be.getTank(0).getFluidAmount();
        String probeName = foreignAfter.get(net.minecraft.core.component.DataComponents.CUSTOM_NAME) == null
                ? "" : foreignAfter.get(net.minecraft.core.component.DataComponents.CUSTOM_NAME).getString();
        check(foreignAfter.is(Items.DIAMOND) && moved == 50
                        && probeName.equals("probe|potato_s_t:hydrogen|50"),
                "C5 跨 mod 容器：10 tick 灌进 50 mB，getContainer() 的结果写回槽位（名字里累计到 50）",
                "槽=" + foreignAfter + " 名字=" + probeName + " 罐减=" + moved);
        check(e1 - be.getEnergy() == 10 * FillingMachineBlockEntity.ENERGY_PER_TANK,
                "C6 跨 mod 那条路的电费同样按罐计", "扣了 " + (e1 - be.getEnergy()));
        check(probeFills == 10, "C7 能力句柄被 EXECUTE 了 10 次（每 tick 一次，没有重复灌）",
                "实际 " + probeFills);

        // ---- 负对照 1：不是容器 ----
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);
        be.getInventory().setStackInSlot(0, new ItemStack(Items.EMERALD));
        int amount2 = be.getTank(0).getFluidAmount();
        int e2 = be.getEnergy();
        for (int t = 0; t < 5; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        check(be.stateOf(0) == FillingMachineBlockEntity.SlotState.UNSUPPORTED
                        && be.getTank(0).getFluidAmount() == amount2 && be.getEnergy() == e2
                        && be.getInventory().getStackInSlot(0).is(Items.EMERALD),
                "C8 负对照：绿宝石（不是容器）⇒ UNSUPPORTED，罐与电一个字节没动",
                "state=" + be.stateOf(0));
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);

        // ---- 负对照 2：气罐拒液体（罐 4 换原油，槽 4 放气罐）----
        be.getTank(4).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 3000), IFluidHandler.FluidAction.EXECUTE);
        be.getInventory().setStackInSlot(4, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        for (int t = 0; t < 3; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        ItemStack gasInOil = be.getInventory().getStackInSlot(4);
        check(be.stateOf(4) == FillingMachineBlockEntity.SlotState.REJECTED
                        && be.getTank(4).getFluidAmount() == 3000
                        && ((FluidContainerItem) gasInOil.getItem()).contents(gasInOil).isEmpty(),
                "C9 负对照：罐里是原油时，高压气罐拒收（用户点名「这两个不要动」）",
                "state=" + be.stateOf(4) + " 罐=" + be.getTank(4).getFluidAmount());
        be.getInventory().setStackInSlot(4, ItemStack.EMPTY);

        // ---- 负对照 3：油桶拒气体（罐 0 是氢气，槽 0 放油桶）----
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        int amount4 = be.getTank(0).getFluidAmount();
        for (int t = 0; t < 3; t++) {
            FillingMachineBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
        ItemStack oilInGas = be.getInventory().getStackInSlot(0);
        check(be.stateOf(0) == FillingMachineBlockEntity.SlotState.REJECTED
                        && be.getTank(0).getFluidAmount() == amount4
                        && ((FluidContainerItem) oilInGas.getItem()).contents(oilInGas).isEmpty(),
                "C10 负对照：罐里是氢气时，油桶拒收",
                "state=" + be.stateOf(0) + " 罐=" + be.getTank(0).getFluidAmount());
        be.getInventory().setStackInSlot(0, ItemStack.EMPTY);

        // ---- 全物品扫：现在还有哪些物品能被这台机器灌氢（含用户点名的 Mek 喷气背包）----
        LINES.add("-- 全物品扫描：谁能被这台机器灌氢气（模拟 100000 mB）--");
        int withHandler = 0;
        List<String> fillable = new ArrayList<>();
        for (Item item : BuiltInRegistries.ITEM) {
            if (item == Items.AIR) {
                continue;
            }
            ItemStack st = new ItemStack(item);
            IFluidHandlerItem h = st.copyWithCount(1).getCapability(Capabilities.FluidHandler.ITEM);
            if (h == null) {
                continue;
            }
            withHandler++;
            int space = h.fill(new FluidStack(ModFluids.HYDROGEN.get(), 100000), IFluidHandler.FluidAction.SIMULATE);
            if (space > 0) {
                fillable.add(BuiltInRegistries.ITEM.getKey(item) + " space=" + space);
            }
        }
        LINES.add("   有物品流体能力的物品共 " + withHandler + " 种；其中能再灌进氢气的 " + fillable.size() + " 种");
        for (int i = 0; i < Math.min(fillable.size(), 25); i++) {
            LINES.add("     " + fillable.get(i));
        }
        for (String id : new String[]{"mekanism:jetpack", "mekanism:jetpack_armored", "mekanism:free_runners",
                "mekanism:basic_fluid_tank", "mekanism:advanced_fluid_tank", "immersiveengineering:jerrycan",
                "mekanism:gas_tank", "mekanism:basic_chemical_tank"}) {
            ResourceLocation rl = ResourceLocation.tryParse(id);
            Item it = rl == null ? Items.AIR : BuiltInRegistries.ITEM.get(rl);
            if (it == Items.AIR) {
                LINES.add("   [查] " + id + "：这个包里没有");
                continue;
            }
            IFluidHandlerItem h = new ItemStack(it).copyWithCount(1)
                    .getCapability(Capabilities.FluidHandler.ITEM);
            LINES.add("   [查] " + id + "：物品流体能力 = " + (h == null ? "没有" : "有"));
        }
        check(true, "C11 三条负对照 + 两条正路全过（详见报告里的扫描段）");
    }

    // ================= 记账 =================

    private static void check(boolean ok, String label) {
        check(ok, label, "");
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label);
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    private static void fail(String code, String detail) {
        failed++;
        LINES.add(TAG + "[FAIL] " + code + " " + detail);
    }

    private static void writeReport() {
        LINES.add("");
        LINES.add("通过 = " + passed + "   失败 = " + failed);
        try {
            Files.createDirectories(REPORT.getParent());
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(REPORT), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
        } catch (IOException e) {
            System.out.println("probe report write failed: " + e);
        }
    }
}
