# -*- coding: utf-8 -*-
"""_zf133_d15.py —— 末地伤害最后一环：`hurt()` 到底有没有生效

`[D14B]` 已经证明实体框能查到人（found=1）；现在只剩一个问题：
`target.hurt(playerAttack(owner), 12)` 返回什么、事件有没有发出来。

跑法：python build\\zftools\\_zf133_d15.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """            target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);"""
NEW = """            boolean hurt = target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
            System.out.println("[D15] hurt(" + target.getName().getString() + ", " + damage
                    + ") = " + hurt + " 之后 hp=" + target.getHealth()
                    + " invul=" + target.invulnerableTime
                    + " isInvulTo=" + target.isInvulnerableTo(
                            wave.level.damageSources().playerAttack(owner)));"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入 [D15]"))


main()
