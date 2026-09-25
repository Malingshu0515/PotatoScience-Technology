package com.potatost.mod;

import java.util.Optional;
import java.util.stream.Stream;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.resources.RegistryFixedCodec;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 群系源：包住一个 delegate（本工程 = 原版 multi_noise overworld），在两个"结果恰好是原版群系"
 * 的位置上做替换：
 *
 * <ol>
 *   <li><b>河流 → 咸水河</b>（ZF18 起）：按位置哈希以 {@code chance}（默认 0.75）替换；</li>
 *   <li><b>靠岸的浅海 → 海洋油田</b>（0.11 ZF75，ZF77 改成海里）：原版浅海 {@code minecraft:ocean}
 *       且<b>四邻至少有一个不是海洋</b>（= 贴着岸）时，按位置哈希以 {@code oil_chance}（默认 0.15）替换
 *       —— 用户先要"石岸过渡"，后改口"还是放在海里吧 靠近岸边就行 概率较低"。</li>
 * </ol>
 *
 * <p>注册进 {@code Registries.BIOME_SOURCE}，由
 * {@code data/minecraft/worldgen/world_preset/{normal,amplified,large_biomes}.json} 里
 * overworld 的 {@code generator.biome_source} 引用（delegate = 原版 multi_noise）。</p>
 *
 * <p><b>【旧存档兼容（ZF75 的关键设计）】</b>老世界的 level.dat 里存的是旧配置
 * （只有 {@code delegate/salty_biome/chance}）。所以两个新字段必须是
 * <b>带默认值的可选字段</b>；缺字段时用 {@code salty_biome} 这个 Holder 反查它所属的注册表
 * （{@link Holder.Reference#unwrapLookup()}）把默认的海洋油田群系取出来
 * —— <b>不用开新世界也能吃到新群系</b>。反过来，改名或加必填字段都会让旧存档开图即崩。</p>
 *
 * <p>⚠ <b>咸水河的哈希公式一个字节都不许改</b>（含 CELL_SHIFT 与那两个乘数）：改了之后
 * 旧存档已生成区块与新生成区块的群系边界会错开。油田用**另一套常数**（{@code + 0x5EEDL}）独立算。</p>
 *
 * <p><b>【0.10 ZF18 修正】</b>本注释原先写的是"由 {@code data/minecraft/dimension/overworld.json} 引用"，
 * 但那份 1.5 MB 的 level_stem 覆盖其实**内联了 7609 条 multi_noise 生物群系参数、根本没引用本类**
 * —— 也就是说本类一直是<b>死代码</b>。而且它往 {@code minecraft:level_stem} 注册表塞了一个
 * {@code minecraft:overworld}，<b>优先级压过 world_preset</b>，导致世界创建时的
 * 超平坦 / 放大化 / 大型生物群系 / 单一生物群系**全部失效、一律生成默认地形**。
 * 现已删除该文件，改从 {@code world_preset} 注入（那才是决定世界类型的地方）。
 * 详细取证见开发档案 §4.19。</p>
 */
public class SaltyRiverBiomeSource extends BiomeSource {

    public static final ResourceKey<Biome> SALTY_RIVER = ResourceKey.create(
            Registries.BIOME, ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "salty_river"));

    /** 0.11 ZF75 新增：海洋油田群系。 */
    public static final ResourceKey<Biome> OCEAN_OILFIELD = ResourceKey.create(
            Registries.BIOME, ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ocean_oilfield"));

    public static final DeferredRegister<MapCodec<? extends BiomeSource>> BIOME_SOURCES =
            DeferredRegister.create(Registries.BIOME_SOURCE, PotatoST.MODID);

    public static final DeferredHolder<MapCodec<? extends BiomeSource>, MapCodec<SaltyRiverBiomeSource>> SALTY_RIVER_CODEC =
            BIOME_SOURCES.register("salty_river", () -> SaltyRiverBiomeSource.CODEC);

    /** 判定单元跨度：quart坐标 >> 5 = 128 格一段（想变细改小，比如 >>3 = 32 格） */
    private static final int CELL_SHIFT = 5;

    /** 咸水河默认替换率（旧存档缺字段时用）。 */
    private static final double DEFAULT_CHANCE = 0.75D;

    /** 海洋油田默认替换率（用户："不要太高"）。 */
    private static final double DEFAULT_OIL_CHANCE = 0.15D;

    /** 油田那一套哈希的偏移量：与咸水河用不同的常数，两条规则互不相关。 */
    private static final long OIL_SALT = 0x5EEDL;

    /** {@code #minecraft:is_ocean}：用来判断相邻格"是不是海"（ZF77 近岸判定）。 */
    private static final TagKey<Biome> OCEAN = TagKey.create(Registries.BIOME,
            ResourceLocation.withDefaultNamespace("is_ocean"));

    /** 四个正方向（相邻 1 个 quart 格 = 4 格）。 */
    private static final int[][] NEIGHBOUR_OFFSETS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

    public static final MapCodec<SaltyRiverBiomeSource> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            BiomeSource.CODEC.fieldOf("delegate").forGetter(source -> source.delegate),
            RegistryFixedCodec.create(Registries.BIOME).fieldOf("salty_biome").forGetter(source -> source.saltyBiome),
            Codec.doubleRange(0.0D, 1.0D).optionalFieldOf("chance", DEFAULT_CHANCE).forGetter(source -> source.chance),
            // ↓ 0.11 ZF75：两个**可选**字段（旧存档没有它们，必须能缺省解出来）
            RegistryFixedCodec.create(Registries.BIOME).optionalFieldOf("oil_biome")
                    .forGetter(source -> source.oilBiome),
            Codec.doubleRange(0.0D, 1.0D).optionalFieldOf("oil_chance", DEFAULT_OIL_CHANCE)
                    .forGetter(source -> source.oilChance)
    ).apply(instance, SaltyRiverBiomeSource::new));

    private final BiomeSource delegate;
    private final Holder<Biome> saltyBiome;
    private final double chance;
    private final Optional<Holder<Biome>> oilBiome;
    private final double oilChance;

    /** 实际使用的油田群系；解析不出来就是 null（此时油田规则整个不生效）。 */
    private final Holder<Biome> resolvedOilBiome;

    /** 兼容旧签名（探针与老代码用）：不带海洋油田。 */
    public SaltyRiverBiomeSource(BiomeSource delegate, Holder<Biome> saltyBiome, double chance) {
        this(delegate, saltyBiome, chance, Optional.empty(), DEFAULT_OIL_CHANCE);
    }

    /** codec 用的完整签名。 */
    public SaltyRiverBiomeSource(BiomeSource delegate, Holder<Biome> saltyBiome, double chance,
                                 Optional<Holder<Biome>> oilBiome, double oilChance) {
        this.delegate = delegate;
        this.saltyBiome = saltyBiome;
        this.chance = chance;
        this.oilBiome = oilBiome;
        this.oilChance = oilChance;
        Holder<Biome> resolved = oilBiome.orElse(null);
        if (resolved == null) {
            resolved = defaultOilBiome(saltyBiome);
        }
        this.resolvedOilBiome = resolved;
    }

    /**
     * 旧存档兜底：从 {@code salty_biome} 那个 Holder 反查它所属的注册表，取出默认的海洋油田群系。
     *
     * <p>这就是"不改 level.dat 也能让老世界吃到新群系"的关键 —— 见类注释。
     * 解析失败（比如群系被删了）就返回 null，油田规则静默不生效，绝不让世界加载崩掉。</p>
     */
    private static Holder<Biome> defaultOilBiome(Holder<Biome> salty) {
        if (salty instanceof Holder.Reference<?> reference) {
            try {
                @SuppressWarnings("unchecked")
                HolderLookup.RegistryLookup<Biome> lookup =
                        (HolderLookup.RegistryLookup<Biome>) reference.unwrapLookup();
                return lookup.getOrThrow(OCEAN_OILFIELD);
            } catch (Throwable ignored) {
                return null;
            }
        }
        return null;
    }

    @Override
    protected MapCodec<? extends BiomeSource> codec() {
        return CODEC;
    }

    @Override
    protected Stream<Holder<Biome>> collectPossibleBiomes() {
        Stream<Holder<Biome>> base =
                Stream.concat(this.delegate.possibleBiomes().stream(), Stream.of(this.saltyBiome));
        return this.resolvedOilBiome == null ? base : Stream.concat(base, Stream.of(this.resolvedOilBiome));
    }

    @Override
    public Holder<Biome> getNoiseBiome(int quartX, int quartY, int quartZ, Climate.Sampler sampler) {
        Holder<Biome> original = this.delegate.getNoiseBiome(quartX, quartY, quartZ, sampler);
        if (original.is(Biomes.RIVER) && this.isSaltySection(quartX, quartZ)) {
            return this.saltyBiome;
        }
        if (this.resolvedOilBiome != null && original.is(Biomes.OCEAN)
                && this.isOilSection(quartX, quartZ)
                && this.isCoastalOcean(quartX, quartY, quartZ, sampler)) {
            return this.resolvedOilBiome;
        }
        return original;
    }

    /** 咸水河那一段的判定（**公式与 ZF18 完全一致，不许改**）。 */
    private boolean isSaltySection(int quartX, int quartZ) {
        if (this.chance <= 0.0D) {
            return false;
        }
        if (this.chance >= 1.0D) {
            return true;
        }
        long seed = (long) (quartX >> CELL_SHIFT) * 341873128712L
                + (long) (quartZ >> CELL_SHIFT) * 132897987541L;
        return RandomSource.create(seed).nextDouble() < this.chance;
    }

    /**
     * 「靠岸的浅海」判定（ZF77，用户要求「放在海里、靠近岸边就行」）。
     *
     * <p>四个正方向的**相邻 quart 格**（= 4 格外）里，只要有一个不是海洋
     * （不在 {@code #minecraft:is_ocean} 里，那就意味着石头岸/沙滩/陆地），
     * 就认为这一格是"近岸浅海"。</p>
     *
     * <p>⚠ 顺序很重要：先算便宜的哈希（{@link #isOilSection}），再查邻居 ——
     * 大部分格子在第一步就被否掉，只有命中哈希的格才多花 1~4 次 delegate 查询。</p>
     */
    private boolean isCoastalOcean(int quartX, int quartY, int quartZ, Climate.Sampler sampler) {
        for (int[] offset : NEIGHBOUR_OFFSETS) {
            Holder<Biome> neighbour = this.delegate.getNoiseBiome(
                    quartX + offset[0], quartY, quartZ + offset[1], sampler);
            if (!neighbour.is(OCEAN)) {
                return true;
            }
        }
        return false;
    }

    /** 海洋油田那一段的判定：同一套格子、不同常数（互不相关）。 */
    private boolean isOilSection(int quartX, int quartZ) {
        if (this.oilChance <= 0.0D) {
            return false;
        }
        if (this.oilChance >= 1.0D) {
            return true;
        }
        long seed = (long) (quartX >> CELL_SHIFT) * 341873128712L
                + (long) (quartZ >> CELL_SHIFT) * 132897987541L + OIL_SALT;
        return RandomSource.create(seed).nextDouble() < this.oilChance;
    }

    public static void register(IEventBus modEventBus) {
        BIOME_SOURCES.register(modEventBus);
    }
}
