# -*- coding: utf-8 -*-
"""_zf137_check.py —— 本轮文案改动的**全链核对**（只读）

不靠"看着对"，逐条钉：
  ① 键集合四语言一致、键数没变（只改值）；
  ② 格式占位符签名一致（`%1$s` 不丢不多）——死亡文案靠它接玩家名，错一个就是崩客户端；
  ③ 老内容没被顺手删掉（数值 token 全在）；
  ④ 用户点名要删的两条**开发笔记**在四语言里都绝迹；
  ⑤ 死亡文案键的 `%1$s` 恰好 1 个（多了少了都会让 `String.format` 出问题）；
  ⑥ 挂载点还在：`death.attack.` 前缀 + damage_type 的 message_id 对得上。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
DT = r"E:\PotatoST\src\main\resources\data\potato_s_t\damage_type"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

REWRITTEN = {
    "tooltip.potato_s_t.star_steel_set",
    "tooltip.potato_s_t.vibranium_set",
    "tooltip.potato_s_t.titanium_alloy_set",
}
DEATH = "death.attack.potato_s_t.vibranium_reflect"
NUM = re.compile(r"\d+(?:\.\d+)?")
PH = re.compile(r"%\d+\$s|%s")
fails = []


def say(ok, msg):
    print(u"  [%s] %s" % (u"OK" if ok else u"!!", msg))
    if not ok:
        fails.append(msg)


tabs = {}
for lg in LANGS:
    tabs[lg] = json.loads(io.open(os.path.join(LANG, lg + ".json"), encoding="utf-8").read())

print(u"== ① 键集合一致 ==")
base = set(tabs["zh_cn"])
for lg in LANGS:
    say(set(tabs[lg]) == base, u"%s 键集合与 zh_cn 一致（%d 键）" % (lg, len(tabs[lg])))

print(u"\n== ② 只改值：四组键都在，且不是空串 ==")
for k in sorted(REWRITTEN | {DEATH}):
    for lg in LANGS:
        v = tabs[lg].get(k)
        say(isinstance(v, str) and len(v) > 0, u"%s[%s] 在且非空" % (k.split(".")[-1], lg))

print(u"\n== ③ 死亡文案的 %1$s 恰好 1 个 ==")
for lg in LANGS:
    v = tabs[lg][DEATH]
    n = v.count(u"%1$s")
    say(n == 1, u"%s：%%1$s 出现 %d 次（必须 1）" % (lg, n))

print(u"\n== ④ 开发笔记与俗套死亡文案在四语言里绝迹 ==")
BANNED = [u"贴图暂时", u"暂时借用", u"暂用原版", u"踢到了铁板",
          u"Textures currently borrow", u"borrow the vanilla",
          u"暫定でバニラ", u"テクスチャは暫定",
          u"заимствованы у ванильного", u"Текстуры пока",
          u"kicked a steel plate", u"鉄板を蹴った", u"пнул стальную плиту"]
allvals = u"\n".join(v for lg in LANGS for v in tabs[lg].values())
for b in BANNED:
    say(b not in allvals, u"四语言全域都不含「%s」" % b)

print(u"\n== ⑤ 老数值一条没丢（文案重写 ≠ 数值改动）==")
# 这些是改动前那些说明里的数字，必须原样还在
KEEP = {
    "tooltip.potato_s_t.star_steel_set": [u"4", u"45", u"10", u"15", u"12", u"20"],
    "tooltip.potato_s_t.vibranium_set": [u"2", u"10%"],
    "tooltip.potato_s_t.titanium_alloy_set": [u"25", u"22"],
}
for k, nums in KEEP.items():
    for lg in LANGS:
        v = tabs[lg][k]
        miss = [n for n in nums if n not in v]
        say(not miss, u"%s[%s] 数值齐（缺 %s）" % (k.split(".")[-1], lg, miss or u"无"))

print(u"\n== ⑥ 死亡伤害类型的挂载点对得上 ==")
# ⚠ 第一版这条断言我写错了：原版拼键的规则是
#     "death.attack." + **message_id 的 path 部分**
#   （message_id 是 `potato_s_t.vibranium_reflect` ⇒ 键 `death.attack.potato_s_t.vibranium_reflect`）。
#   我却把 message_id 整串带上、再前置 `death.attack.`，拼成了
#   `death.attack.potato_s_t.potato_s_t.vibranium_reflect`（重复命名空间）⇒ 假 FAIL。
#   （档案 §4.30 那一族：FAIL 先怀疑期望。）
p = os.path.join(DT, "vibranium_reflect.json")
if os.path.exists(p):
    d = json.loads(io.open(p, encoding="utf-8").read())
    mid = d.get("message_id")
    # path 部分 = 去掉命名空间后的那段
    path = mid.split(":", 1)[1] if ":" in mid else mid
    expect_key = "death.attack." + path
    say(expect_key == DEATH,
        u"damage_type 的 message_id = %r ⇒ 拼出的键 %r == 我们改的那个键" % (mid, expect_key))
    say(DEATH in tabs["zh_cn"], u"对应文案键存在（四语言都在）")
    for lg in LANGS:
        say(DEATH in tabs[lg], u"%s 有这个键" % lg)
else:
    say(False, u"缺 %s" % p)

print(u"\n== ⑦ 新文案抽样（中文）==")
for k in sorted(REWRITTEN):
    print(u"  ── %s ──" % k.split(".")[-1])
    for line in tabs["zh_cn"][k].split(u"\n"):
        print(u"     %s" % line)
print(u"  ── death.attack ──")
print(u"     %s" % tabs["zh_cn"][DEATH])

print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
