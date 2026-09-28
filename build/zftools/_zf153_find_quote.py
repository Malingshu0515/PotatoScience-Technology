# -*- coding: utf-8 -*-
u"""找"双引号个数是奇数"的行 —— 那就是内嵌引号把字符串提前截断的地方。"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf153_verify.py"
lines = io.open(P, encoding="utf-8").read().split(u"\n")

print(u"== 双引号个数为奇数的行 ==")
for i, l in enumerate(lines, 1):
    code = l.split(u"#")[0]
    if u'"""' in code:          # 三引号行单独看
        if code.count(u'"') % 3 != 0:
            print(u"  %4d | %s" % (i, l))
        continue
    if code.count(u'"') % 2 == 1:
        print(u"  %4d | %s" % (i, l))

print(u"\n== 括号余额（只看 ASCII 括号，粗略）==")
bal = 0
for i, l in enumerate(lines, 1):
    code = l.split(u"#")[0]
    # 去掉字符串字面量里的括号太麻烦，这里只看余额是否出现负数
    bal += code.count(u"(") - code.count(u")")
    if bal < 0:
        print(u"  第 %d 行余额变成 %d：%s" % (i, bal, l))
        break
print(u"  末尾余额 = %d（函数定义各自成对时应当回到 0 附近）" % bal)
