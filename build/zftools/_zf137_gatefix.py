# -*- coding: utf-8 -*-
"""_zf137_gatefix.py —— 把受这次套装文案重写影响的门**跟平**（判据不删，只换靶子）

用户让我把套装说明"写得像文案、别写成开发笔记"，删掉的两条是：
  ① `（贴图暂时借用原版铁套）`
  ② `被这一下打死的人，死因写的是「踢到了铁板」`
并把死亡文案 `%1$s踢到了铁板` 换成 `%1$s被自己的攻击原样奉还`。

`_zf139_verify.py`（另一条线的）有一条判据要求"振金说明里必须出现
『踢到了铁板 / steel plate / 鉄板 / плиту』"—— 那正是 ② —— 所以它红了。
本脚本把那 4 个 needle 换成"**反伤**"这个玩法要素（判据强度不变），
并在文件里留下说明，免得下一轮有人又改回去。
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOOLS = r"E:\PotatoST\build\zftools"
P = os.path.join(TOOLS, "_zf139_verify.py")
fails = []

t = io.open(P, encoding="utf-8").read()

print(u"== ① needle 换靶子（幂等）==")
PAIRS = [
    (u'(u"zh_cn", [u"抗性提升 I", u"摔落", u"10%", u"踢到了铁板"]),',
     u'(u"zh_cn", [u"抗性提升 I", u"摔落", u"10%", u"奉还"]),',
     u"zh_cn 踢到了铁板 -> 奉还"),
    (u'(u"en_us", [u"Resistance I", u"fall damage", u"10%", u"steel plate"]),',
     u'(u"en_us", [u"Resistance I", u"fall damage", u"10%", u"given back"]),',
     u"en_us steel plate -> given back"),
    (u'(u"ja_jp", [u"耐性 I", u"落下", u"10%", u"鉄板"]),',
     u'(u"ja_jp", [u"耐性 I", u"落下", u"10%", u"返される"]),',
     u"ja_jp 鉄板 -> 返される"),
    (u'(u"ru_ru", [u"Сопротивление I", u"падени", u"10%", u"плиту"])):',
     u'(u"ru_ru", [u"Сопротивление I", u"падени", u"10%", u"возвращает"])):',
     u"ru_ru плиту -> возвращает"),
]
for old, new, label in PAIRS:
    if new in t:
        print(u"  [幂等] %s" % label)
    elif t.count(old) == 1:
        t = t.replace(old, new)
        print(u"  [OK] %s" % label)
    else:
        fails.append(u"%s 锚点 %d 次" % (label, t.count(old)))
        print(u"  !! %s 锚点 %d 次，停手" % (label, t.count(old)))
io.open(P, "w", encoding="utf-8", newline="\n").write(t)

print(u"\n== ② 在用户原话引用之后补一行「现状」==")
t = io.open(P, encoding="utf-8").read()
NOTE = (u"    （⚠ 0.11 ZF137：上面这段是**当时的原话**，保留不改。其中「死亡提示为踢到了铁板」\n"
        u"      后来按用户要求改过 —— 死亡文案现在是「被自己的攻击原样奉还」，\n"
        u"      而且这句话**不再写进套装说明**：说明只讲玩法，不讲实现。）\n")
anchor = u"      如果攻击者被反伤而死 死亡提示为「攻击者」踢到了铁板」\n"
if u"0.11 ZF137：上面这段是**当时的原话**" in t:
    print(u"  [幂等] 注释已在")
elif t.count(anchor) == 1:
    io.open(P, "w", encoding="utf-8", newline="\n").write(t.replace(anchor, anchor + NOTE, 1))
    print(u"  [OK] 已在原话之后补「现状」一行（原话本身一字未动）")
else:
    fails.append(u"原话锚点 %d 次" % t.count(anchor))
    print(u"  !! 原话锚点 %d 次，停手" % t.count(anchor))

print(u"\n== ③ 语法自检 ==")
try:
    ast.parse(io.open(P, encoding="utf-8").read())
    print(u"  [OK] AST 解析通过")
except SyntaxError as e:
    fails.append(u"语法错误：%s" % e)
    print(u"  !! 语法错误 %s" % e)

print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
