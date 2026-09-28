# -*- coding: utf-8 -*-
u"""_zf155_mkgatesnap.py —— 由 ZF148 那份快照脚本生成 ZF155 的（只做文本改写，不跑门）。

名单口径：沿用 ZF148 那份**精选名单**，补上它之后新写的门
（`_zf150` / `_zf153` / `_zf155` 本轮自己的，以及 `_zf137` / `_zf140` / `_zf117_audit`）。
⚠ ZF148 名单里 `_zf135/_zf143/_zf144` 三个盘上已经不在（别人删/改名了）⇒ 保留在名单里、
由脚本自己报"不存在"（不替别人删账）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"E:\PotatoST\build\zftools\_zf148_gatesnap.py"
DST = r"E:\PotatoST\build\zftools\_zf155_gatesnap.py"

OLD = (u'         "_zf149_verify.py", "_zf151_verify.py",\n'
       u'         "_zf109_tabaudit.py"]')
NEW = (u'         "_zf149_verify.py", "_zf151_verify.py",\n'
       u'         "_zf150_verify.py", "_zf153_verify.py", "_zf155_verify.py",\n'
       u'         "_zf137_verify.py", "_zf140_verify.py", "_zf117_audit.py",\n'
       u'         "_zf109_tabaudit.py"]')

t = io.open(SRC, encoding="utf-8").read()
t = t.replace(u"ZF148", u"ZF155").replace(u"_zf148_gatesnap.txt", u"_zf155_gatesnap.txt")
if t.count(OLD) != 1:
    print(u"!! 锚点命中 %d 次" % t.count(OLD))
    sys.exit(1)
t = t.replace(OLD, NEW, 1)
io.open(DST, "w", encoding="utf-8", newline="\n").write(t)
print(u"已写 %s（%d 字节）" % (DST, len(t.encode("utf-8"))))
