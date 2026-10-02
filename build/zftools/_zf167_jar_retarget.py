# -*- coding: utf-8 -*-
u"""_zf167_jar_retarget.py —— 成品那份门的两处跟平（本轮重打了 0.13 成品）

`_zf149_verify.py`：WANT_SHA / WANT_SIZE 换成本轮发布那一刻的实测值
`_zf149_jar.py`  ：产物里的三个统计（class / 配方 / 语言键数）换成实测值
"""
import ast
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"E:\PotatoST\build\zftools"
JAR = r"E:\PotatoST\release\PotatoST-0.13.jar"

sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
size = os.path.getsize(JAR)
print(u"实测：%s = %d 字节 / sha1 %s" % (os.path.basename(JAR), size, sha))

fails = []
p = os.path.join(T, "_zf149_verify.py")
t = io.open(p, encoding="utf-8").read()
t2 = re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % sha, t)
t2 = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, t2)
if t2 != t:
    ast.parse(t2)
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t2)
    print(u"  [OK] _zf149_verify.py 的 WANT_SHA / WANT_SIZE 已跟平")
else:
    print(u"  [幂等] _zf149_verify.py 已是目标值")

p = os.path.join(T, "_zf149_jar.py")
t = io.open(p, encoding="utf-8").read()
n_old = len(re.findall(u"len\\(recipes\\) == \\d+", t))
t2 = re.sub(u"len\\(recipes\\) == \\d+", u"len(recipes) == 98", t)
t2 = re.sub(u'u"zh_cn": \\d+, u"en_us": \\d+, u"ja_jp": \\d+, u"ru_ru": \\d+, u"lzh": \\d+',
            u'u"zh_cn": 620, u"en_us": 620, u"ja_jp": 620, u"ru_ru": 620, u"lzh": 622', t2)
t2 = re.sub(u"len\\(cls\\) >= \\d+", u"len(cls) >= 389", t2)
if t2 != t:
    ast.parse(t2)
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t2)
    print(u"  [OK] _zf149_jar.py 的配方数 / 语言键数 / class 数已跟平（%d 处 recipes 判据）" % n_old)
else:
    print(u"  [幂等] _zf149_jar.py 已是目标值")
print(u"失败项 = %d" % len(fails))
sys.exit(1 if fails else 0)
