# -*- coding: utf-8 -*-
"""_zf133_d16.py —— 把 [D14B] 与 [D15] 合成一刀（这次只关心**末影人在不在框里**）

已知：`[D14B]` 那一轮（末影人还在 z=0.5 时）能查到**发射者自己**（found=1），
说明查询本身是好的；挪到 z=12.5 之后 `[D15]` 一次都没打 ⇒ `found=0`。
所以问题变成：`getEntitiesOfClass` 为什么**查不到末影人**。
打印框与"末影人自己的碰撞盒"两条，一次就能对上。

跑法：python build\\zftools\\_zf133_d16.py   /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """            boolean hurt = target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
            System.out.println("[D15] hurt(" + target.getName().getString() + ", " + damage
                    + ") = " + hurt + " 之后 hp=" + target.getHealth()
                    + " invul=" + target.invulnerableTime
                    + " isInvulTo=" + target.isInvulnerableTo(
                            wave.level.damageSources().playerAttack(owner)));"""
NEW = """            boolean hurt = target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
            System.out.println("[D16] hurt(" + target.getName().getString() + ", " + damage
                    + ") = " + hurt + " hp=" + target.getHealth());"""

OLD2 = """        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"""
NEW2 = """        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        if (pos.getZ() >= 9) {
            System.out.println("[D16] pos=" + pos.toShortString() + " box=" + box
                    + " found=" + found.size()
                    + " 全场实体=" + wave.level.getEntities().getAll().size());
            for (var e : wave.level.getEntities().getAll()) {
                if (e instanceof LivingEntity le) {
                    System.out.println("[D16]    候选 " + le.getName().getString()
                            + " aabb=" + le.getBoundingBox()
                            + " 交集=" + le.getBoundingBox().intersects(box));
                }
            }
        }
        for (LivingEntity target : found) {"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    for a, b in ([(NEW, OLD), (NEW2, OLD2)] if off else [(OLD, NEW), (OLD2, NEW2)]):
        n = s.count(a)
        assert n == 1, "锚点 %d：%r" % (n, a[:60])
        s = s.replace(a, b, 1)
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
    print("[OK] %s" % ("撤销" if off else "插入 [D16]"))


main()
