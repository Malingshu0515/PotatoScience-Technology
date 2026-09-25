# -*- coding: utf-8 -*-
u"""_zf75_fixprobe2.py —— 把探针第 (4) 段的测试平台做大

原版 `LakeFeature` 的作用区是 **origin 起 +15 格**（x/z 各 16 格、y 为 origin-4..origin+3），
而"下半个透镜（i1<4）必须是固体方块"否则整次放置直接 `return false`。
我原来只铺了 16×16 的石头（x/z 0..15），原点却在 (8, y, 8) ⇒ 透镜右半边落在平台外（空气）
⇒ 特征放弃、0 块油。平台改成 origin 四周都够宽。
"""
import io
import sys

OLD_SLAB = u"""        for (int dx = -2; dx < 18; dx++) {
            for (int dz = -2; dz < 18; dz++) {
                for (int dy = -8; dy <= 2; dy++) {
                    level.setBlock(new BlockPos(dx, baseY + dy, dz), Blocks.STONE.defaultBlockState(), 3);
                }
            }
        }"""
NEW_SLAB = u"""        // 原版 LakeFeature 的作用区是 origin 起 +15 格（x/z），下半个透镜必须是固体，
        // 所以平台要盖住 origin(8,*,8) 的 8..23 ⇒ 这里铺 -2..26。
        for (int dx = -2; dx < 27; dx++) {
            for (int dz = -2; dz < 27; dz++) {
                for (int dy = -10; dy <= 2; dy++) {
                    level.setBlock(new BlockPos(dx, baseY + dy, dz), Blocks.STONE.defaultBlockState(), 3);
                }
            }
        }"""

OLD_SCAN = u"""        for (int dx = -6; dx < 24; dx++) {
            for (int dz = -6; dz < 24; dz++) {
                for (int dy = -10; dy <= 6; dy++) {"""
NEW_SCAN = u"""        for (int dx = -2; dx < 27; dx++) {
            for (int dz = -2; dz < 27; dz++) {
                for (int dy = -12; dy <= 8; dy++) {"""

PATHS = [
    r"E:\PotatoST\build\zftools\check\OilfieldCheck2.java",
    r"E:\PotatoST\src\main\java\com\potatost\mod\OilfieldCheck.java",
]


def main():
    for p in PATHS:
        t = io.open(p, "r", encoding="utf-8").read()
        for old, new, label in ((OLD_SLAB, NEW_SLAB, u"平台"),
                                (OLD_SCAN, NEW_SCAN, u"扫描范围")):
            n = t.count(old)
            if n != 1:
                print(u"  !! %s / %s：命中 %d 次" % (p, label, n))
                return 1
            t = t.replace(old, new, 1)
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)
        print(u"  [OK] %s 平台与扫描范围已放大" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
