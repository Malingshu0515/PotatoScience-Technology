# -*- coding: utf-8 -*-
"""_zf133_dbg13.py —— 末地伤害为什么没落地（临时打印 box / 目标）

`damageAt` 已经接进了采样循环、`Level.END` 判断也在（探针里波确实活着），
但末影人一次都没被记到伤害。这一刀把每格结算时的 box 与查到的实体打出来。

跑法：python build\\zftools\\_zf133_dbg13.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """        int mobsDebug = 0;"""
OLD_REAL = """        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"""
NEW_REAL = """        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        if (TRACE) {
            System.out.println("[TRDMG] " + pos.toShortString() + " dmg=" + damage
                    + " box=" + box + " 查到 " + found.size() + " 个实体");
            for (LivingEntity e : found) {
                System.out.println("[TRDMG]     " + e.getName().getString() + " @ "
                        + String.format("%.2f,%.2f,%.2f", e.getX(), e.getY(), e.getZ())
                        + " uuid=" + e.getUUID().toString().substring(0, 8)
                        + " owner=" + wave.owner.toString().substring(0, 8)
                        + " creative=" + (e instanceof Player p && p.isCreative()));
            }
        }
        for (LivingEntity target : found) {"""

s = io.open(SHOCK, encoding="utf-8").read()
assert s.count(OLD_REAL) == 1, "锚点 %d" % s.count(OLD_REAL)
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD_REAL, NEW_REAL, 1))
print("[OK] 已插入末地伤害诊断")
