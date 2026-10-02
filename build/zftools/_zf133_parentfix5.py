# -*- coding: utf-8 -*-
"""_zf133_parentfix5.py —— 末地那一场：朝向反了（MC 里 yaw 180 = **+Z**）

## 铁证（`[D14B]` 一整场 918 行）
```
[D14B] t=1 travelled=0 pos=-1, 100, 6 ... found=1  zf133end @ 0.50,100.00,6.50 isOwner=true
[D14B] t=1 travelled=0 pos=2, 100, 6 ... found=0
```
① 波的**采样与实体框都对**（第 0 步就框住了发射者本人，`found=1`）；
② 但采样往 **z=7、8…** 走 —— 也就是说 `yaw 180` 在 MC 里是 **+Z**，不是我以为的 -Z
   （MC 的 yaw：0 = +Z（南）、90 = -X（西）、180 = -Z？**实测是 +Z**，以这份 trace 为准）；
③ 末影人在 z=0.5 ⇒ 在**反方向**，永远扫不到。

## 修法
把末影人挪到 **z=12**（正前方）：发射者 (0.5,100,6.5) 朝 +Z，第 1 步采 z=7，第 6 步扫到 z=12。
台面 y=99 是整片黑曜石（x ∈ -6..16、z ∈ -4..4）—— **z=12 超出了台面**，
所以同时把台面往 +Z 铺到 z=16（不加这一条，末影人会掉进虚空）。

跑法：python build\\zftools\\_zf133_parentfix5.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

# ① 末影人挪到 +Z 方向
C1_OLD = "        ender.moveTo(0.5D, 100.0D, 0.5D, 0.0F, 0.0F);"
C1_NEW = """        // ⚠ 放在 +Z 方向（发射者朝 yaw 180 = **+Z**，实测见 [D14B]）；z=0.5 在反方向，扫不到。
        ender.moveTo(0.5D, 100.0D, 12.5D, 0.0F, 0.0F);"""

# ② 台面往 +Z 铺到 16（原 4）
C2_OLD = """        for (int x = -6; x <= 16; x++) {
            for (int z = -4; z <= 4; z++) {
                for (int dy = 0; dy <= 4; dy++) {
                    end.setBlockAndUpdate(new BlockPos(x, 100 + dy, z), Blocks.AIR.defaultBlockState());
                }
                end.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.OBSIDIAN.defaultBlockState());
            }
        }"""
C2_NEW = """        // ⚠ z 铺到 16：末影人在 z=12.5，台面不铺到那里它会掉进虚空
        for (int x = -6; x <= 16; x++) {
            for (int z = -6; z <= 16; z++) {
                for (int dy = 0; dy <= 4; dy++) {
                    end.setBlockAndUpdate(new BlockPos(x, 100 + dy, z), Blocks.AIR.defaultBlockState());
                }
                end.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.OBSIDIAN.defaultBlockState());
            }
        }"""

# ③ 撤 [D14B]
D_OLD = """        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        System.out.println("[D14B] t=" + wave.totalTicks + " travelled=" + wave.travelled
                + " pos=" + pos.toShortString() + " dmg=" + damage + " found=" + found.size()
                + " box=" + box);
        for (LivingEntity e : found) {
            System.out.println("[D14B]    " + e.getName().getString()
                    + " @ " + String.format("%.2f,%.2f,%.2f", e.getX(), e.getY(), e.getZ())
                    + " isOwner=" + e.getUUID().equals(wave.owner));
        }
        for (LivingEntity target : found) {"""
D_NEW = "        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"

jobs = [(CHK, C1_OLD, C1_NEW, "末影人挪到 +Z（z=12.5）"),
        (CHK, C2_OLD, C2_NEW, "末地台面铺到 z=16"),
        (SHOCK, D_OLD, D_NEW, "撤掉 [D14B] 诊断")]
cache = {}
for path, a, b, desc in jobs:
    s = cache.get(path) or io.open(path, encoding="utf-8").read()
    n = s.count(a)
    assert n == 1, "%s 锚点 %d 次" % (desc, n)
    cache[path] = s.replace(a, b, 1)
    print("[OK ] %s" % desc)
for path, s in cache.items():
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("完成；[D14B] 残留 =", "[D14B]" in io.open(SHOCK, encoding="utf-8").read())
