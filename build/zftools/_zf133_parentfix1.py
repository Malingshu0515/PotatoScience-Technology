# -*- coding: utf-8 -*-
"""_zf133_parentfix1.py —— 末地那一场的几何：波被**发射者自己站的格**挡死了

## 铁证（`[D14]` 诊断，一次跑就定案）
```
[D14] damageAt dim=minecraft:the_end pos=0, 100, -3 dmg=12.0 box=... found=0
...（一共 18 行 = 6 列 × 3 层，全部落在 x=0 这一排）... found=0
```
① `damageAt` **确实被调用了**（维度、伤害、box 全对）⇒ 产品代码没问题；
② 整场**只采了 x=0 这一排**（18 行 = 1 tick × 6 列 × 3 层）⇒ 波在第 1 tick 就停了；
③ 停因：末地那台发射者**站在波自己扫过的那条线上**（(0.5,100,0.5)，x=0 那一排正对他），
   而他脚下那格既不是原木/树叶、`isCorrectToolForDrops(空气)` 也判不出来 ⇒ `blocked` ⇒ 当场散。
   末影人在 x=1.5 ⇒ 永远轮不到那一排。

## 修法（只改探针几何；"朝面向放出去"的产品语义一个字不动）
  发射者挪到 **(0.5, 100, 6.5)、朝向 -Z（yaw 180）**⇒ 主轴 = z（负方向），第 1 步采 z=5…
  末影人放 **(0.5, 100, 0.5)**⇒ 第 6 步扫到它；中途没有任何非原木/树叶方块（台面在 y=99）。

跑法：python build\\zftools\\_zf133_parentfix1.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

C1_OLD = "        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);"
C1_NEW = """        // ⚠ 站到**采样区之外**：波的第 0 步会采样发射者脚下那一格，而"实体所在格"
        //   既不是原木/树叶、也不是"斧子挖得动的方块" ⇒ 波会在第 1 tick 被自己人挡死
        //   （[D14] 诊断实测：整场只采了一排 18 格就散）。挪到 z=6.5、朝 -Z：
        //   第 1 步采 z=5，末影人在 z=0，第 6 步扫到。
        endPlayer.moveTo(0.5D, 100.0D, 6.5D, 180.0F, 0.0F);"""

C2_OLD = "        ender.moveTo(1.5D, 100.0D, 0.5D, 0.0F, 0.0F);"
C2_NEW = "        ender.moveTo(0.5D, 100.0D, 0.5D, 0.0F, 0.0F);"

D14_OLD = """        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        System.out.println("[D14] damageAt dim=" + wave.level.dimension().location()
                + " pos=" + pos.toShortString() + " dmg=" + damage
                + " box=" + box + " found=" + found.size());
        for (LivingEntity e : found) {
            System.out.println("[D14]    " + e.getName().getString()
                    + " @ " + String.format("%.2f,%.2f,%.2f", e.getX(), e.getY(), e.getZ())
                    + " owner? " + e.getUUID().equals(wave.owner));
        }
        for (LivingEntity target : found) {"""
D14_NEW = "        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"

jobs = [(CHK, C1_OLD, C1_NEW, "末地发射者挪到采样区外"),
        (CHK, C2_OLD, C2_NEW, "末影人挪到走廊上"),
        (SHOCK, D14_OLD, D14_NEW, "撤掉 D14 诊断（产品代码不许留）")]
cache = {}
for path, a, b, desc in jobs:
    s = cache.get(path) or io.open(path, encoding="utf-8").read()
    n = s.count(a)
    assert n == 1, "%s 锚点 %d 次：%r" % (desc, n, a.strip().split("\n")[0][:60])
    cache[path] = s.replace(a, b, 1)
    print("[OK ] %s" % desc)
for path, s in cache.items():
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("完成；产品代码残留 [D14] =", "[D14]" in io.open(SHOCK, encoding="utf-8").read())
