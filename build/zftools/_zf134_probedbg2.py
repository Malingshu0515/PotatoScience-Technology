# -*- coding: utf-8 -*-
"""_zf134_probedbg2.py —— (j) 出手前把 shift / 冷却 / 波数 / 存活一次性打出来

上一跑：斧子在手上、耐久 0/1192（满）、同一实例，`use()` 却回 PASS。
PASS 只可能来自三处门禁之一：shift 没按下、冷却中、耐久不够 —— 前两个都可疑，直接打。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

ANCHOR = """                + " 同一实例? " + (player.getMainHandItem() == axe));"""

INSERT = ANCHOR + """
        say(TAG + "      [J] shift=" + player.isShiftKeyDown()
                + " 冷却中=" + player.getCooldowns().isOnCooldown(axe.getItem())
                + " activeWaves=" + ShockwaveManager.activeCount()
                + " 存活=" + player.isAlive() + " hp=" + player.getHealth()
                + " 主手耐久=" + axe.getDamageValue() + "/" + axe.getMaxDamage());"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(ANCHOR)
assert n == 1, "锚点 %d 次" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, INSERT, 1))
print("[OK] 已加前置状态打印")
