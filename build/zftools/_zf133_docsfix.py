# -*- coding: utf-8 -*-
"""_zf133_docsfix.py —— §4 编号撞车：我的五条要从 4.118 起

写文档时 §4 最大编号是 **4.112**，所以我用了 4.113~4.117。
但**另一条会话在同一时间把 4.113/4.114 写进去了**（ZF131 的循环音、ZF132 的接缝校验），
于是我的第一条（假玩家探针）被挤到了不属于它的编号上、我的 4.115~4.117 反而接在别人后面 ——
**编号不连续，读者会以为 4.113 就是我的第一条**。

修法：把我的四条改成 **4.118(假玩家) / 4.119(PS+无BOM) / 4.120(框架事件) / 4.121(时间线) / 4.122(改注释)**，
并同步改掉 §9 与台账行里的引用。**先按标题整段定位（不靠编号猜）**，改完复核编号连续。
⚠ 但 4.115 那条（框架事件）现在的位置是**在我插进去之后**的——它本来就是我的。
   所以按**标题内容**定位，不按编号。

跑法：python build\\zftools\\_zf133_docsfix.py            # 只看
      python build\\zftools\\_zf133_docsfix.py --write
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"
WRITE = "--write" in sys.argv

# 我的四条（真正由我写的四段；§4.113/4.114 是别人的）
MINE = [
    ("### 4.115 【陷阱】框架事件", "### 4.120 【陷阱】框架事件", "框架事件"),
    ("### 4.116 【陷阱】探针的时间线常量", "### 4.121 【陷阱】探针的时间线常量", "时间线常量"),
    ("### 4.117 【陷阱】「改注释」", "### 4.122 【陷阱】「改注释」", "改注释"),
]

s = io.open(DOC, encoding="utf-8").read()

# ① 先把我插在 4.112 之前的那一段整体找出来：它现在紧贴在"### 4.113 【方法论】"之前
MINE_START = "### 4.113 【陷阱】假玩家探针"
i = s.find(MINE_START)
print("我的第一段（假玩家）在不在：", i > 0)
if i < 0:
    print("（可能已经被改过编号；下面只改其余三条）")

# ② 三条改号
for a, b, name in MINE:
    n = s.count(a)
    print("  %-12s 锚点 %d 次" % (name, n))
    assert n == 1, "%s 锚点不唯一" % name
    s = s.replace(a, b, 1)

# ③ 假玩家那条 4.113 -> 4.118
if i > 0:
    s = s.replace(MINE_START, "### 4.118 【陷阱】假玩家探针", 1)
    print("  假玩家那条 -> 4.118")

# ④ PS/无 BOM 那条（我写的，但编号被 4.114 占了）——它现在的标题是「4.114 【陷阱】PowerShell 5.1」
PS_OLD = "### 4.114 【陷阱】PowerShell 5.1"
if s.count(PS_OLD) == 1:
    s = s.replace(PS_OLD, "### 4.119 【陷阱】PowerShell 5.1", 1)
    print("  PS/无 BOM 那条 -> 4.119")
else:
    print("  ⚠ PS 那条没找到（编号可能已被改）")

# ⑤ 引用同步
s = s.replace("见 §4.113~§4.117", "见 §4.118~§4.122")
s = s.replace("见 **§4.113**（假玩家探针必须进 PlayerList 且救活）、**§4.114**（PS 5.1 读无 BOM 的 UTF-8 ps1）、\n**§4.115**（框架事件不是判据：末地龙不调 `super.hurt`）、**§4.116**（时间线常量不许撞车）、\n**§4.117**（「改注释」不许和「功能行」同一次替换）",
              "见 **§4.118**（假玩家探针必须进 PlayerList 且救活）、**§4.119**（PS 5.1 读无 BOM 的 UTF-8 ps1）、\n**§4.120**（框架事件不是判据：末地龙不调 `super.hurt`）、**§4.121**（时间线常量不许撞车）、\n**§4.122**（「改注释」不许和「功能行」同一次替换）")

if WRITE:
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("已落笔")
else:
    print("（只看；要落笔加 --write）")

# 复核
import re
body = io.open(DOC, encoding="utf-8").read() if WRITE else s
nums = sorted(set(int(m) for m in re.findall(r"### 4\.(\d+)", body)))
print("§4 编号尾部：", nums[-10:])
gaps = [n for n in range(1, max(nums) + 1) if n not in nums and n >= max(nums) - 12]
print("尾部缺号：", gaps if gaps else "无")
for k in ("§4.113~§4.117", "§4.118~§4.122"):
    print("  引用 %s 出现 %d 次" % (k, body.count(k)))
