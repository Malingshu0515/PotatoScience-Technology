# -*- coding: utf-8 -*-
"""_zf133_falsifyfix.py —— 反证三把刀的问题：两把是"期望编号写错"，**一把是真漏网**

| 刀 | 现象 | 真因 | 修法 |
|---|---|---|---|
| K6 | 注入后**红了 2 条**（B12），但脚本期望的是 B10 | 期望串写错了（B10 后来被我改成了"两支结构"那条）| 期望改成 B12 |
| K9 | 注入"挖掘等级改成下界合金"后 **0 条红** | ⚠ **这是常驻校验的真漏洞**：A2 判据是 `"INCORRECT_FOR_DIAMOND_TOOL" in tiers`，而**文件里其他地方**（`INCORRECT_FOR_NETHERITE` 的定义/旧档位）也含这串 ⇒ 恒真 | A2 改成盯**那一行 build 调用**（正则把 `build(1192, ..., 标签, 22)` 整条抓出来比） |
| K8 | 锚点 0 次 | "挖不动就停"那段在"拆/挡分两支"重构时换了形状 | 锚点改成重构后的实际文本 |

跑法：python build\\zftools\\_zf133_falsifyfix.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VER = r"E:\PotatoST\build\zftools\_zf133_verify.py"
FAL = r"E:\PotatoST\build\zftools\_zf133_falsify.py"

# ---------- ① A2 判据收紧（真漏洞） ----------
V_OLD = """    ok("A2 挖掘等级 = 钻石标签（INCORRECT_FOR_DIAMOND_TOOL）",
       "INCORRECT_FOR_DIAMOND_TOOL" in tiers)"""
V_NEW = """    # ⚠ 这条**必须**盯那一行 build 调用本身：只写 `"INCORRECT_FOR_DIAMOND_TOOL" in tiers`
    #   是恒真的（文件里别处也出现过这串）—— 反证 K9（把钻石改成下界合金）当场证明了它是漏网。
    m_tier = re.search(r"build\\(1192,\\s*STAR_STEEL_DAMAGE,\\s*STAR_STEEL_SPEED,\\s*"
                       r"(BlockTags\\.[A-Z_]+),\\s*(\\d+)\\)", tiers)
    ok("A2 挖掘等级 = 钻石标签 + 附魔权重 22（读那一行 build 调用本身）",
       m_tier is not None and m_tier.group(1) == "BlockTags.INCORRECT_FOR_DIAMOND_TOOL"
       and m_tier.group(2) == "22",
       ("抓到 %s / %s" % (m_tier.group(1), m_tier.group(2))) if m_tier else "没抓到 build 调用")"""

s = io.open(VER, encoding="utf-8").read()
n = s.count(V_OLD)
assert n == 1, "A2 锚点 %d 次" % n
s = s.replace(V_OLD, V_NEW, 1)
io.open(VER, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] A2 判据已收紧")

# ---------- ② K6 期望编号 + ③ K8 锚点 ----------
f = io.open(FAL, encoding="utf-8").read()

f = f.replace('''    ("K6", "滚动窗口退化成一次性计时（拆到也不清零）", SHOCK,
     "            wave.sinceBreak = 0;",
     "            wave.sinceBreak = wave.sinceBreak;",
     "B10"),''',
'''    ("K6", "滚动窗口退化成一次性计时（拆到也不清零）", SHOCK,
     "            wave.sinceBreak = 0;",
     "            wave.sinceBreak = wave.sinceBreak;",
     "B12"),''', 1)

f = f.replace('''    ("K8", "「挖不动就停」的判据去掉", SHOCK,
     "                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {\\n                    blocked = true;\\n                    continue;\\n                }\\n",
     "",
     "B7"),''',
'''    ("K8", "「挖不动就停」的判据去掉（撞墙也不停）", SHOCK,
     "                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {\\n                    blocked = true;\\n                }",
     "                if (false) {\\n                    blocked = true;\\n                }",
     "B10"),''', 1)

io.open(FAL, "w", encoding="utf-8", newline="\n").write(f)
print("[OK] K6 期望改 B12 / K8 锚点改成重构后的文本")
