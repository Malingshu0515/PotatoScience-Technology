# -*- coding: utf-8 -*-
"""_zf133_dbg14.py —— 末地伤害：只打三行，问死它

问三件事（都在 `damageAt` 里，只在末地那一场会打）：
  ① 这个函数**到底有没有被调用**；
  ② 调用时 `wave.level.dimension()` 是什么、`pos` 是哪个格；
  ③ `getEntitiesOfClass` 查到几个实体、都是谁、坐标在哪。

跑法：python build\\zftools\\_zf133_dbg14.py      插
      python build\\zftools\\_zf133_dbg14.py --off 撤
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """    private static void damageAt(Wave wave, ServerPlayer owner, BlockPos pos) {
        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"""
NEW = """    private static void damageAt(Wave wave, ServerPlayer owner, BlockPos pos) {
        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        System.out.println("[D14] damageAt dim=" + wave.level.dimension().location()
                + " pos=" + pos.toShortString() + " dmg=" + damage
                + " box=" + box + " found=" + found.size());
        for (LivingEntity e : found) {
            System.out.println("[D14]    " + e.getName().getString()
                    + " @ " + String.format("%.2f,%.2f,%.2f", e.getX(), e.getY(), e.getZ())
                    + " owner? " + e.getUUID().equals(wave.owner));
        }
        for (LivingEntity target : found) {"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d 次" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入 [D14] 诊断"))


main()
