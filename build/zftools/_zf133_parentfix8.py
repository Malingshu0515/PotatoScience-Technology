# -*- coding: utf-8 -*-
"""_zf133_parentfix8.py —— 把 `for (LivingEntity target : found)` 恢复成直接查询（`found` 已删）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = "        for (LivingEntity target : found) {"
NEW = "        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"

s = io.open(SHOCK, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 已恢复直接查询")
