# -*- coding: utf-8 -*-
u"""_zf151_api2.py —— ZF151 侦察③：把 `ServerPlayerGameMode.destroyBlock` 那段原文打出来。

判据链（1.21.1，反混淆源码）：
  canHarvestBlock(...) → Player.hasCorrectToolForDrops(state)
      = `!state.requiresCorrectToolForDrops() || 手上那件是这块的正确工具`
  ⇒ **手上没拿对工具时 canHarvestBlock = false**，而掉落就在 `playerDestroy` 里。
"""
import io
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
SRC = r"E:\PotatoST\.gradle\repositories\ng_dummy_ng\net\neoforged\neoforge\21.1.235\neoforge-21.1.235-sources.jar"

z = zipfile.ZipFile(SRC)
txt = z.read(u"net/minecraft/server/level/ServerPlayerGameMode.java").decode(u"utf-8", u"replace")
lines = txt.split(u"\n")
for i, ln in enumerate(lines):
    if u"canHarvestBlock" in ln:
        for j in range(max(0, i - 12), min(len(lines), i + 22)):
            print(u"%5d | %s" % (j + 1, lines[j].rstrip()[:150]))
        break
print(u"")
txt2 = z.read(u"net/minecraft/world/entity/player/Player.java").decode(u"utf-8", u"replace")
for i, ln in enumerate(txt2.split(u"\n")):
    if u"requiresCorrectToolForDrops" in ln:
        for j in range(max(0, i - 6), i + 3):
            print(u"P %5d | %s" % (j + 1, txt2.split(u"\n")[j].rstrip()[:150]))
        break
z.close()
