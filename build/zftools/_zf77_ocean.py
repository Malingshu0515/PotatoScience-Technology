# -*- coding: utf-8 -*-
u"""_zf77_ocean.py —— 海洋油田从「替换石岸」改成「替换**靠岸的浅海**」

用户原话：「海洋油田还是放在海里吧 靠近岸边就行 概率较低」。
⇒ 判定改成：原版**浅海** `minecraft:ocean` **且四个正方向邻居至少有一个不是海洋**
（`#minecraft:is_ocean` 之外 = 陆地/石岸/沙滩…）⇒ 油田出现在贴着岸的浅海里，
地貌仍是海（地形由 multi_noise 决定，换群系不动地形），水色 4047AD 就在那片海上显示。

顺带把群系的"植被"那一步换成海洋风格（发光地衣/海草/海带），原来是照石岸抄的陆地植物。
"""
import io
import json
import os
import sys

PROJ = r"E:\PotatoST"
JAVA = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                    u"SaltyRiverBiomeSource.java")
BIOME = os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"potato_s_t",
                     u"worldgen", u"biome", u"ocean_oilfield.json")

OLD_RULE = u"""        if (this.resolvedOilBiome != null && original.is(Biomes.STONY_SHORE)
                && this.isOilSection(quartX, quartZ)) {
            return this.resolvedOilBiome;
        }"""
NEW_RULE = u"""        if (this.resolvedOilBiome != null && original.is(Biomes.OCEAN)
                && this.isOilSection(quartX, quartZ)
                && this.isCoastalOcean(quartX, quartY, quartZ, sampler)) {
            return this.resolvedOilBiome;
        }"""

OLD_TAIL = u"""    /** 海洋油田那一段的判定：同一套格子、不同常数（互不相关）。 */"""
NEW_TAIL = u"""    /**
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

    /** 海洋油田那一段的判定：同一套格子、不同常数（互不相关）。 */"""

OLD_FIELDS = u"""    /** 油田那一套哈希的偏移量：与咸水河用不同的常数，两条规则互不相关。 */
    private static final long OIL_SALT = 0x5EEDL;"""
NEW_FIELDS = u"""    /** 油田那一套哈希的偏移量：与咸水河用不同的常数，两条规则互不相关。 */
    private static final long OIL_SALT = 0x5EEDL;

    /** {@code #minecraft:is_ocean}：用来判断相邻格"是不是海"（ZF77 近岸判定）。 */
    private static final TagKey<Biome> OCEAN = TagKey.create(Registries.BIOME,
            ResourceLocation.withDefaultNamespace("is_ocean"));

    /** 四个正方向（相邻 1 个 quart 格 = 4 格）。 */
    private static final int[][] NEIGHBOUR_OFFSETS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};"""

OLD_IMPORT = u"import net.minecraft.core.registries.Registries;"
NEW_IMPORT = (u"import net.minecraft.core.registries.Registries;\n"
              u"import net.minecraft.tags.TagKey;")

OLD_DOC = u""" *   <li><b>石岸 → 海洋油田</b>（0.11 ZF75）：按位置哈希以 {@code oil_chance}（默认 0.15）替换
 *       —— 用户要的"在石岸群系和海洋群系之间过渡、概率不要太高"。</li>"""
NEW_DOC = u""" *   <li><b>靠岸的浅海 → 海洋油田</b>（0.11 ZF75，ZF77 改成海里）：原版浅海 {@code minecraft:ocean}
 *       且<b>四邻至少有一个不是海洋</b>（= 贴着岸）时，按位置哈希以 {@code oil_chance}（默认 0.15）替换
 *       —— 用户先要"石岸过渡"，后改口"还是放在海里吧 靠近岸边就行 概率较低"。</li>"""

fails = []


def patch(path, old, new, label):
    t = io.open(path, "r", encoding="utf-8").read()
    n = t.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次" % (label, n))
        print(u"  !! %s：命中 %d 次" % (label, n))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK] %s" % label)


def main():
    for old, new, label in ((OLD_RULE, NEW_RULE, u"getNoiseBiome 改成浅海近岸"),
                            (OLD_TAIL, NEW_TAIL, u"新增 isCoastalOcean"),
                            (OLD_FIELDS, NEW_FIELDS, u"新增 OCEAN 标签与邻居常量"),
                            (OLD_IMPORT, NEW_IMPORT, u"补 TagKey import"),
                            (OLD_DOC, NEW_DOC, u"类注释同步")):
        patch(JAVA, old, new, label)

    biome = json.loads(io.open(BIOME, "r", encoding="utf-8").read())
    steps = biome.get(u"features", [])
    # 第 9 步（index 9）= vegetal_decoration：换成海洋风格
    steps[9] = [u"minecraft:glow_lichen", u"minecraft:seagrass_normal",
                u"minecraft:seagrass_simple", u"minecraft:kelp_cold"]
    biome[u"features"] = steps
    io.open(BIOME, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(biome, ensure_ascii=False, indent=2) + u"\n")
    print(u"  [OK] 群系植被步骤换成海洋风格（发光地衣/海草/海带）")

    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
