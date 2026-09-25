package com.potatost.mod;

import java.util.Optional;
import java.util.stream.Stream;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF75). Delete after the run.
 *
 * <p>Worldgen probe. The rule test uses a SYNTHETIC delegate (always returns stony shore),
 * so it never depends on climate sampling or on how lucky the dev world happens to be.</p>
 */
public final class OilfieldCheck {

    private static final String TAG = "[F75] ";
    private static final ResourceKey<Biome> OIL_BIOME = SaltyRiverBiomeSource.OCEAN_OILFIELD;
    private static final ResourceLocation OIL_PLACED =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "mini_oilfield_placed");
    private static boolean registered;
    private static int failed;

    private OilfieldCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(OilfieldCheck.class);
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
            checkBiome(level);
            checkModifiers(level);
            checkRule(level);
            checkPlaceFeature(event, level);
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

    private static void checkBiome(ServerLevel level) {
        System.out.println(TAG + "(1) ocean oilfield biome");
        Biome biome = level.registryAccess().registryOrThrow(Registries.BIOME).get(OIL_BIOME);
        failed += check("biome potato_s_t:ocean_oilfield is registered", biome != null);
        if (biome == null) {
            return;
        }
        Object color = callDeclared(biome, "getWaterColor", new Class<?>[0]);
        System.out.println(TAG + "    water_color = " + color);
        failed += check("water colour = 4212653 (0x4047AD)", color instanceof Integer i && i == 4212653);
        failed += check("biome name resolves = Ocean Oilfield", "Ocean Oilfield".equals(
                net.minecraft.network.chat.Component.translatable("biome.potato_s_t.ocean_oilfield").getString()));
        TagKey<Biome> isOverworld = TagKey.create(Registries.BIOME,
                ResourceLocation.withDefaultNamespace("is_overworld"));
        failed += check("biome is in #minecraft:is_overworld",
                level.registryAccess().registryOrThrow(Registries.BIOME).getHolderOrThrow(OIL_BIOME)
                        .is(isOverworld));

        BiomeSource source = level.getChunkSource().getGenerator().getBiomeSource();
        System.out.println(TAG + "    dev-world biome source = " + source.getClass().getName());
        if (source instanceof SaltyRiverBiomeSource) {
            failed += check("possibleBiomes contains the oil biome", has(source, OIL_BIOME));
            failed += check("possibleBiomes still contains the salty river",
                    has(source, SaltyRiverBiomeSource.SALTY_RIVER));
        } else {
            System.out.println(TAG + "    [SKIP] this dev world bakes the VANILLA biome source in level.dat"
                    + " -- the wiring is covered by (3) with a synthetic delegate");
        }
    }

    private static boolean has(BiomeSource source, ResourceKey<Biome> key) {
        return source.possibleBiomes().stream()
                .anyMatch(h -> h.unwrapKey().map(k -> k.equals(key)).orElse(false));
    }

    private static void checkModifiers(ServerLevel level) {
        System.out.println(TAG + "(2) biome modifiers injected the lake feature");
        failed += check("placed feature is registered", level.registryAccess()
                .registryOrThrow(Registries.PLACED_FEATURE)
                .containsKey(ResourceKey.create(Registries.PLACED_FEATURE, OIL_PLACED)));
        failed += check("configured feature is registered", level.registryAccess()
                .registryOrThrow(Registries.CONFIGURED_FEATURE)
                .containsKey(ResourceKey.create(Registries.CONFIGURED_FEATURE,
                        ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "mini_oilfield"))));
        int plains = count(level, Biomes.PLAINS);
        int desert = count(level, Biomes.DESERT);
        int badlands = count(level, Biomes.BADLANDS);
        int oil = count(level, OIL_BIOME);
        System.out.println(TAG + "    copies -> plains=" + plains + " desert=" + desert
                + " badlands=" + badlands + " ocean_oilfield=" + oil);
        failed += check("plains: 1 copy (base modifier)", plains == 1);
        failed += check("desert: 3 copies (base + 2 extra = the 3x rule)", desert == 3);
        failed += check("badlands: 3 copies", badlands == 3);
        failed += check("ocean oilfield biome: 1 copy (is in #is_overworld)", oil == 1);
    }

    private static int count(ServerLevel level, ResourceKey<Biome> key) {
        Biome biome = level.registryAccess().registryOrThrow(Registries.BIOME).get(key);
        if (biome == null) {
            return -1;
        }
        int n = 0;
        for (HolderSet<PlacedFeature> step : biome.getGenerationSettings().features()) {
            for (Holder<PlacedFeature> h : step) {
                if (h.unwrapKey().map(k -> k.location().equals(OIL_PLACED)).orElse(false)) {
                    n++;
                }
            }
        }
        return n;
    }

    private static void checkRule(ServerLevel level) {
        System.out.println(TAG + "(3) stony shore -> oilfield rule (synthetic delegate)");
        var reg = level.registryAccess().registryOrThrow(Registries.BIOME);
        Holder<Biome> stony = reg.getHolderOrThrow(Biomes.STONY_SHORE);
        Holder<Biome> river = reg.getHolderOrThrow(Biomes.RIVER);
        Holder<Biome> salty = reg.getHolderOrThrow(SaltyRiverBiomeSource.SALTY_RIVER);
        Holder<Biome> oil = reg.getHolderOrThrow(OIL_BIOME);

        BiomeSource fakeStony = new FakeSource(stony);
        BiomeSource fakeRiver = new FakeSource(river);
        SaltyRiverBiomeSource all = new SaltyRiverBiomeSource(fakeStony, salty, 0.0D, Optional.of(oil), 1.0D);
        SaltyRiverBiomeSource none = new SaltyRiverBiomeSource(fakeStony, salty, 0.0D, Optional.of(oil), 0.0D);
        SaltyRiverBiomeSource saltyAll = new SaltyRiverBiomeSource(fakeRiver, salty, 1.0D, Optional.of(oil), 0.0D);

        int replacedAll = 0;
        int replacedNone = 0;
        for (int i = 0; i < 400; i++) {
            if (all.getNoiseBiome(i * 7, 64, i * 13, null).is(OIL_BIOME)) {
                replacedAll++;
            }
            if (none.getNoiseBiome(i * 7, 64, i * 13, null).is(OIL_BIOME)) {
                replacedNone++;
            }
        }
        failed += check("oil_chance=1.0 replaces every stony shore (400/400)", replacedAll == 400,
                "got " + replacedAll);
        failed += check("oil_chance=0.0 replaces none", replacedNone == 0);
        failed += check("salty rule untouched: river -> salty river",
                saltyAll.getNoiseBiome(12345, 64, 54321, null).is(SaltyRiverBiomeSource.SALTY_RIVER));
        failed += check("oil biome is in possibleBiomes of the wrapper", has(all, OIL_BIOME));
        SaltyRiverBiomeSource defaulted = new SaltyRiverBiomeSource(fakeStony, salty, 0.0D,
                Optional.empty(), 1.0D);
        failed += check("OLD-WORLD fallback: missing oil_biome resolves from the registry",
                defaulted.getNoiseBiome(999, 64, 999, null).is(OIL_BIOME));
    }

    /** 只为探针存在的假群系源（codec() 永不被调用）。 */
    private static final class FakeSource extends BiomeSource {
        private final Holder<Biome> only;

        FakeSource(Holder<Biome> only) {
            this.only = only;
        }

        @Override
        protected MapCodec<? extends BiomeSource> codec() {
            return null;
        }

        @Override
        protected Stream<Holder<Biome>> collectPossibleBiomes() {
            return Stream.of(this.only);
        }

        @Override
        public Holder<Biome> getNoiseBiome(int x, int y, int z, Climate.Sampler sampler) {
            return this.only;
        }
    }

    private static void checkPlaceFeature(ServerStartedEvent event, ServerLevel level) {
        System.out.println(TAG + "(4) /place feature potato_s_t:mini_oilfield");
        BlockPos surface = level.getHeightmapPos(Heightmap.Types.WORLD_SURFACE_WG, new BlockPos(0, 0, 0));
        int baseY = surface.getY() - 2;
        // 原版 LakeFeature 的作用区是 origin 起 +15 格（x/z），下半个透镜必须是固体，
        // 所以平台要盖住 origin(8,*,8) 的 8..23 ⇒ 这里铺 -2..26。
        for (int dx = -2; dx < 27; dx++) {
            for (int dz = -2; dz < 27; dz++) {
                for (int dy = -10; dy <= 2; dy++) {
                    level.setBlock(new BlockPos(dx, baseY + dy, dz), Blocks.STONE.defaultBlockState(), 3);
                }
            }
        }
        String cmd = "place feature potato_s_t:mini_oilfield 8 " + (baseY + 3) + " 8";
        try {
            event.getServer().getCommands().performPrefixedCommand(
                    event.getServer().createCommandSourceStack().withSuppressedOutput(), cmd);
            System.out.println(TAG + "    command executed   [" + cmd + "]");
        } catch (Throwable t) {
            System.out.println(TAG + "    command threw: " + t);
        }
        int oil = 0;
        boolean source = false;
        BlockPos first = null;
        for (int dx = -2; dx < 27; dx++) {
            for (int dz = -2; dz < 27; dz++) {
                for (int dy = -12; dy <= 8; dy++) {
                    BlockPos p = new BlockPos(dx, baseY + 3 + dy, dz);
                    if (level.getBlockState(p).is(ModBlocks.CRUDE_OIL.get())) {
                        oil++;
                        first = first == null ? p : first;
                        if (level.getFluidState(p).isSource()) {
                            source = true;
                        }
                    }
                }
            }
        }
        System.out.println(TAG + "    oil blocks = " + oil + "  first = " + first
                + "  source block seen = " + source);
        failed += check("the lake feature really places crude oil blocks", oil > 0);
        failed += check("placed oil is a SOURCE block (scoopable, never infinite)", source);
    }

    private static Object callDeclared(Object target, String name, Class<?>[] types, Object... args) {
        Class<?> c = target.getClass();
        while (c != null) {
            try {
                java.lang.reflect.Method m = c.getDeclaredMethod(name, types);
                m.setAccessible(true);
                return m.invoke(target, args);
            } catch (NoSuchMethodException e) {
                c = c.getSuperclass();
            } catch (Throwable t) {
                return null;
            }
        }
        return null;
    }

    private static int check(String what, boolean ok) {
        System.out.println(TAG + (ok ? "[OK]   " : "[FAIL] ") + what);
        return ok ? 0 : 1;
    }

    private static int check(String what, boolean ok, String detail) {
        System.out.println(TAG + (ok ? "[OK]   " : "[FAIL] ") + what + "   (" + detail + ")");
        return ok ? 0 : 1;
    }
}
