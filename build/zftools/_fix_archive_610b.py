# -*- coding: utf-8 -*-
"""第二次修 §6.10：上一轮把 ⑩ 的**正文**落在 ⑪ 后面了，这一轮把正文搬到 ⑩ 标题下面。

目标顺序：⑩ 标题 → ⑩ 正文 → ⑪ 标题 → ⑪ 正文
（上一轮的结果是：⑩ 标题 → ⑪ 标题 → ⑪ 正文 → ⑩ 正文）
"""
import io

PATH = r"E:\PotatoST\docs\开发档案.md"
text = io.open(PATH, encoding="utf-8").read()
lines = text.splitlines(keepends=True)


def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    return None


t10 = find(lambda l: l.startswith("**⑩ tooltip 是给玩家看的"))
t11 = find(lambda l: l.startswith("**⑪ 复用 GUI 部件时"))
assert t10 is not None and t11 is not None and t10 < t11, "标题顺序不对"

# ⑩ 正文 = 从"用户原话：**「哎呀shift介绍"那一行开始，到"…一个字都帮不上忙…"那段结束
b10 = find(lambda l: l.startswith("用户原话：**「哎呀shift介绍"))
assert b10 is not None and b10 > t11, "⑩ 正文不在 ⑪ 之后？"
# 正文结束：⑩ 正文的最后一行是"> 只能靠这条规矩和…（`_verify_tooltip_in_jar.py`）。"
e10 = find(lambda l: l.startswith("> 只能靠这条规矩"), b10)
assert e10 is not None, "找不到 ⑩ 正文结尾"
# 结尾后面应当是一个空行或 ---
while e10 + 1 < len(lines) and lines[e10 + 1].strip() == "":
    e10 += 1

body = lines[b10:e10 + 1]

# 从原位置删掉正文
rest = lines[:b10] + lines[e10 + 1:]

# 重新定位（删除后行号会变），插到 ⑩ 标题的下一行（跳过标题后那个空行）
t10b = None
for i, l in enumerate(rest):
    if l.startswith("**⑩ tooltip 是给玩家看的"):
        t10b = i
        break
assert t10b is not None
insert_at = t10b + 1
# 标题后已有一个空行，正文插在空行之后
if rest[insert_at].strip() == "":
    insert_at += 1
out = rest[:insert_at] + body + rest[insert_at:]
text2 = "".join(out)

p10 = text2.find("**⑩ tooltip 是给玩家看的")
p10body = text2.find("用户原话：**「哎呀shift介绍")
p11 = text2.find("**⑪ 复用 GUI 部件时")
assert -1 not in (p10, p10body, p11), "有段落丢了"
assert p10 < p10body < p11, "顺序仍不对：%d %d %d" % (p10, p10body, p11)
assert text2.count("**⑩ tooltip 是给玩家看的") == 1
assert text2.count("**⑪ 复用 GUI 部件时") == 1
assert text2.count("用户原话：**「哎呀shift介绍") == 1

io.open(PATH, "w", encoding="utf-8", newline="").write(text2)
print("OK  顺序已正：⑩标题(L%d) → ⑩正文(L%d) → ⑪标题(L%d)"
      % (text2[:p10].count("\n") + 1,
         text2[:p10body].count("\n") + 1,
         text2[:p11].count("\n") + 1))
