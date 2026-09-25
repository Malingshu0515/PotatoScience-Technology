package com.potatost.mod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeResolver;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatus;

/**
 * 采油机把一片海洋油田"抽干"成普通海洋（0.11 ZF109）。
 *
 * <p>用户原话：「每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋
 * （冻洋 暖洋 温带海洋...）」。范围单位是<b>区块</b>（用户拍板），
 * 即以机器为中心 <b>10×10 个区块 = 160×160 格</b>。</p>
 *
 * <p><b>⚠ 这里走的是原版 {@code /fillbiome} 那条路，不是"自己找个 setter"：</b>
 * 1.21.1 里 {@code ChunkAccess} <b>没有</b> {@code getBiomes()} / {@code fillBiome(...)} /
 * {@code setBiome(...)}（这几个名字在 5500 个原版类里一个都不存在，
 * 是本轮动手前用 {@code javap} + 源码 jar 逐个核过的，见 §9 ZF109），
 * 能做这件事的公开口子只有一个：
 * {@link ChunkAccess#fillBiomesFromNoise(BiomeResolver, Climate.Sampler)} —— 原版
 * {@code FillBiomeCommand}（{@code /fillbiome} 指令）用的就是它。</p>
 *
 * <p><b>两个坑（都会静默出错，所以写在这里）：</b>
 * <ul>
 *   <li>{@code fillBiomesFromNoise} 会<b>重写整根柱子</b>（它内部 {@code biomes.recreate()}
 *       把 24 个 section 全铺一遍）⇒ 我们的 resolver <b>必须在区域外原样返回旧群系</b>，
 *       否则整根柱子会被"抹平"成一个群系；</li>
 *   <li>改完必须 {@code chunk.setUnsaved(true)}：{@code ChunkMap.save} 看到
 *       {@code !isUnsaved()} 会直接返回，<b>不落盘</b>。</li>
 * </ul>
 *
 * <p><b>通知客户端</b>：{@code chunkMap.resendBiomesForChunks(...)}。
 * ⚠ 1.21.1 这个方法是<b>只发群系调色板</b>（{@code ClientboundChunksBiomesPacket}），
 * 不再整块重发 —— 老教程里那种"重发整块"写法在这里是多余的（也是性能灾难）。
 * 客户端收到后会自己清染色缓存 + 把渲染区块标脏，不需要重登。</p>
 *
 * <p><b>本类不加载区块</b>：没加载的区块直接跳过（为了这 100 个区块去强加载不值当；
 * 正常玩的时候玩家就在机器旁边，±5 个区块本来就在加载范围里）。</p>
 *
 * <p><b>⚠ 必须在服务端主线程调用</b>（我们是从方块实体的服务端 tick 里调的，天然满足）。</p>
 */
public final class OilfieldDepletion {

    /** {@code #minecraft:is_ocean}：投票只认"海"（冻洋 / 暖洋 / 温带海洋 / 深海…）。 */
    private static final TagKey<Biome> OCEAN_TAG = TagKey.create(Registries.BIOME,
            ResourceLocation.withDefaultNamespace("is_ocean"));

    private OilfieldDepletion() {
    }

    /**
     * 一次转化的账（探针要读数）。
     *
     * @param chunks  真正改了群系的区块数
     * @param skipped 没加载、跳过的区块数
     * @param cells   被改掉的<b>群系格子</b>数（quart 格：一个区块最多 24×64）
     * @param target  选中的目标海洋群系
     */
    public record Result(int chunks, int skipped, int cells, Holder<Biome> target) {
    }

    /**
     * 把以 {@code center} 为中心、{@code span}×{@code span} 个区块里所有
     * {@code potato_s_t:ocean_oilfield} 格子改成"旁边那种海洋"。
     *
     * @param span 区块数（用户要的 10）
     */
    public static Result convertAround(ServerLevel level, BlockPos center, int span) {
        int cx = SectionPos.blockToSectionCoord(center.getX());
        int cz = SectionPos.blockToSectionCoord(center.getZ());
        // 偶数个区块的"居中"：机器所在区块算第 span/2+1 个 ⇒ 起点往回 span/2
        int minChunkX = cx - span / 2;
        int minChunkZ = cz - span / 2;

        // ① 收齐加载好的区块
        List<ChunkAccess> loaded = new ArrayList<>(span * span);
        int skipped = 0;
        for (int x = minChunkX; x < minChunkX + span; x++) {
            for (int z = minChunkZ; z < minChunkZ + span; z++) {
                ChunkAccess chunk = level.getChunk(x, z, ChunkStatus.FULL, false);
                if (chunk == null) {
                    skipped++;
                } else {
                    loaded.add(chunk);
                }
            }
        }
        if (loaded.isEmpty()) {
            return new Result(0, skipped, 0, null);
        }

        // ② 目标：区域外一圈投票（票最多者胜；一格海都没有就兜底温带海洋）
        Holder<Biome> target = pickTargetOcean(level, minChunkX, minChunkZ, span, center);

        // ③ 逐格改：只动"海洋油田"，别的原样返回（见类注释第 1 个坑）
        Climate.Sampler sampler = level.getChunkSource().randomState().sampler();
        int[] cells = {0};
        for (ChunkAccess chunk : loaded) {
            BiomeResolver resolver = (qx, qy, qz, s) -> {
                Holder<Biome> current = chunk.getNoiseBiome(qx, qy, qz);
                if (current.is(SaltyRiverBiomeSource.OCEAN_OILFIELD)) {
                    cells[0]++;
                    return target;
                }
                return current;
            };
            chunk.fillBiomesFromNoise(resolver, sampler);
            chunk.setUnsaved(true);          // 缺这句不落盘（见类注释第 2 个坑）
        }

        // ④ 只把群系调色板发给"正在跟踪这些区块"的玩家
        level.getChunkSource().chunkMap.resendBiomesForChunks(loaded);
        return new Result(loaded.size(), skipped, cells[0], target);
    }

    /**
     * 在区域<b>外面那一圈</b>按区块采样，投票选出"旁边是哪种海"。
     *
     * <p>票数相同按群系 id 的字典序取小的那个 —— 同样的地形每次都会得到同样的答案
     * （探针与假刀都要可复现，不能靠 HashMap 的遍历顺序）。</p>
     */
    static Holder<Biome> pickTargetOcean(ServerLevel level, int minChunkX, int minChunkZ,
                                         int span, BlockPos center) {
        Map<ResourceKey<Biome>, Integer> votes = new HashMap<>();
        int y = center.getY();
        for (int x = minChunkX - 1; x <= minChunkX + span; x++) {
            vote(level, votes, (x << 4) + 8, y, ((minChunkZ - 1) << 4) + 8);
            vote(level, votes, (x << 4) + 8, y, ((minChunkZ + span) << 4) + 8);
        }
        for (int z = minChunkZ; z < minChunkZ + span; z++) {
            vote(level, votes, ((minChunkX - 1) << 4) + 8, y, (z << 4) + 8);
            vote(level, votes, ((minChunkX + span) << 4) + 8, y, (z << 4) + 8);
        }
        ResourceKey<Biome> best = null;
        int bestVotes = -1;
        for (Map.Entry<ResourceKey<Biome>, Integer> entry : votes.entrySet()) {
            if (entry.getValue() > bestVotes
                    || (entry.getValue() == bestVotes && best != null
                        && entry.getKey().compareTo(best) < 0)) {
                best = entry.getKey();
                bestVotes = entry.getValue();
            }
        }
        // 一格海都没投出来（比如机器贴着海底山脉）⇒ 兜底温带海洋 minecraft:ocean
        ResourceKey<Biome> key = best != null ? best : Biomes.OCEAN;
        return level.registryAccess().lookupOrThrow(Registries.BIOME).getOrThrow(key);
    }

    private static void vote(ServerLevel level, Map<ResourceKey<Biome>, Integer> votes,
                             int x, int y, int z) {
        Holder<Biome> holder = level.getBiome(new BlockPos(x, y, z));
        if (!holder.is(OCEAN_TAG) || holder.is(SaltyRiverBiomeSource.OCEAN_OILFIELD)) {
            return;
        }
        holder.unwrapKey().ifPresent(key -> votes.merge(key, 1, Integer::sum));
    }
}
