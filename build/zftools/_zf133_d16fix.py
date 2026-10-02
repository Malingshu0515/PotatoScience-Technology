# -*- coding: utf-8 -*-
"""_zf133_d16fix.py —— 去掉那个编译不过的 `getAll().size()`（LevelEntityGetter 没有 size()）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
BAD = ' + " 全场实体=" + wave.level.getEntities().getAll().size()'
s = io.open(P, encoding="utf-8").read()
n = s.count(BAD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(BAD, "", 1))
print("[OK] 已去掉")
