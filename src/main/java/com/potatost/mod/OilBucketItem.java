package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * 油桶（0.11 ZF73）。
 *
 * <p>用户原话：「套用高压气罐那一套但是改了点东西（白色容量条、显示容器内液体等不变）
 * … 油桶目前可以舀取石油在内的任何液体（灌装机内也可以放油桶 不可以罐装气体）
 * … 单个油桶为3000mB的容积 … 只可以存在一种流体 异种流体不可以再被灌装进油桶」。</p>
 *
 * <ul>
 *   <li>容量 3000 mB、**只装一种**液体（异种拒收）、**装不进气体**；</li>
 *   <li>白色容量条 = 复用气罐那三个覆写（{@link #isBarVisible}/{@link #getBarWidth}/{@link #getBarColor}）；</li>
 *   <li>世界里右键**舀**任何液体：原版 {@code BucketItem} 只认自己那一种流体，所以自己写
 *       （一次一格源方块 = 1000 mB，三格装满）；</li>
 *   <li><b>本轮不做倒出/放置</b>（用户没要求，见 v0.11 规划 §5 待决 2）；</li>
 *   <li>原油在世界上是 {@code potato_s_t:crude_oil} 液体方块，不无限（{@code canConvertToSource=false}），
 *       所以舀干一片油田就是真的舀干了。</li>
 * </ul>
 */
public class OilBucketItem extends Item implements FluidContainerItem {

    /** 满条宽度（原版常数 {@code Item.MAX_BAR_WIDTH}）。 */
    private static final int BAR_FULL_WIDTH = 13;

    /**
     * 右键够得着的距离。原版空桶用的是玩家方块交互距离属性，
     * 这里直接用 4.5 格常数（和创造/生存默认一致），少一处 API 依赖。
     */
    private static final double REACH = 4.5D;

    public OilBucketItem(Properties properties) {
        super(properties);
    }

    // ===================== 白色容量条（与高压气罐同款表现） =====================

    @Override
    public boolean isBarVisible(ItemStack stack) {
        return OilBucketContents.amount(stack) > 0;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        int amount = OilBucketContents.amount(stack);
        if (amount <= 0) {
            return 0;
        }
        return (int) Math.round((double) BAR_FULL_WIDTH
                * Math.min(amount, OilBucketContents.CAPACITY) / OilBucketContents.CAPACITY);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return 0xFFFFFF;
    }

    // ===================== tooltip =====================

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
        if (!tooltipFlag.hasShiftDown() && !tooltipFlag.isAdvanced()) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
            return;
        }
        tooltipComponents.add(Component.translatable("tooltip.potato_s_t.oil_bucket.total",
                OilBucketContents.amount(stack), OilBucketContents.CAPACITY));
        if (OilBucketContents.isEmpty(stack)) {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.oil_bucket.empty"));
        } else {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.oil_bucket.entry",
                    OilBucketContents.fluid(stack).getFluidType().getDescription(),
                    OilBucketContents.amount(stack)));
        }
        tooltipComponents.add(Component.translatable("tooltip.potato_s_t.oil_bucket.rule"));
    }

    // ===================== 舀取 =====================

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        Vec3 eye = player.getEyePosition(1.0F);
        Vec3 look = player.getViewVector(1.0F);
        BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(
                look.x * REACH, look.y * REACH, look.z * REACH),
                ClipContext.Block.OUTLINE, ClipContext.Fluid.SOURCE_ONLY, player));
        if (hit.getType() != HitResult.Type.BLOCK) {
            return InteractionResultHolder.pass(stack);
        }
        BlockPos pos = hit.getBlockPos();
        if (!level.mayInteract(player, pos)) {
            return InteractionResultHolder.pass(stack);
        }
        if (level.isClientSide()) {
            // 客户端只回一个挥手动作，落改动全交给服务端（能不能舀由 scoopAt 判）
            return InteractionResultHolder.success(stack);
        }
        if (scoopAt(level, pos, stack) > 0) {
            return InteractionResultHolder.success(stack);
        }
        return InteractionResultHolder.pass(stack);
    }

    /**
     * 从 {@code pos} 舀一格源方块进桶（服务端调用；探针也直接调它，所以是 public static）。
     *
     * <p>拒绝的四种情形：不是源方块 / 不是液体（气体本来也没有方块）/ 桶里已有异种流体 /
     * 桶里剩下的空间不足 1000 mB（避免"舀半格、剩下半格凭空消失"）。</p>
     *
     * @return 实际舀到的 mB（0 = 没舀成）
     */
    public static int scoopAt(Level level, BlockPos pos, ItemStack stack) {
        if (level.isClientSide() || stack.isEmpty()) {
            return 0;
        }
        FluidState state = level.getFluidState(pos);
        if (!state.isSource()) {
            return 0;
        }
        Fluid fluid = state.getType();
        if (!OilBucketContents.accepts(fluid)) {
            return 0;
        }
        Fluid have = OilBucketContents.fluid(stack);
        if (have != Fluids.EMPTY && have != fluid) {
            return 0;
        }
        if (OilBucketContents.space(stack) < OilBucketContents.SOURCE_AMOUNT) {
            return 0;
        }
        int moved = OilBucketContents.fill(stack,
                new FluidStack(fluid, OilBucketContents.SOURCE_AMOUNT),
                OilBucketContents.SOURCE_AMOUNT);
        if (moved <= 0) {
            return 0;
        }
        // 抽掉这格源方块：原油不无限（canConvertToSource=false），舀掉就是真的少一格
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.gameEvent(null, GameEvent.FLUID_PICKUP, pos);
        level.playSound(null, pos,
                fluid == Fluids.LAVA ? SoundEvents.BUCKET_FILL_LAVA : SoundEvents.BUCKET_FILL,
                SoundSource.BLOCKS, 1.0F, 1.0F);
        return moved;
    }

    // ===================== FluidContainerItem（灌装机用） =====================

    @Override
    public int space(ItemStack stack) {
        return OilBucketContents.space(stack);
    }

    @Override
    public boolean accepts(Fluid fluid) {
        return OilBucketContents.accepts(fluid);
    }

    @Override
    public int fill(ItemStack stack, FluidStack fluid, int maxAmount) {
        return OilBucketContents.fill(stack, fluid, maxAmount);
    }

    @Override
    public boolean isEmpty(ItemStack stack) {
        return OilBucketContents.isEmpty(stack);
    }

    // ---- 0.11 ZF78：取出来（操作器右键倒油用）----

    @Override
    public FluidStack contents(ItemStack stack) {
        Fluid fluid = OilBucketContents.fluid(stack);
        if (fluid == null || fluid == Fluids.EMPTY) {
            return FluidStack.EMPTY;
        }
        return new FluidStack(fluid, OilBucketContents.amount(stack));
    }

    @Override
    public FluidStack drain(ItemStack stack, int maxAmount) {
        return OilBucketContents.drain(stack, maxAmount);
    }
}
