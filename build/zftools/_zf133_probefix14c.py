# -*- coding: utf-8 -*-
"""_zf133_probefix14c.py —— `Enemy` 是接口，不能当 `getEntitiesOfClass` 的泛型参数

改成"取范围内所有 `Mob`，过滤掉玩家自己"，`discard()` 走 `Entity`（`Mob` 上有）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        int mobsCleared = 0;
        for (net.minecraft.world.entity.monster.Enemy mob : level.getEntitiesOfClass(
                net.minecraft.world.entity.monster.Enemy.class,
                new net.minecraft.world.phys.AABB(X0 - 48, Y0 - 48, Z0 - 48,
                        X0 + 48, Y0 + 48, Z0 + 48))) {
            mob.discard();
            mobsCleared++;
        }"""
NEW = """        int mobsCleared = 0;
        // ⚠ `Enemy` 是**接口**，不能当 getEntitiesOfClass 的泛型参数（编译期就顶回来）
        //   ⇒ 取范围内所有 Mob，把两台假玩家挑出去，其余全清。
        for (net.minecraft.world.entity.Mob mob : level.getEntitiesOfClass(
                net.minecraft.world.entity.Mob.class,
                new net.minecraft.world.phys.AABB(X0 - 48, Y0 - 48, Z0 - 48,
                        X0 + 48, Y0 + 48, Z0 + 48))) {
            if (mob == player || mob == creativePlayer) {
                continue;
            }
            mob.discard();
            mobsCleared++;
        }"""

s = io.open(CHK, encoding="utf-8").read()
assert s.count(OLD) == 1, "锚点 %d 次" % s.count(OLD)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 已改成按 Mob 过滤")
