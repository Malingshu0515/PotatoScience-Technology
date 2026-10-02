# -*- coding: utf-8 -*-
"""_zf133_parentfix7.py —— 撤掉 [D16] 剩下的两段（前一次因为文本里多了一个独立行 `);` 没匹配上）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

s = io.open(SHOCK, encoding="utf-8").read()

# ① 查找块（用起止下标切，别靠长锚点）
start = s.find("        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(")
assert start > 0, "找不到查找块起点"
end = s.find("        for (LivingEntity target : found) {", start)
assert end > start, "找不到查找块终点"
s = s[:start] + s[end:]

# ② hurt 打印那两行 → 恢复成原来的调用
OLD = """            boolean hurt = target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
            System.out.println("[D16] hurt(" + target.getName().getString() + ", " + damage
                    + ") = " + hurt + " hp=" + target.getHealth());"""
NEW = """            target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);"""
n = s.count(OLD)
assert n == 1, "hurt 打印锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
body = io.open(SHOCK, encoding="utf-8").read()
for k in ("[D16]", "[D15]", "[D14", "[WB]", "System.out"):
    print("残留 %-10s = %s" % (k, k in body))
