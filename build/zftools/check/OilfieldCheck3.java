package com.potatost.mod;

import java.util.Optional;
import java.util.stream.Stream;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF77). Delete after the run.
 *
 * <p>Checks the coastal-ocean rule and that a brand-new world generated at all
 * (reaching ServerStartedEvent already proves new-chunk generation works).</p>
 */
public final class OilfieldCheck3 {

    private static final String TAG = "[F77] ";
    private static final ResourceKey<Biome> OIL = SaltyRiverBiomeSource.OCEAN_OILFIELD;
    private static final ResourceLocation PLACED =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "mini_oilfield_placed");
    private static final ResourceLocation DENSE =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "mini_oilfield_placed_dense");
    private static boolean registered;
    private static int failed;

    private OilfieldCheck3() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(OilfieldCheck3.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            System.out.println(TAG + "NEW WORLD GENERATED OK (this event only fires after spawn chunks exist)");
            var reg = level.registryAccess().registryOrThrow(Registries.BIOME);
            Biome biome = reg.get(OIL);
            failed += check("biome registered", biome != null);
            Object color = biome == null ? null
                    : biome.getClass().getMethod("getWaterColor").invoke(biome);
            failed += check("water colour 4212653", color instanceof Integer i && i == 4212653);
            failed += check("name = Ocean Oilfield", "Ocean Oilfield".equals(
                    net.minecraft.network.chat.Component.translatable("biome.potato_s_t.ocean_oilfield")
                            .getString()));
            failed += check("in #minecraft:is_overworld", reg.getHolderOrThrow(OIL).is(
                    TagKey.create(Registries.BIOME, ResourceLocation.withDefaultNamespace("is_overworld"))));

            int plains = count(level, Biomes.PLAINS, PLACED);
            int desertP = count(level, Biomes.DESERT, PLACED);
            int desertD = count(level, Biomes.DESERT, DENSE);
            int oceanP = count(level, Biomes.OCEAN, PLACED);
            int oil = count(level, OIL, PLACED);
            System.out.println(TAG + "    injections -> plains=" + plains + " desert=" + desertP + "+"
                    + desertD + " ocean=" + oceanP + " oilfield=" + oil);
            failed += check("plains 1x", plains == 1);
            failed += check("desert 2 distinct features (200 + 100 = 3x)", desertP == 1 && desertD == 1);
            failed += check("ocean 1x", oceanP == 1);
            failed += check("oilfield biome 1x", oil == 1);

            // 近岸规则：合成 delegate —— x>=0 是海、x<0 是陆地 ⇒ x=0 那一列是"靠岸的浅海"
            Holder<Biome> oceanH = reg.getHolderOrThrow(Biomes.OCEAN);
            Holder<Biome> landH = reg.getHolderOrThrow(Biomes.PLAINS);
            Holder<Biome> salty = reg.getHolderOrThrow(SaltyRiverBiomeSource.SALTY_RIVER);
            Holder<Biome> oilH = reg.getHolderOrThrow(OIL);
            BiomeSource coast = new FakeCoast(oceanH, landH);
            SaltyRiverBiomeSource all = new SaltyRiverBiomeSource(coast, salty, 0.0D,
                    Optional.of(oilH), 1.0D);
            SaltyRiverBiomeSource off = new SaltyRiverBiomeSource(coast, salty, 0.0D,
                    Optional.of(oilH), 0.0D);
            failed += check("coastal shallow ocean -> oilfield (chance 1.0)",
                    all.getNoiseBiome(0, 64, 5, null).is(OIL));
            failed += check("offshore ocean NOT replaced (no land neighbour)",
                    !all.getNoiseBiome(40, 64, 40, null).is(OIL));
            failed += check("chance 0.0 -> nothing replaced", !off.getNoiseBiome(0, 64, 5, null).is(OIL));
            failed += check("biome source is ours in this new world",
                    level.getChunkSource().getGenerator().getBiomeSource() instanceof SaltyRiverBiomeSource);
        } catch (Throwable t) {
            System.out.println(TAG + "exception: " + t);
            t.printStackTrace();
            failed++;
        } finally {
            System.out.println(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
            System.out.println(TAG + "done, halting server");
            event.getServer().halt(false);
        }
    }

    private static int count(ServerLevel level, ResourceKey<Biome> key, ResourceLocation feature) {
        Biome biome = level.registryAccess().registryOrThrow(Registries.BIOME).get(key);
        if (biome == null) {
            return -1;
        }
        int n = 0;
        for (HolderSet<PlacedFeature> step : biome.getGenerationSettings().features()) {
            for (Holder<PlacedFeature> h : step) {
                if (h.unwrapKey().map(k -> k.location().equals(feature)).orElse(false)) {
                    n++;
                }
            }
        }
        return n;
    }

    /** x >= 0 返回海、x < 0 返回陆地 ⇒ x=0 那一列四邻里有一个是陆地。 */
    private static final class FakeCoast extends BiomeSource {
        private final Holder<Biome> ocean;
        private final Holder<Biome> land;

        FakeCoast(Holder<Biome> ocean, Holder<Biome> land) {
            this.ocean = ocean;
            this.land = land;
        }

        @Override
        protected MapCodec<? extends BiomeSource> codec() {
            return null;
        }

        @Override
        protected Stream<Holder<Biome>> collectPossibleBiomes() {
            return Stream.of(this.ocean, this.land);
        }

        @Override
        public Holder<Biome> getNoiseBiome(int x, int y, int z, Climate.Sampler sampler) {
            return x >= 0 ? this.ocean : this.land;
        }
    }

    private static int check(String what, boolean ok) {
        System.out.println(TAG + (ok ? "[OK]   " : "[FAIL] ") + what);
        return ok ? 0 : 1;
    }
}
