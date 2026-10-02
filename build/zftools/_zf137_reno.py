# -*- coding: utf-8 -*-
"""_zf137_reno.py —— 修一处**编号冲突**：我的 4.125 让给别人的 4.125

## 事故

档案里出现了**两个 `### 4.125`**：
  · 我那条（ZF135）：`【校验雷】"比值"必须配一条"绝对量"…` —— `_zf135_docs.py` 写于 22:01:55
  · 别人那条（ZF134）：`【行区间切片】切一段代码要吃三样…` —— 从 `_zf134_apply2.py` 等脚本写入

我的脚本按"取档案里最大号 +1"选号，读到 4.124 就拿了 4.125 ——
而**4.125 是别人为"行区间切片"预留的**（他们的脚本 21:5x 就在写那段内容）。
⇒ **同号**。按惯例**后来者让**，而且我这轮已经改过一次号（117→130），再动我的成本最低。

## 做法

把我那条从 4.125 改号为 **4.134**，并**移到 4.133 之后**。
别人的 4.125 一个字不动。改完回读：确认我那条只剩一个 4.134、别人的 4.125 还在、正文一字未变。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ARCH = r"E:\PotatoST\docs\开发档案.md"
list_md = r"E:\PotatoST\docs\贴图清单.md"

raw = io.open(ARCH, encoding="utf-8").read()
lines = raw.split(u"\n")

# ① 定位我那条（用标题里的特征词，不用行号）
def is_mine(ln):
    return ln.startswith(u"### 4.125 ") and (u"绝对量" in ln or u"比值" in ln)

def is_theirs(ln):
    return ln.startswith(u"### 4.125 ") and u"行区间切片" in ln

mine_i = [i for i, ln in enumerate(lines) if is_mine(ln)]
their_i = [i for i, ln in enumerate(lines) if is_theirs(ln)]
print(u"我的 4.125 在行 %s；别人的在行 %s" % ([i + 1 for i in mine_i], [i + 1 for i in their_i]))

if not mine_i:
    print(u"  [幂等] 找不到我那条 4.125（可能已经改过号）")
    sys.exit(0)
if not their_i:
    print(u"  !! 找不到别人那条 4.125，停手（别乱动）")
    sys.exit(1)
if len(mine_i) != 1 or len(their_i) != 1:
    print(u"  !! 各应只有 1 条，实际 %d / %d，停手" % (len(mine_i), len(their_i)))
    sys.exit(1)

m = mine_i[0]
# ② 切出我这条的整段（到下一个 '### ' 或 '---' 之前）
end = m + 1
while end < len(lines) and not lines[end].startswith(u"### ") and not lines[end].startswith(u"---"):
    end += 1
block = lines[m:end]
print(u"我那条共 %d 行（%d..%d）" % (len(block), m + 1, end))

# ③ 改号
block[0] = block[0].replace(u"### 4.125 ", u"### 4.134 ", 1)
if u"4.125" in u"\n".join(block):
    print(u"  [注意] 我这条正文里还提到 4.125，一并改掉")
    block = [ln.replace(u"4.125", u"4.134") for ln in block]

# ④ 从原处删掉
rest = lines[:m] + lines[end:]
# ⑤ 插到 4.133 之后
tgt = None
for i, ln in enumerate(rest):
    if ln.startswith(u"### 4.133 "):
        tgt = i
if tgt is None:
    print(u"  !! 找不到 4.133 之后的位置，停手")
    sys.exit(1)
en2 = tgt + 1
while en2 < len(rest) and not rest[en2].startswith(u"### ") and not rest[en2].startswith(u"---"):
    en2 += 1
out = rest[:en2] + block + rest[en2:]
io.open(ARCH, "w", encoding="utf-8", newline="\n").write(u"\n".join(out))

# ⑥ 回读
back = io.open(ARCH, encoding="utf-8").read()
bl = back.split(u"\n")
n125 = sum(1 for ln in bl if ln.startswith(u"### 4.125 "))
n134 = sum(1 for ln in bl if ln.startswith(u"### 4.134 "))
ok = (n125 == 1 and n134 == 1
      and any(is_theirs(ln) for ln in bl)
      and any(u"### 4.134 " in ln and (u"绝对量" in ln) for ln in bl)
      and u"### 4.133 " in back)
print(u"\n回读：4.125 出现 %d 次（应为 1，是别人的行区间切片）；4.134 出现 %d 次（应为 1，是我的）" % (n125, n134))
print(u"  %s" % (u"[OK] 编号冲突已解，别人的内容没动" if ok else u"[!!] 需要人工检查"))

# ⑦ 清单里我写的 4.125 引用也要跟
lm = io.open(list_md, encoding="utf-8").read()
if u"§4.125" in lm:
    io.open(list_md, "w", encoding="utf-8", newline="\n").write(lm.replace(u"§4.125", u"§4.134"))
    print(u"  [OK] 贴图清单里的 §4.125 -> §4.134")
sys.exit(0 if ok else 1)
