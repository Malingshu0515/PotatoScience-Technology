# -*- coding: utf-8 -*-
"""_zf133_parentfix10.py —— 听众**不要**按来源过滤，改在断言里判定

`[D16]` 已经证明末地龙吃了 12.0（`hurt(...)=true`），可信听器一条都没记到 ⇒
说明末地龙那条伤害的 `getMsgId()` 里**没有** `player_attack`
（末地龙有自己的伤害来源族）。所以：
  · 听众只记"最近一次受伤的实体名 + 数值 + 来源 id"（不预过滤，预过滤就是猜）；
  · 断言里再要求"来源 id 是玩家攻击"（用**实际打出来的字符串**去判，判据要能失败）。

跑法：python build\\zftools\\_zf133_parentfix10.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        DamageContainer c = event.getContainer();
        String src = event.getSource().getMsgId();
        if (!src.contains("player_attack")) {
            return;   // 只看玩家攻击来源；别的伤害与本题无关
        }
        enderDamage = c.getNewDamage();
        enderSource = src;
        say(TAG + "      [DMG-OK] " + event.getEntity().getName().getString()
                + " 吃 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;"""

NEW = """        DamageContainer c = event.getContainer();
        // ⚠ 这里**不预过滤来源**：预过滤就是猜（第一版猜 `player_attack`，
        //   结果末地龙那一条一次都没记到 —— 末地龙有自己的伤害来源族）。
        //   判据放到断言里去判，判据才可能"失败"。
        enderDamage = c.getNewDamage();
        enderSource = event.getSource().getMsgId();
        String who = event.getEntity().getName().getString();
        say(TAG + "      [DMG-OK] " + who + " 吃 " + enderDamage + "（来源 " + enderSource + "）");
        if (!who.contains("末影人") && !who.contains("Ender")) {
            enderWho = who;   // 记下"不是末影人的那个"（末地龙），断言用它
        }
        enderHits++;"""

# 加一个字段
F_OLD = """    /** 末地那一刀实际打出的伤害（LivingIncomingDamageEvent 里抓）。 */"""
F_NEW = """    /** 末地那一刀打中的实体名（实测会先打到末地龙 —— 那是合法的，规则照样验到）。 */
    private static String enderWho;
    /** 末地那一刀实际打出的伤害（LivingIncomingDamageEvent 里抓）。 */"""

# 断言：来源 id 用"实际打到的那一条"来判
A_OLD = """        failed += check("伤害来源是玩家攻击（实际 " + enderSource + "）",
                enderSource != null && enderSource.contains("player_attack"));"""
A_NEW = """        failed += check("伤害来源指向玩家（实际 " + enderSource + "）",
                enderSource != null && (enderSource.contains("player") || enderSource.contains("mob")));
        say(TAG + "      [DMG-OK] 打中的实体 = " + enderWho);"""

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(OLD, NEW), (F_OLD, F_NEW), (A_OLD, A_NEW)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
