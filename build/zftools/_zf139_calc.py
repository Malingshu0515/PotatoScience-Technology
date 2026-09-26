# -*- coding: utf-8 -*-
"""ZF139 备选：把「护甲值/韧性 + 抗性提升」换算成实际吃到的伤害（原版公式，逐字照 CombatRules.getDamageAfterAbsorb
+ LivingEntity.getDamageAfterMagicAbsorb）。只读、不改盘。"""
import io, sys

def after_armor(dmg, armor, tough):
    f = 2.0 + tough / 4.0
    f1 = min(max(armor - dmg / f, armor * 0.2), 20.0)
    return dmg * (1.0 - f1 / 25.0)

def after_resist(dmg, amp):          # amp 0/1/2 = I/II/III 级
    i = (amp + 1) * 5
    return max(dmg * (25 - i) / 25.0, 0.0)

def total(dmg, armor, tough, amp=None):
    d = after_armor(dmg, armor, tough)
    if amp is not None:
        d = after_resist(d, amp)
    return d

CASES = [
    # 名字, 护甲值, 韧性, 抗性 amp（None = 没有）
    ("下界合金（满套）",            20, 12.0, None),
    ("星璨钢·白天（满套）",          28,  2.5, None),
    ("星璨钢·夜晚主世界（满套）",     28,  2.5, 1),
    ("星璨钢·末地（满套）",          28,  2.5, 2),
    ("振金·现在",                   20, 12.0, None),
    ("振金·甲（抗性 I + 摔落免伤）",  20, 12.0, 0),
    ("振金·乙（甲 + 各 +1 护甲值）",  24, 12.0, 0),
    ("振金·丁（抗性 II）",           20, 12.0, 1),
]

HITS = [("小怪 6", 6.0), ("普通 10", 10.0), ("重击 20", 20.0)]

out = []
out.append("原版公式：先护甲（min(max(护甲 - 伤害/(2+韧性/4), 护甲*0.2), 20)/25 减伤），再抗性（每级 ×0.8）")
out.append("")
head = "| 方案 | " + " | ".join(h[0] for h in HITS) + " |"
out.append(head)
out.append("|---|" + "---|" * len(HITS))
for name, armor, tough, amp in CASES:
    cells = []
    for _, d in HITS:
        x = total(d, armor, tough, amp)
        cells.append("%.2f（%.0f%%）" % (x, x / d * 100))
    out.append("| %s | %s |" % (name, " | ".join(cells)))

out.append("")
out.append("== 爆炸（原版苦力怕 20 点，振金在事件里先减半 ⇒ 进护甲前就是 10）==")
for name, armor, tough, amp in CASES:
    d = 10.0 if name.startswith("振金") else 20.0
    x = total(d, armor, tough, amp)
    out.append("  %-26s 进护甲 %.1f → 实际 %.2f" % (name, d, x))

out.append("")
out.append("== 箭（原版骷髅 1~4 点，振金直接免疫、连伤害都不结算 ⇒ 0）==")

txt = "\n".join(out)
# ⚠ 控制台是 GBK：先落盘（UTF-8），再往 stdout 打（打不出来也无所谓）
io.open(r"E:\PotatoST\build\zftools\_zf139_calc.txt", "w", encoding="utf-8").write(txt + "\n")
try:
    sys.stdout.write(txt + "\n")
except UnicodeEncodeError:
    sys.stdout.write("(console is GBK; see _zf139_calc.txt)\n")
