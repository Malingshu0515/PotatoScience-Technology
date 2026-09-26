# -*- coding: utf-8 -*-
u"""_zf128_mkgatesnap.py —— 生成 `_zf128_gatesnap.py`（照 ZF127 那份改名 + 加上本轮的常驻门）

口径与历轮完全一样（只读、每份最多 300 秒、超时按红记）。

跑法：
    python build\\zftools\\_zf128_mkgatesnap.py
"""
import io
import os

ZT = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(ZT, "_zf127_gatesnap.py"), encoding="utf-8", newline=u"").read()
out = (src
       .replace(u"ZF127 轮", u"ZF128 轮")
       .replace(u"（ZF127）", u"（ZF128）")
       .replace(u"_zf127_gatesnap_before.txt", u"_zf128_gatesnap.txt")
       .replace(u'"_zf127_verify.py",', u'"_zf127_verify.py",\n         "_zf128_verify.py",')
       .replace(u"_zf127_gatesnap.py", u"_zf128_gatesnap.py"))
io.open(os.path.join(ZT, "_zf128_gatesnap.py"), "w", encoding="utf-8", newline=u"\n").write(out)
print(u"写好 _zf128_gatesnap.py（含 _zf128_verify.py：%s）" % (u"_zf128_verify.py" in out))
