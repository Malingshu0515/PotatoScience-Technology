# -*- coding: utf-8 -*-
"""_zf133_d14b.py —— 末地伤害最后一查（带着"空气早退已修好"这个新前提）

上一次 `[D14]` 的结论（"只采了一排"）是**在空气早退缺失的前提下**得到的 ——
那个 bug 已经修好（波不再被空气挡死），所以现在要**重测一遍**：
  · `damageAt` 每 tick 都在被调用吗？
  · 末影人在不在采样格里？

跑法：python build\\zftools\\_zf133_d14b.py   /  --off
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
        System.out.println("[D14B] t=" + wave.totalTicks + " travelled=" + wave.travelled
                + " pos=" + pos.toShortString() + " dmg=" + damage + " found=" + found.size()
                + " box=" + box);
        for (LivingEntity e : found) {
            System.out.println("[D14B]    " + e.getName().getString()
                    + " @ " + String.format("%.2f,%.2f,%.2f", e.getX(), e.getY(), e.getZ())
                    + " isOwner=" + e.getUUID().equals(wave.owner));
        }
        for (LivingEntity target : found) {"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入 [D14B]"))


main()
