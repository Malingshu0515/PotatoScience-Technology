# -*- coding: utf-8 -*-
u"""_zf160_mkgatesnap.py —— 由 ZF158 那份快照脚本生成 ZF160 的（只做文本改写，不跑门）。

名单口径沿用 ZF158 那份，本轮再补上自己的 `_zf160_verify.py`。
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

SRC = r"E:\PotatoST\build\zftools\_zf158_gatesnap.py"
DST = r"E:\PotatoST\build\zftools\_zf160_gatesnap.py"

t = io.open(SRC, encoding="utf-8").read()
t = t.replace(u"ZF158", u"ZF160").replace(u"_zf158_gatesnap.txt", u"_zf160_gatesnap.txt")
old = u'"_zf158_verify.py",'
new = u'"_zf158_verify.py", "_zf160_verify.py",'
if t.count(old) != 1:
    print(u"!! 锚点命中 %d 次" % t.count(old))
    sys.exit(1)
t = t.replace(old, new, 1)
io.open(DST, "w", encoding="utf-8", newline="\n").write(t)
print(u"已写 %s（%d 字节）" % (DST, len(t.encode("utf-8"))))
