# -*- coding: utf-8 -*-
"""_zf133_parentfix9.py —— 探针听众：只认 EnderMan ⇒ 漏掉了末地龙那 12.0

（上一版脚本在改完产品文件后才断言失败，所以这两处探针改动**没落到盘上**，重来一遍。）
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

L_OLD = """        if (!(event.getEntity() instanceof EnderMan)) {
            return;
        }
        DamageContainer c = event.getContainer();
        enderDamage = c.getNewDamage();
        enderSource = event.getSource().getMsgId();
        say(TAG + "      末影人吃伤害 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;"""
L_NEW = """        DamageContainer c = event.getContainer();
        String src = event.getSource().getMsgId();
        if (!src.contains("player_attack")) {
            return;   // 只看玩家攻击来源；别的伤害与本题无关
        }
        enderDamage = c.getNewDamage();
        enderSource = src;
        say(TAG + "      [DMG-OK] " + event.getEntity().getName().getString()
                + " 吃 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;"""

A_OLD = """        failed += check("末影人被打到了（命中 " + enderHits + " 次，伤害 \""""
A_NEW = """        failed += check("末地有实体吃到这一刀（命中 " + enderHits + " 次，伤害 \""""

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(L_OLD, L_NEW), (A_OLD, A_NEW)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))

# 顺带把 javadoc 里那句"只认末影人"的说法更正
s = s.replace("末影人吃到 10 + 0.5n（n=玩家基础伤害）的伤害",
              "末地**任意实体**吃到 10 + 0.5n（n=玩家基础伤害）的伤害（实战里先挨打的是末地龙）", 1)

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
